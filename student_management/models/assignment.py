from odoo import models, fields, api

class TeacherAssignment(models.Model):
    _name = 'teacher.assignment'
    _description = 'Teacher Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string="Assignment Title")
    
    # FIXED: Correct comodel name
    teacher_id = fields.Many2one('student.teacher', string="Teacher", required=True)
    
    subject_id = fields.Many2one('student.subject', string="Subject")
    class_id = fields.Many2one('student.class', string="Class")
    attachment_ids = fields.Many2many('ir.attachment', string="Documents")
    description = fields.Text()
    submission_count = fields.Integer(compute='_compute_submission_count', string="Submissions")

    issue_date = fields.Date(string="Issue Date", default=fields.Date.context_today)
    due_date = fields.Date(string="Due Date", required=True)
    
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], default='new', tracking=True)

    @api.depends('name') # Added basic dependency to ensure it triggers
    def _compute_submission_count(self):
        for record in self:
            # We use a try/except in case student.submission isn't loaded yet
            try:
                record.submission_count = self.env['student.submission'].search_count([
                    ('assignment_id', '=', record.id)
                ])
            except:
                record.submission_count = 0

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