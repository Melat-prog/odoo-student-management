from odoo import models, fields


class StudentAttendance(models.Model):
    _name = 'student.attendance'
    _description = 'Student Attendance'

    student_id = fields.Many2one('student.student', string="Student", required=True)

    course_id = fields.Many2one('student.course', string="Course")  # ✅ ADD THIS

    date = fields.Date(required=True)

    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
    ], default='present')

    note = fields.Text(string="Note")