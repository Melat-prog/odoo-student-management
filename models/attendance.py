from odoo import models, fields, api


class Attendance(models.Model):
    _name = "student.attendance"
    _description = "Student Attendance"

    student_id = fields.Many2one(
        'student.student',
        string="Student",
        required=True
    )

    course_id = fields.Many2one(
        'student.course',
        string="Course",
        required=True
    )

    date = fields.Date(string="Date", required=True)

    status = fields.Selection(
        [
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late')
        ],
        string="Status",
        default='present'
    )

    note = fields.Text(string="Notes")

    @api.onchange('student_id')
    def _onchange_student(self):
        if self.student_id:
            self.course_id = self.student_id.course_id