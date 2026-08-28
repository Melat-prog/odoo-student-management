from odoo import models, fields

class StudentEnrollmentHistory(models.Model):
    _name = 'student.enrollment.history'
    _description = 'Enrollment History'

    student_id = fields.Many2one('student.student', string="Student", required=True, ondelete='cascade')
    course_id = fields.Many2one('student.course', string="Course")
    class_id = fields.Many2one('student.class', string="Class Section")
    academic_year_id = fields.Many2one('student.academic.year', string="Academic Year")
    grade_level_id = fields.Many2one('student.grade.level', string="Grade Level")
    
    start_date = fields.Date(string="Start Date", default=fields.Date.context_today)
    end_date = fields.Date(string="End Date")
    state = fields.Selection([
        ('enrolled','Enrolled'),
        ('promoted','Promoted'),
        ('graduated','Graduated'),
        ('dropped', 'Dropped Out')
    ], string="State", required=True)
    note = fields.Text(string="Notes")