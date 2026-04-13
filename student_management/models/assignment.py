from odoo import models, fields, api

class TeacherAssignment(models.Model):
    _name = 'teacher.assignment'
    _description = 'Teacher Assignment'

    name = fields.Char(required=True)
    teacher_id = fields.Many2one('teacher.teacher', string="Teacher", required=True)
    subject_id = fields.Many2one('student.subject', string="Subject")
    class_id = fields.Many2one('student.class', string="Class")
    attachment_ids = fields.Many2many('ir.attachment', string="Documents")
    description = fields.Text()
    submission_count = fields.Integer(compute='_compute_submission_count', string="Submissions")

    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], default='new')
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'Ongoing'),
        ('done', 'Done')
    ], default='draft', string="Status")

    def _compute_submission_count(self):
        for record in self:
            record.submission_count = self.env['student.submission'].search_count([
                ('assignment_id', '=', record.id)
            ])

    def action_view_submissions(self):
        return {
            'name': 'Submissions',
            'type': 'ir.actions.act_window',
            'res_model': 'student.submission',
            'view_mode': 'list,form',
            'domain': [('assignment_id', '=', self.id)],
            'context': {'default_assignment_id': self.id},
            'target': 'current',
        }

    def action_start(self):
        for record in self:
            record.state = 'in_progress'

    def action_complete(self):
        for record in self:
            record.state = 'completed'