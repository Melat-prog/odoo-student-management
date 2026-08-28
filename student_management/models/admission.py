from odoo import models, fields, api, _

class AdmissionApplication(models.Model):
    _name = 'admission.application'
    _description = 'Admission Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    reference = fields.Char(string="Reference", readonly=True, copy=False, default='New')
    name = fields.Char(required=True, tracking=True)
    email = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    application_date = fields.Date(string="Application Date", default=fields.Date.today, tracking=True)
    notes = fields.Text(string="Notes")

    applied_class_id = fields.Many2one('student.class', string="Applied Class")
    student_id = fields.Many2one('student.student', string="Created Student")

    # FIXED: Correct comodel name
    teacher_id = fields.Many2one('student.teacher', string="Interviewed By")

    state = fields.Selection([
        ('draft', 'Applicant'),
        ('review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], default='draft', string="Status", tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('reference', 'New') == 'New':
            vals['reference'] = self.env['ir.sequence'].next_by_code('admission.application') or 'ADM/NEW'
        return super().create(vals)

    def action_submit(self):
        for record in self:
            record.state = 'review'
        return True

    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'
        return True

    def action_accept(self):
        for record in self:
            record.state = 'accepted'
            if not record.student_id:
                new_student = self.env['student.student'].create({
                    'name': record.name,
                    'email': record.email,
                    'phone': record.phone,
                    'class_id': record.applied_class_id.id,
                })
                new_student.action_enroll()
                record.student_id = new_student.id
        return True

    def action_reject(self):
        for record in self:
            record.state = 'rejected'
        return True

    def action_view_student(self):
        self.ensure_one()
        return {
            'name': 'Student',
            'type': 'ir.actions.act_window',
            'res_model': 'student.student',
            'view_mode': 'form',
            'res_id': self.student_id.id,
        }