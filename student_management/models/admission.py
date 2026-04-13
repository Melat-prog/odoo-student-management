from odoo import models, fields


class AdmissionApplication(models.Model):
    _name = 'admission.application'
    _description = 'Admission Application'

    name = fields.Char(required=True)
    email = fields.Char()
    phone = fields.Char()

    applied_class_id = fields.Many2one('student.class', string="Applied Class")
    student_id = fields.Many2one('student.student')

    teacher_id = fields.Many2one('teacher.teacher', string="Teacher")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft')

    def action_submit(self):
        for record in self:
            record.state = 'submitted'

    def action_approve(self):
        for record in self:
            record.state = 'approved'

            new_student = self.env['student.student'].create({
                'name': record.name,
                'email': record.email,
                'phone': record.phone,
                'class_id': record.applied_class_id.id,
                'state': 'enrolled'
            })

            record.student_id = new_student.id

    def action_reject(self):
        for record in self:
            record.state = 'rejected'