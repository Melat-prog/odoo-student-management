from odoo import models, fields


class Teacher(models.Model):
    _name = "teacher.teacher"
    _description = "Teacher"

    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")

    specialization = fields.Char(string="Specialization")

    course_ids = fields.One2many(
        'student.course',
        'teacher_id',
        string="Courses"
    )