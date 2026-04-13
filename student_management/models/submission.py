from odoo import models, fields, api

class AssignmentSubmission(models.Model):
    _name = 'student.submission'
    _description = 'Student Assignment Submission'
    _order = "submission_date desc"

    name = fields.Char(string="Reference", compute="_compute_name", store=True, default="New Submission")
    assignment_id = fields.Many2one('teacher.assignment', string="Assignment", required=True)
    student_id = fields.Many2one('student.student', string="Student", required=True)
    submission_file = fields.Binary(string="Upload Assignment", required=True)
    file_name = fields.Char(string="File Name") 
    submission_date = fields.Datetime(string="Submission Date", default=fields.Datetime.now)
    notes = fields.Text(string="Student Notes")
    grade = fields.Selection([
        ('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'), ('f', 'F')
    ], string="Grade")
    teacher_feedback = fields.Text(string="Teacher Feedback")
    state = fields.Selection([
        ('draft', 'Draft'), ('submitted', 'Submitted'), ('graded', 'Graded')
    ], default='draft', string="Status")
    
    # New Dashboard Fields (Fixed Indentation)
    color = fields.Integer(string="Color Index")
    count = fields.Integer(string="Count", compute="_compute_count", store=True, default=1)

    @api.depends('student_id', 'assignment_id')
    def _compute_name(self):
        for record in self:
            if record.student_id and record.assignment_id:
                record.name = f"[{record.assignment_id.name}] - {record.student_id.name}"
            else:
                record.name = "New Submission"

    def _compute_count(self):
        for record in self:
            record.count = 1

    def action_submit(self):
        for record in self:
            record.state = 'submitted'

    def action_grade(self):
        for record in self:
            record.state = 'graded'