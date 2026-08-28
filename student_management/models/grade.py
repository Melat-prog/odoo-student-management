from odoo import models, fields, api

class StudentGrade(models.Model):
    _name = 'student.grade'
    _description = 'Student Grades'

    student_id = fields.Many2one('student.student', string="Student", required=True)
    subject_id = fields.Many2one('student.subject', string="Subject", required=True)
    teacher_id = fields.Many2one('student.teacher', string="Teacher", related='subject_id.teacher_id', readonly=True)
    
    # Source Tracking
    assignment_id = fields.Many2one('teacher.assignment', string="Related Assignment")
    exam_id = fields.Many2one('student.exam', string="Related Exam")
    
    evaluation_type = fields.Selection([
        ('percentage', 'Percentage / Marks'),
        ('letter', 'Letter Grade Only'),
        ('pass_fail', 'Pass / Fail')
    ], string="Grading Type", default='percentage', required=True)
    
    # Value fields
    marks = fields.Float(string="Marks Achieved")
    max_marks = fields.Float(string="Maximum Marks", default=100.0)
    pass_mark = fields.Float(string="Pass Mark", default=50.0)
    
    grade_letter = fields.Char(string="Letter Grade", compute="_compute_grade", store=True, readonly=False)
    is_pass = fields.Boolean(string="Passed", compute="_compute_pass", store=True)
    
    remark = fields.Text(string="Teacher's Feedback")

    @api.depends('marks', 'max_marks', 'evaluation_type', 'grade_letter')
    def _compute_grade(self):
        for record in self:
            if record.evaluation_type == 'percentage' and record.max_marks > 0:
                percentage = (record.marks / record.max_marks) * 100
                if percentage >= 90:
                    record.grade_letter = 'A+'
                elif percentage >= 80:
                    record.grade_letter = 'A'
                elif percentage >= 70:
                    record.grade_letter = 'B'
                elif percentage >= 50:
                    record.grade_letter = 'C'
                else:
                    record.grade_letter = 'F'
            elif record.evaluation_type == 'pass_fail':
                if record.marks >= record.pass_mark:
                    record.grade_letter = 'Pass'
                else:
                    record.grade_letter = 'Fail'

    @api.depends('marks', 'pass_mark', 'evaluation_type', 'grade_letter')
    def _compute_pass(self):
        for record in self:
            if record.evaluation_type in ('percentage', 'pass_fail'):
                record.is_pass = record.marks >= record.pass_mark
            else:
                # For letter grades without marks, depend on manual entry
                record.is_pass = record.grade_letter not in ('F', 'Fail', False)
                