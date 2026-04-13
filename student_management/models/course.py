from odoo import models, fields

class Course(models.Model):
    _name = "student.course"
    _description = "Course"

    name = fields.Char(string="Course Name")

    teacher_id = fields.Many2one(
        'teacher.teacher',
        string="Teacher"
    )

    duration = fields.Integer(string="Duration")

    duration_unit = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ], string="Unit")

    description = fields.Text(string="Description")

    capacity = fields.Integer(string="Maximum Students")

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('closed', 'Closed')
        ],
        string="Status",
        default='draft'
    )

    # UPDATED STRINGS BELOW TO AVOID DUPLICATES
    student_ids = fields.One2many(
        'student.student',
        'course_id',
        string="Registered Students"
    )

    student_count = fields.Integer(
        string="Total Student Count",
        compute="_compute_student_count"
    )

    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)

    def action_view_students(self):
        return {
            'name': 'Students',
            'type': 'ir.actions.act_window',
            'res_model': 'student.student',
            'view_mode': 'list,form',
            'domain': [('course_id', '=', self.id)],
        }

    # ADDED 'for record' LOOPS TO PREVENT SINGLETON ERRORS
    def action_open_course(self):
        for record in self:
            record.state = 'open'

    def action_close_course(self):
        for record in self:
            record.state = 'closed'

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'