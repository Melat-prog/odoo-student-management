from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
import logging
import base64
import io
import requests
from bs4 import BeautifulSoup
import pypdf

_logger = logging.getLogger(__name__)

# Preferred models in order — these are short text-generation models that work
# well for academic tasks and are available on free-tier API keys.
# Uses the full model ID as returned by the API (e.g. "models/gemini-3.6-flash").
_PREFERRED_MODELS = [
    'models/gemini-3.6-flash',
    'models/gemini-3.5-flash',
    'models/gemini-3.7-flash',
    'models/gemini-flash-latest',
    'models/gemini-3.1-flash-lite',
    'models/gemini-3.5-flash-lite',
]


class StudentAIAssistant(models.TransientModel):
    _name = 'student.ai.assistant'
    _inherit = ['ai.extraction.mixin']
    _description = 'AI Learning Assistant Architecture'

    name = fields.Char(string="Task Title", required=True)
    student_id = fields.Many2one('student.student', string="Student", default=lambda self: self._default_student())
    resource_id = fields.Many2one('student.learning.resource', string="Source Material")
    file_attachment = fields.Binary(string="Document Attachment")
    file_name = fields.Char(string="File Name")
    custom_text = fields.Text(string="Or Paste Custom Text")

    res_model = fields.Char(string="Target Model", default=False)
    res_id = fields.Integer(string="Target Record ID", default=0)

    @api.model
    def _get_action_type_selection(self):
        user = self.env.user
        is_teacher = (
            user.has_group('student_management.group_teacher') or
            user.has_group('student_management.group_student_manager') or
            user.has_group('base.group_system') or
            user.has_group('base.group_erp_manager') or
            (not user.has_group('student_management.group_student') and not user.has_group('base.group_portal'))
        )
        if is_teacher:
            return [
                ('summary', 'Generate Summary'),
                ('notes', 'Generate Study Notes'),
                ('flashcards', 'Generate Flashcards'),
                ('mcq', 'Generate Multiple Choice Questions'),
                ('short_q', 'Generate Short-Answer Questions')
            ]
        else:
            return [
                ('summary', 'Generate Summary'),
                ('notes', 'Generate Study Notes'),
                ('flashcards', 'Generate Flashcards')
            ]

    action_type = fields.Selection(selection='_get_action_type_selection', string="AI Action", required=True, default='summary')

    difficulty = fields.Selection([
        ('easy', 'Easy / Beginner'),
        ('medium', 'Medium / Intermediate'),
        ('hard', 'Hard / Advanced')
    ], string="Difficulty", default='medium')

    generated_content = fields.Html(string="AI Output", readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('processing', 'Processing'), ('done', 'Done')], default='draft')

    def _default_student(self):
        return False

    @classmethod
    def _sanitize_val_recursive(cls, val):
        if isinstance(val, str):
            return val.replace('\x00', '').replace('\0', '').strip()
        elif isinstance(val, dict):
            return {k: cls._sanitize_val_recursive(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [cls._sanitize_val_recursive(v) for v in val]
        elif isinstance(val, tuple):
            return tuple(cls._sanitize_val_recursive(v) for v in val)
        return val

    @api.model_create_multi
    def create(self, vals_list):
        # DEBUG: Log which fields contain NUL bytes BEFORE sanitization
        for idx, vals in enumerate(vals_list):
            for key, value in vals.items():
                if isinstance(value, str) and '\x00' in value:
                    _logger.warning(
                        "NUL BYTE FOUND in student.ai.assistant create() "
                        "field '%s' (vals_list[%d]): %r",
                        key, idx, value[:200]
                    )
        sanitized_list = [self._sanitize_val_recursive(vals) for vals in vals_list]
        clean_vals_list = []
        for vals in sanitized_list:
            vals_copy = dict(vals)
            if vals_copy.get('custom_text'):
                vals_copy.pop('document_attachment', None)
                vals_copy.pop('file_attachment', None)
            clean_vals_list.append(vals_copy)
        return super().create(clean_vals_list)

    def write(self, vals):
        # DEBUG: Log which fields contain NUL bytes BEFORE sanitization
        for key, value in vals.items():
            if isinstance(value, str) and '\x00' in value:
                _logger.warning(
                    "NUL BYTE FOUND in student.ai.assistant write() "
                    "field '%s': %r",
                    key, value[:200]
                )
        sanitized_vals = self._sanitize_val_recursive(vals)
        vals_copy = dict(sanitized_vals)
        if vals_copy.get('custom_text') or self.custom_text:
            vals_copy.pop('document_attachment', None)
            vals_copy.pop('file_attachment', None)
        return super().write(vals_copy)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context
        resource_id = ctx.get('default_resource_id')
        if not resource_id and ctx.get('active_model') == 'student.learning.resource' and ctx.get('active_id'):
            resource_id = ctx.get('active_id')

        if resource_id and 'resource_id' in fields_list and not res.get('resource_id'):
            res['resource_id'] = resource_id

        if 'res_model' in fields_list and not res.get('res_model'):
            res['res_model'] = ctx.get('default_res_model') or ctx.get('active_model')
        if 'res_id' in fields_list and not res.get('res_id'):
            res['res_id'] = ctx.get('default_res_id') or ctx.get('active_id')

        r_id = res.get('resource_id')
        if r_id and 'custom_text' in fields_list and not res.get('custom_text'):
            resource_rec = self.env['student.learning.resource'].browse(r_id)
            if resource_rec.exists():
                extracted = self._get_extracted_text(resource_id=resource_rec)
                if extracted:
                    res['custom_text'] = self._sanitize_text(extracted)
                    if 'name' in fields_list and not res.get('name'):
                        res['name'] = f"Analyze: {resource_rec.name}"

        return self._sanitize_val_recursive(res)

    def action_save_to_record(self):
        self.ensure_one()
        res_model = self.res_model or self.env.context.get('default_res_model') or self.env.context.get('active_model')
        res_id = self.res_id or self.env.context.get('default_res_id') or self.env.context.get('active_id')

        output = self.generated_content
        if not output:
            raise UserError(_("No generated output to save."))

        if res_model and res_id:
            target_record = self.env[res_model].browse(res_id)
            if target_record.exists():
                if hasattr(target_record, 'ai_output'):
                    target_record.ai_output = output
                elif hasattr(target_record, 'description'):
                    target_record.description = output
                elif hasattr(target_record, 'content'):
                    target_record.content = output
                _logger.info("Saved AI output to %s ID %s", res_model, res_id)
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('resource_id')
    def _onchange_resource_id(self):
        if self.resource_id:
            extracted = self._get_extracted_text(resource_id=self.resource_id)
            if extracted:
                self.custom_text = self._sanitize_text(extracted)
                if not self.name or self.name == 'New Task':
                    self.name = f"Analyze: {self.resource_id.name}"

    @api.onchange('file_attachment', 'file_name')
    def _onchange_file_attachment(self):
        if self.file_attachment:
            extracted = self._get_extracted_text(
                file_attachment=self.file_attachment,
                file_name=self.file_name
            )
            if extracted:
                self.custom_text = self._sanitize_text(extracted)

    def _get_genai_client(self):
        """Return a configured google.genai Client instance."""
        try:
            from google import genai
        except ImportError:
            raise UserError(_(
                "The 'google-genai' Python package is not installed. "
                "Please run: pip install google-genai"
            ))

        api_key = self.env['ir.config_parameter'].sudo().get_param('student_management.gemini_api_key')
        if not api_key:
            raise UserError(_(
                "Gemini API key not configured. "
                "Go to Settings → Technical → Parameters → System Parameters "
                "and set 'student_management.gemini_api_key'."
            ))

        client = genai.Client(api_key=api_key)
        return client

    def _pick_model(self, client):
        """
        Pick the first working model from _PREFERRED_MODELS.
        Uses the live model list (with supported_actions) for validation.
        Falls back through the list until one is found.
        """
        try:
            available_names = {
                m.name for m in client.models.list()
                if 'generateContent' in getattr(m, 'supported_actions', [])
            }
        except Exception as e:
            _logger.warning("Failed to list Gemini models: %s", e)
            available_names = set()

        for model_id in _PREFERRED_MODELS:
            if available_names and model_id not in available_names:
                continue
            return model_id

        for name in sorted(available_names):
            if 'flash' in name and 'tts' not in name and 'image' not in name:
                return name

        raise UserError(_(
            "No suitable Gemini text model found for this API key. "
            "Ensure the key has access to a generateContent-capable model."
        ))

    def _format_ai_output(self, raw_response_text):
        if not raw_response_text:
            return "<p>No response received from AI service.</p>"
        
        text = self._sanitize_text(str(raw_response_text))
        
        # Remove starting code fence (```html, ```xml, ```json, or ```)
        if text.startswith("```"):
            # Find the first newline after the opening backticks
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1:]
            else:
                text = text.lstrip("`")
                
        # Remove closing code fence (```)
        if text.endswith("```"):
            text = text[:-3]
            
        return self._sanitize_text(text)

    def action_generate(self):
        self.ensure_one()

        # Enforce role-based security check
        is_teacher = (
            self.env.user.has_group('student_management.group_teacher') or
            self.env.user.has_group('student_management.group_student_manager') or
            self.env.user.has_group('base.group_system') or
            self.env.user.has_group('base.group_erp_manager') or
            (not self.env.user.has_group('student_management.group_student') and not self.env.user.has_group('base.group_portal'))
        )
        if not is_teacher and self.action_type in ('mcq', 'short_q'):
            raise AccessError(_("Quiz and question generation is restricted to teachers."))

        self.state = 'processing'

        # --- Get client & pick model ---
        client = self._get_genai_client()
        model_id = self._pick_model(client)
        _logger.info("AI Assistant: using model %s", model_id)

        resource_content = self._get_extracted_text(
            resource_id=self.resource_id,
            custom_text=self.custom_text,
            file_attachment=self.file_attachment,
            file_name=self.file_name
        )
        content_str = self._sanitize_text(str(resource_content or ''))

        # Fallback & Auto-Fill: if custom_text was empty, assign the extracted content
        if not self.custom_text and content_str:
            self.custom_text = self._sanitize_text(content_str)

        # Validate minimum content
        if not content_str:
            raise UserError(_("Please provide source text or upload a document attachment."))

        if len(content_str) < 10:
            raise UserError(_(
                "Please provide more detailed source material "
                "(at least 2–3 sentences) for the AI to process."
            ))
        if len(content_str.split()) < 5:
            self.write({
                'generated_content': "<div class='ai-response'><p>Insufficient content provided. "
                                     "Please supply at least a few sentences.</p></div>",
                'state': 'done'
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'student.ai.assistant',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

        # --- Build prompt ---
        action_label = dict(self._fields['action_type']._description_selection(self.env)).get(self.action_type, self.action_type)
        
        # Specific formatting instructions based on action type
        format_instructions = ""
        if self.action_type == 'mcq':
            format_instructions = (
                "Format every question using sequential numbering (1., 2., 3.).\n"
                "List each choice on its own individual line directly below the question (A), B), C), D)).\n"
                "Put the correct answer on a new line directly after the choices, starting with 'Answer: '.\n"
                "Leave a single blank line before the next question.\n"
            )
        elif self.action_type == 'short_q':
            format_instructions = (
                "List each question on a new line with sequential numbering (1., 2., 3.).\n"
                "Place the answer on a new line directly below the question starting with 'Answer: '.\n"
                "Leave a single blank line before the next question.\n"
            )
        elif self.action_type == 'flashcards':
            format_instructions = (
                "Present flashcards exclusively in a clean 2-column Markdown table.\n"
                "Column headers must be: | Front (Concept / Question) | Back (Definition / Answer) |\n"
                "Keep table rows compact, clear, and single-spaced.\n"
            )
        else: # summary or notes
            format_instructions = (
                "Group sections under bold text titles on a new line (e.g., **Section Title**).\n"
                "Use tight bullet points with bold inline terms.\n"
                "Enclose all code snippets inside language-tagged Markdown code blocks.\n"
            )

        system_instruction = (
            "You are an academic assistant. Use only the provided source text. "
            "Wrap ONLY your final answer between the exact markers "
            "<<<ANSWER>>> and <<<END>>>. Put nothing else inside those markers "
            "except the requested content itself — no explanation, no draft "
            "attempts, no reasoning, no meta-commentary. If the source text is "
            "too short or unclear to work with, put exactly this inside the "
            "markers: 'Insufficient content provided.'\n\n"
            "Inside the markers, produce all output strictly according to the following layout and structural rules:\n"
            f"{format_instructions}"
        )
        prompt = (
            f"{system_instruction}\n\n"
            f"Action: {action_label}\n"
            f"Difficulty: {self.difficulty}\n"
            f"Task: {self.name}\n"
            f"Content: {content_str}\n"
        )

        # --- Call Gemini API ---
        from google.genai import types as genai_types
        response = None
        last_error = None
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except Exception as e:
            last_error = e
            _logger.error("Gemini generation failed on model %s: %s", model_id, e)

        if not response or not getattr(response, 'text', None):
            raise UserError(_(
                "AI content generation failed (model: %s).\n"
                "Error: %s\n\n"
                "If you see a quota/rate-limit error, wait a moment and try again. "
                "If you see a 404, the model may not be available for your API key."
            ) % (model_id, last_error or 'No response received'))

        import re
        raw_text = self._sanitize_text(response.text)
        _logger.info("RAW GEMINI RESPONSE (first 300 chars): %r", raw_text[:300])

        match = re.search(r'<<<ANSWER>>>(.*?)<<<END>>>', raw_text, re.DOTALL)
        if match:
            clean_text = self._format_ai_output(match.group(1).strip())
        else:
            _logger.warning("Response missing <<<ANSWER>>>/<<<END>>> markers, using full response.")
            fallback = re.sub(r'<thought>.*?</thought>', '', raw_text, flags=re.DOTALL)
            meta_pattern = r'\*\s*(Strict Grounding Instruction|Constraint|Self[-\u2011]Correction|Did I|Task)[:]?[^*]*'
            fallback = re.sub(meta_pattern, '', fallback, flags=re.IGNORECASE)
            clean_text = self._format_ai_output(fallback)

        generated_html = self._sanitize_text(
            f"<div class='ai-response'>{clean_text}</div>"
        )
        self.write({
            'generated_content': generated_html,
            'state': 'done'
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'student.ai.assistant',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
