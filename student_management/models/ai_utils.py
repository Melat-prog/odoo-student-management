from odoo import models
import base64
import io
import requests
from bs4 import BeautifulSoup
import pypdf
import logging

_logger = logging.getLogger(__name__)


class AIExtractionMixin(models.AbstractModel):
    _name = 'ai.extraction.mixin'
    _description = 'AI Extraction Mixin'

    @staticmethod
    def _sanitize_text(text):
        """Remove NUL bytes and other characters PostgreSQL rejects in text fields."""
        if not text:
            return ''
        return str(text).replace('\x00', '').replace('\0', '').strip()

    @staticmethod
    def _safe_decode_bytes(raw_bytes):
        if not raw_bytes:
            return ""
        decoded_text = raw_bytes.decode('utf-8', errors='ignore')
        return decoded_text.replace('\x00', '').replace('\0', '').strip()

    def _extract_text_from_binary(self, file_data, file_name=''):
        """Extract text from binary file data based on extension (PDF, DOCX, TXT)."""
        if not file_data:
            return ""
        file_name = (file_name or '').lower()
        extracted_text = ""

        if file_name.endswith('.pdf'):
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_data))
                for page in reader.pages:
                    raw_page_text = page.extract_text() or ''
                    # Clean NUL bytes from page segments immediately
                    extracted_text += raw_page_text.replace('\x00', '').replace('\0', '') + "\n"
            except Exception as e:
                _logger.warning("PDF extraction failed for %s: %s", file_name, e)
        elif file_name.endswith('.docx'):
            try:
                import docx
                doc = docx.Document(io.BytesIO(file_data))
                # Clean paragraphs immediately
                paragraphs = [p.text.replace('\x00', '').replace('\0', '') for p in doc.paragraphs]
                extracted_text = '\n'.join(paragraphs)
            except Exception as e:
                _logger.warning("DOCX extraction failed for %s: %s", file_name, e)
        else:
            try:
                extracted_text = self._safe_decode_bytes(file_data)
            except Exception as e:
                _logger.warning("Text decoding failed for %s: %s", file_name, e)

        return self._sanitize_text(extracted_text)

    def _get_extracted_text(self, resource_id=None, custom_text=None, file_attachment=None, file_name=None):
        """
        Shared method to extract text from:
        1. Direct custom_text
        2. Direct file_attachment binary
        3. Learning Resource record (file_attachment, ir.attachment, URL, description)
        4. Record ir.attachments
        """
        resource_content = ""

        # 1. Custom text provided directly
        if custom_text and str(custom_text).strip():
            resource_content = str(custom_text).strip()

        # 2. Extract from direct binary attachment if passed
        if not resource_content and file_attachment:
            try:
                file_data = base64.b64decode(file_attachment)
                resource_content = self._extract_text_from_binary(file_data, file_name)
            except Exception as e:
                _logger.warning("Failed to decode direct file_attachment: %s", e)

        # 3. Extract from Learning Resource record if provided
        if not resource_content and resource_id:
            res = resource_id

            # 3a. Resource Binary field (file_attachment)
            if hasattr(res, 'file_attachment') and res.file_attachment:
                try:
                    file_data = base64.b64decode(res.file_attachment)
                    fname = getattr(res, 'file_name', '') or ''
                    resource_content = self._extract_text_from_binary(file_data, fname)
                except Exception as e:
                    _logger.warning("Failed to decode resource file_attachment: %s", e)

            # 3b. Resource ir.attachment records
            if not resource_content.strip():
                attachments = self.env['ir.attachment'].sudo().search([
                    ('res_model', '=', res._name),
                    ('res_id', '=', res.id)
                ], limit=5)
                for att in attachments:
                    if att.datas:
                        try:
                            file_data = base64.b64decode(att.datas)
                            fname = att.name or ''
                            extracted = self._extract_text_from_binary(file_data, fname)
                            if extracted.strip():
                                resource_content += "\n" + extracted
                        except Exception as e:
                            _logger.warning("Failed to extract ir.attachment %s: %s", att.name, e)

            # 3c. Resource URL
            if not resource_content.strip():
                url = getattr(res, 'resource_url', None) or getattr(res, 'url', None)
                if url:
                    try:
                        response_req = requests.get(url, timeout=10)
                        if response_req.status_code == 200:
                            soup = BeautifulSoup(response_req.content, 'html.parser')
                            paragraphs = [p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'article'])]
                            resource_content = self._sanitize_text('\n'.join(paragraphs))
                    except Exception as e:
                        _logger.warning('Failed to fetch URL %s: %s', url, e)

            # 3d. Fallback to description/text
            if not resource_content.strip():
                resource_content = self._sanitize_text(
                    getattr(res, 'description', None) or
                    getattr(res, 'text', None) or
                    getattr(res, 'content', '') or ''
                )

        # 4. Check ir.attachment attached to the wizard record itself
        if not resource_content and hasattr(self, 'id') and self.id and hasattr(self, '_name'):
            attachments = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id)
            ], limit=5)
            for att in attachments:
                if att.datas:
                    try:
                        file_data = base64.b64decode(att.datas)
                        fname = att.name or ''
                        extracted = self._extract_text_from_binary(file_data, fname)
                        if extracted.strip():
                            resource_content += "\n" + extracted
                    except Exception as e:
                        _logger.warning("Failed to extract ir.attachment %s: %s", att.name, e)

        return self._sanitize_text(resource_content)
