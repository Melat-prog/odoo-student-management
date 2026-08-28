import logging
import re
import markdown
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from markupsafe import Markup

_logger = logging.getLogger(__name__)

# Preferred models in order of preference — short text-generation models
# that work well for academic tasks on free-tier API keys.
_PREFERRED_MODELS = [
    'models/gemini-3.6-flash',
    'models/gemini-3.5-flash',
    'models/gemini-3.7-flash',
    'models/gemini-flash-latest',
    'models/gemini-3.1-flash-lite',
    'models/gemini-3.5-flash-lite',
]


class AILearningAssistantWizard(models.TransientModel):
    _name = 'ai.learning.assistant.wizard'
    _inherit = ['ai.extraction.mixin']
    _description = 'AI Learning Assistant Wizard'

    task_title = fields.Char(string='Task Title', required=True)
    source_material_id = fields.Many2one('student.learning.resource', string='Source Material')
    file_attachment = fields.Binary(string='Document Attachment')
    file_name = fields.Char(string='File Name')
    custom_text = fields.Text(string='Or Paste Custom Text')

    res_model = fields.Char(string="Target Model", default=False)
    res_id = fields.Integer(string="Target Record ID", default=0)

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
                        "NUL BYTE FOUND in ai.learning.assistant.wizard create() "
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
                    "NUL BYTE FOUND in ai.learning.assistant.wizard write() "
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
    def _get_ai_action_selection(self):
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
                ('study_notes', 'Generate Study Notes'),
                ('flashcards', 'Generate Flashcards'),
                ('mcq', 'Generate Multiple Choice Questions'),
                ('short_answer', 'Generate Short-Answer Questions'),
            ]
        else:
            return [
                ('summary', 'Generate Summary'),
                ('study_notes', 'Generate Study Notes'),
                ('flashcards', 'Generate Flashcards'),
            ]

    ai_action = fields.Selection(selection='_get_ai_action_selection', string='AI Action', default='summary', required=True)
    generated_result = fields.Html(
        string="Generated Content",
        sanitize=False,
        readonly=True,
    )

    def _get_client(self):
        """Return a configured google.genai Client."""
        try:
            from google import genai
        except ImportError:
            raise UserError(_(
                "The 'google-genai' Python package is not installed. "
                "Run: pip install google-genai"
            ))
        api_key = self.env['ir.config_parameter'].sudo().get_param('student_management.gemini_api_key')
        if not api_key:
            raise UserError(_(
                "Gemini API key not configured. "
                "Set 'student_management.gemini_api_key' in "
                "Settings → Technical → Parameters → System Parameters."
            ))
        return genai.Client(api_key=api_key)

    def _pick_model(self, client):
        """Pick the best available model from the preferred list."""
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

        # Fallback: any flash text model
        for name in sorted(available_names or []):
            if 'flash' in name and 'tts' not in name and 'image' not in name:
                return name

        raise UserError(_("No suitable Gemini text model found for this API key."))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context
        resource_id = ctx.get('default_source_material_id') or ctx.get('default_resource_id')
        if not resource_id and ctx.get('active_model') == 'student.learning.resource' and ctx.get('active_id'):
            resource_id = ctx.get('active_id')

        if resource_id and 'source_material_id' in fields_list and not res.get('source_material_id'):
            res['source_material_id'] = resource_id

        if 'res_model' in fields_list and not res.get('res_model'):
            res['res_model'] = ctx.get('default_res_model') or ctx.get('active_model')
        if 'res_id' in fields_list and not res.get('res_id'):
            res['res_id'] = ctx.get('default_res_id') or ctx.get('active_id')

        r_id = res.get('source_material_id')
        if r_id and 'custom_text' in fields_list and not res.get('custom_text'):
            resource_rec = self.env['student.learning.resource'].browse(r_id)
            if resource_rec.exists():
                extracted = self._get_extracted_text(resource_id=resource_rec)
                if extracted:
                    res['custom_text'] = self._sanitize_text(extracted)
                    if 'task_title' in fields_list and not res.get('task_title'):
                        res['task_title'] = f"Analyze: {resource_rec.name}"

        return self._sanitize_val_recursive(res)

    def action_save_to_record(self):
        self.ensure_one()
        res_model = self.res_model or self.env.context.get('default_res_model') or self.env.context.get('active_model')
        res_id = self.res_id or self.env.context.get('default_res_id') or self.env.context.get('active_id')

        output = self.generated_result
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
                _logger.info("Saved AI wizard output to %s ID %s", res_model, res_id)
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('source_material_id')
    def _onchange_source_material_id(self):
        if self.source_material_id:
            extracted = self._get_extracted_text(resource_id=self.source_material_id)
            if extracted:
                self.custom_text = self._sanitize_text(extracted)
                if not self.task_title:
                    self.task_title = f"Analyze: {self.source_material_id.name}"

    @api.onchange('file_attachment', 'file_name')
    def _onchange_file_attachment(self):
        if self.file_attachment:
            extracted = self._get_extracted_text(
                file_attachment=self.file_attachment,
                file_name=self.file_name
            )
            if extracted:
                self.custom_text = self._sanitize_text(extracted)

    def _get_extracted_text_local(self):
        self.ensure_one()
        return self._get_extracted_text(
            resource_id=self.source_material_id,
            custom_text=self.custom_text,
            file_attachment=self.file_attachment,
            file_name=self.file_name
        )

    def action_generate_output(self):
        """Generate AI output based on selected action and extracted content."""
        self.ensure_one()

        # Enforce role-based security check
        is_teacher = (
            self.env.user.has_group('student_management.group_teacher') or
            self.env.user.has_group('student_management.group_student_manager') or
            self.env.user.has_group('base.group_system') or
            self.env.user.has_group('base.group_erp_manager') or
            (not self.env.user.has_group('student_management.group_student') and not self.env.user.has_group('base.group_portal'))
        )
        if not is_teacher and self.ai_action in ('mcq', 'short_answer'):
            raise AccessError(_("Quiz and question generation is restricted to teachers."))

        client = self._get_client()
        model_id = self._pick_model(client)
        _logger.info("AI Learning Wizard: using model %s", model_id)

        content = self._get_extracted_text_local()
        content_str = self._sanitize_text(str(content or ''))

        if not self.custom_text and content_str:
            self.custom_text = self._sanitize_text(content_str)

        # Validate source material
        if not content_str:
            raise UserError(_("Please provide source text or upload a document attachment."))

        if len(content_str) < 10:
            raise UserError(_(
                "Please provide more detailed source material "
                "(at least 2–3 sentences) for the AI to process."
            ))

        if len(content_str.split()) < 5:
            self.generated_result = self._format_ai_output("Insufficient content provided. Please supply at least a few sentences.")
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

        prompts = {
            'summary': 'Provide a clear summary of the source content.',
            'study_notes': 'Create structured study notes with bullet points from the content.',
            'flashcards': 'Create flashcards formatted strictly as:\nFront: [Question/Concept]\nBack: [Answer/Explanation]',
            'mcq': 'Generate 5 Multiple Choice Questions with options (A-D) and indicate the correct answer.',
            'short_answer': 'Generate 5 short-answer revision questions with sample answers.',
        }
        instruction = prompts.get(self.ai_action, 'Summarize the source content.')

        # Specific formatting instructions based on action type
        format_instructions = ""
        if self.ai_action == 'mcq':
            format_instructions = (
                "Format every question using sequential numbering (1., 2., 3.).\n"
                "List each choice on its own individual line directly below the question (A), B), C), D)).\n"
                "Put the correct answer on a new line directly after the choices, starting with 'Answer: '.\n"
                "Leave a single blank line before the next question.\n"
            )
        elif self.ai_action == 'short_answer':
            format_instructions = (
                "List each question on a new line with sequential numbering (1., 2., 3.).\n"
                "Place the answer on a new line directly below the question starting with 'Answer: '.\n"
                "Leave a single blank line before the next question.\n"
            )
        elif self.ai_action == 'flashcards':
            format_instructions = (
                "Present flashcards exclusively in a clean 2-column Markdown table.\n"
                "Column headers must be: | Front (Concept / Question) | Back (Definition / Answer) |\n"
                "Keep table rows compact, clear, and single-spaced.\n"
            )
        else: # summary or study_notes
            format_instructions = (
                "Group sections under bold text titles on a new line (e.g., **Section Title**).\n"
                "Use tight bullet points with bold inline terms.\n"
                "Enclose all code snippets inside language-tagged Markdown code blocks.\n"
            )

        system_instruction = (
            "You are an AI study assistant.\n"
            "CRITICAL MANDATE: Odoo web views require explicit HTML tags to display line breaks. You MUST format all output using inline HTML tags (<p>, <br/>, <b>, <ul>, <li>). Never output plain text newlines (\\n) or raw unformatted paragraphs. Do NOT wrap output in markdown code blocks. Wrap ONLY your final answer between the exact markers <<<ANSWER>>> and <<<END>>>. Put nothing else inside those markers except the requested content itself — no explanation, no draft attempts, no reasoning, no meta-commentary. If the source text is too short or unclear to work with, put exactly this inside the markers: 'Insufficient content provided.'\n\n"
            "FORMATTING SPECIFICATIONS:\n\n"
            "1. MULTIPLE CHOICE QUESTIONS (MCQ)\n"
            "<p>\n"
            "<b>1. [Question Text]</b><br/>\n"
            "A) [Option A]<br/>\n"
            "B) [Option B]<br/>\n"
            "C) [Option C]<br/>\n"
            "D) [Option D]<br/>\n"
            "<b>Answer:</b> [Correct Option]\n"
            "</p>\n"
            "<br/>\n\n"
            "2. SHORT ANSWER QUESTIONS\n"
            "<p>\n"
            "<b>1. [Question Text]</b><br/>\n"
            "<b>Answer:</b> [Detailed Answer Text]\n"
            "</p>\n"
            "<br/>\n\n"
            "3. FLASHCARDS\n"
            "<p>\n"
            "<b>Card 1</b><br/>\n"
            "<b>FRONT:</b> [Concept/Question]<br/>\n"
            "<b>BACK:</b> [Definition/Answer]\n"
            "</p>\n"
            "<br/>\n\n"
            "4. TECHNICAL NOTES & STUDY GUIDES\n"
            "<p><b>[Topic Title]</b></p>\n"
            "<ul>\n"
            "  <li><b>[Key Term]:</b> [Explanation]</li>\n"
            "</ul>"
        )
        full_prompt = f"{system_instruction}\n\nTask: {instruction}\n\nSource Text:\n{content}"

        from google.genai import types as genai_types
        response = None
        last_error = None
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=full_prompt,
                config=genai_types.GenerateContentConfig(
                    automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except Exception as e:
            last_error = e
            _logger.error("Gemini generation failed on model %s: %s", model_id, e)

        if not response or not getattr(response, 'text', None):
            raise UserError(_(
                "AI generation failed (model: %s).\nError: %s"
            ) % (model_id, last_error or 'No response received'))

        cleaned = self._clean_response(response.text)
        self.generated_result = self._format_ai_output(cleaned)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _format_ai_output(self, raw_text):
        _logger.info("=== _format_ai_output CALLED. Raw input length: %s ===", len(raw_text or ""))
        if not raw_text:
            wrapped_html = "<div class=\"o_ai_generated_content\">No response received from AI service.</div>"
            _logger.info("=== _format_ai_output OUTPUT (first 300 chars): %s ===", wrapped_html[:300])
            return Markup(wrapped_html)

        raw_text = self._sanitize_text(raw_text)

        # 1. Strip any accidental code fences
        cleaned_text = re.sub(r'^```(html|xml|json|markdown)?\s*', '', raw_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\s*```$', '', cleaned_text).strip()

        # 2. Detect whether the text already contains real HTML tags
        html_tags = ['<div', '<p', '<li', '<ul', '<strong>', '<table', '<tr', '<td', '<th', '<h1', '<h2', '<h3', '<br']
        has_html = any(tag in cleaned_text.lower() for tag in html_tags)

        if has_html:
            html_output = cleaned_text
        else:
            text = cleaned_text

            # Insert breaks before answer option letters: A) B) C) D)
            # We do NOT insert a break if it is immediately preceded by "Answer:"
            text = re.sub(r'(?<!Answer:)\s+([A-D]\))', r'\n\1', text)

            # Insert breaks before "Answer:"
            text = re.sub(r'\s+(Answer:)', r'\n\n\1', text)

            # Insert breaks before a new numbered question:
            text = re.sub(r'(?<=[a-z\.\)])\s+(\d{1,2}\.\s+[A-Z])', r'\n\n\1', text)

            # Fallback patterns for Q1./Flashcard N/Q:/A: style
            text = re.sub(r'\s+(Q\d+\.)', r'\n\n\1', text)
            text = re.sub(r'\s+(Flashcard\s+\d+)', r'\n\n\1', text)
            text = re.sub(r'\s+(Q:)', r'\n\n\1', text)
            text = re.sub(r'\s+(A:)', r'\n\1', text)

            # Split into question/card blocks
            # We use negative lookbehinds to ensure we don't split digit starts that are part of Q1., Q2., etc.
            blocks = re.split(r'(?<!Q)(?<!Q\d)(?=\b\d{1,2}\.\s[A-Z])|(?=Q\d+\.)|(?=Card\s+\d+)', text)
            blocks = [b.strip() for b in blocks if b.strip()]

            html_parts = []
            for block in blocks:
                # Check if it is a flashcard block
                if 'front:' in block.lower() or 'back:' in block.lower():
                    card_match = re.search(r'(Card\s+\d+)', block, re.IGNORECASE)
                    card_title = card_match.group(1).strip() if card_match else "Flashcard"
                    
                    front_match = re.search(r'FRONT:\s*(.+?)(?=\s*BACK:|$)', block, re.IGNORECASE | re.DOTALL)
                    back_match = re.search(r'BACK:\s*(.+)$', block, re.IGNORECASE | re.DOTALL)
                    
                    front_text = front_match.group(1).strip() if front_match else ""
                    back_text = back_match.group(1).strip() if back_match else ""
                    
                    html_parts.append('<div class="flashcard-item">')
                    html_parts.append(f'<p><strong>{card_title}</strong></p>')
                    html_parts.append(f'<p><strong>FRONT:</strong> {front_text}</p>')
                    html_parts.append(f'<p><strong>BACK:</strong> {back_text}</p>')
                    html_parts.append('</div>')
                else:
                    # MCQ / Question block
                    m = re.search(r'Answer:\s*(.+)$', block, re.IGNORECASE | re.DOTALL)
                    answer_text = m.group(1).strip() if m else None
                    question_part = block[:m.start()].strip() if m else block

                    opt_matches = list(re.finditer(r'([A-D]\))\s*(.+?)(?=\s[A-D]\)|$)', question_part))
                    if opt_matches:
                        question_text = question_part[:opt_matches[0].start()].strip()
                    else:
                        question_text = question_part.strip()

                    html_parts.append('<div class="mcq-item">')
                    html_parts.append(f'<p><strong>{question_text}</strong></p>')
                    if opt_matches:
                        html_parts.append('<ul>')
                        for om in opt_matches:
                            html_parts.append(f'<li>{om.group(1)} {om.group(2).strip()}</li>')
                        html_parts.append('</ul>')
                    if answer_text:
                        html_parts.append(f'<p><strong>Answer:</strong> {answer_text}</p>')
                    html_parts.append('</div>')
                    
            html_output = ''.join(html_parts)

        # 5. Wrap final HTML in a div container and return safe Markup
        wrapped_html = f"<div class=\"o_ai_generated_content\">{html_output}</div>"
        _logger.info("=== _format_ai_output OUTPUT (first 300 chars): %s ===", wrapped_html[:300])
        return Markup(wrapped_html)


    def _clean_response(self, raw_text):
        """Extract content between <<<ANSWER>>> and <<<END>>> markers, then strip code fences."""
        if not raw_text:
            return "No output generated. Please provide more detailed source material."
        raw_text = self._sanitize_text(raw_text)
        match = re.search(r'<<<ANSWER>>>(.*?)<<<END>>>', raw_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        _logger.warning("Response missing markers. Raw (first 300): %s", raw_text[:300])
        # Fallback: strip thought blocks, meta-commentary, then code fences
        cleaned = re.sub(r'<thought>.*?</thought>', '', raw_text, flags=re.DOTALL)
        meta_pattern = r'\*\s*(Strict Grounding Instruction|Constraint|Self[-\u2011]Correction|Did I|Task)[:]?[^*]*'
        cleaned = re.sub(meta_pattern, '', cleaned, flags=re.IGNORECASE)
        return cleaned
