from odoo import models, fields


class StudentClass(models.Model):
    _name = 'student.class'
    _description = 'Class'

    name = fields.Char(required=True)
    code = fields.Char()

    student_ids = fields.One2many('student.student', 'class_id')
    subject_ids = fields.Many2many('student.subject')

    capacity = fields.Integer(string="Capacity")


class StudentSubject(models.Model):
    _name = 'student.subject'
    _description = 'Subject'

    name = fields.Char(required=True)
    code = fields.Char()
    teacher_id = fields.Many2one('teacher.teacher', string="Teacher")