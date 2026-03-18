from odoo import models, fields
from odoo.exceptions import ValidationError


class Student(models.Model):
    _name = 'student.student'
    _description = 'Student'

    name = fields.Char(string="Name", required=True)
    age = fields.Integer(string="Age")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    note = fields.Text(string="Notes")

    course_id = fields.Many2one(
        'student.course',
        string="Course"
    )
    attendance_ids = fields.One2many(
    'student.attendance',
    'student_id',
    string="Attendance Records"
)
    attendance_count = fields.Integer(
    string="Attendance Count",
    compute="_compute_attendance_count"
)
    def _compute_attendance_count(self):
     for record in self:
        record.attendance_count = len(record.attendance_ids)

    def create(self, vals):
        course = self.env['student.course'].browse(vals.get('course_id'))

        if course.capacity and len(course.student_ids) >= course.capacity:
         raise ValidationError(
    "Cannot enroll student. The course has already reached its maximum number of students."
)
        return super().create(vals)
    def action_view_attendance(self):
     return {
        'name': 'Attendance',
        'type': 'ir.actions.act_window',
        'res_model': 'student.attendance',
        'view_mode': 'list,form',
        'domain': [('student_id', '=', self.id)],
    }
    