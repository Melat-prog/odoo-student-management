from odoo import models, fields

class StudentEnrollmentHistory(models.Model):
    _name = 'student.enrollment.history'
    _description = 'Enrollment History'

    student_id = fields.Many2one('student.student', string="Student", required=True)
    course_id = fields.Many2one('student.course', string="Course")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    state = fields.Selection([
        ('applicant','Applicant'),
        ('enrolled','Enrolled'),
        ('promoted','Promoted'),
        ('graduated','Graduated')
    ], string="State")