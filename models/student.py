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
        compute="_compute_attendance_stats"
    )

    present_count = fields.Integer(
        string="Present Count",
        compute="_compute_attendance_stats"
    )

    absent_count = fields.Integer(
        string="Absent Count",
        compute="_compute_attendance_stats"
    )

    attendance_percentage = fields.Float(
        string="Attendance %",
        compute="_compute_attendance_stats"
    )

    def _compute_attendance_stats(self):
        for record in self:
            total = len(record.attendance_ids)
            present = len(record.attendance_ids.filtered(lambda a: a.status == 'present'))
            absent = len(record.attendance_ids.filtered(lambda a: a.status == 'absent'))

            record.attendance_count = total
            record.present_count = present
            record.absent_count = absent

            if total > 0:
                record.attendance_percentage = (present / total) * 100
            else:
                record.attendance_percentage = 0

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
    def action_view_attendance(self):
     self.ensure_one()
     return {
        'name': 'Attendance',
        'type': 'ir.actions.act_window',
        'res_model': 'student.attendance',
        'view_mode': 'list,form,calendar',
        'domain': [('student_id', '=', self.id)],
        'context': {
            'default_student_id': self.id,
            'default_course_id': self.course_id.id,
        },
    }