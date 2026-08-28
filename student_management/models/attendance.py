from odoo import models, fields


class StudentAttendance(models.Model):
    _name = 'student.attendance'
    _description = 'Student Attendance'

    student_id = fields.Many2one('student.student', string="Student", required=True, ondelete='cascade')
    class_id = fields.Many2one('student.class', string="Class", required=True, store=True)
    course_id = fields.Many2one('student.course', string="Course/Subject")
    teacher_id = fields.Many2one('student.teacher', string="Teacher/Recorder")
    
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    session = fields.Selection([
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('full', 'Full Day')
    ], string="Session", default='full')

    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused')
    ], default='present', required=True)

    note = fields.Text(string="Note")