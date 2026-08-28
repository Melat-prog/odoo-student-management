from odoo import models, fields, api, _

class StudentExamSession(models.Model):
    _name = 'student.exam.session'
    _description = 'Exam Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Session Title", required=True, tracking=True)
    
    subject_id = fields.Many2one('student.subject', string="Subject")
    class_id = fields.Many2one('student.class', string="Class / Grade")
    course_id = fields.Many2one('student.course', string="Course")
    
    exam_type = fields.Selection([
        ('quiz', 'Quiz'), ('midterm', 'Mid-Term'), ('final', 'Final Exam'), ('exit', 'Exit Exam')
    ], string="Type", default='midterm', tracking=True)
    
    date = fields.Datetime(string="Exam Date & Time", default=fields.Datetime.now, required=True)
    
    max_score = fields.Float(string="Maximum Score", default=100.0)
    pass_mark = fields.Float(string="Pass Mark", default=50.0)
    
    teacher_id = fields.Many2one('student.teacher', string="Supervisor")
    
    state = fields.Selection([
        ('draft', 'Draft'), 
        ('scheduled', 'Scheduled'), 
        ('ongoing', 'Ongoing'), 
        ('completed', 'Completed'), 
        ('graded', 'Graded')
    ], default='draft', tracking=True)
    
    exam_line_ids = fields.One2many('student.exam', 'session_id', string="Student Results")

    def action_schedule(self):
        self.write({'state': 'scheduled'})
        
    def action_start(self):
        self.write({'state': 'ongoing'})
        
    def action_complete(self):
        self.write({'state': 'completed'})

    def action_fetch_students(self):
        self.ensure_one()
        domain = []
        if self.class_id:
            domain.append(('class_id', '=', self.class_id.id))
        elif self.course_id:
            domain.append(('course_id', '=', self.course_id.id))
            
        students = self.env['student.student'].search(domain) if domain else []
        lines = [(5, 0, 0)] 
        for student in students:
            lines.append((0, 0, {
                'student_id': student.id,
                'name': self.name,
                'exam_type': self.exam_type,
            }))
        self.exam_line_ids = lines

    def action_post(self):
        self.write({'state': 'graded'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})


class StudentExam(models.Model):
    _name = 'student.exam'
    _description = 'Student Examination'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Exam Title", required=True)
    session_id = fields.Many2one('student.exam.session', string="Session", ondelete='cascade')
    exam_type = fields.Selection([
        ('quiz', 'Quiz'), ('midterm', 'Mid-Term'), ('final', 'Final Exam'), ('exit', 'Exit Exam')
    ], string="Exam Type", required=True)
    
    date = fields.Date(string="Date", default=fields.Date.today)
    student_id = fields.Many2one('student.student', string="Student", required=True)
    
    max_marks = fields.Float(string="Maximum Marks", default=100.0)
    marks = fields.Float(string="Marks")
    percentage = fields.Float(string="Percentage", compute='_compute_percentage', store=True)
    grade = fields.Char(string="Grade", compute='_compute_grade', store=True)
    result_status = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string="Result", compute='_compute_result', store=True)

    @api.depends('marks', 'max_marks')
    def _compute_percentage(self):
        for record in self:
            if record.max_marks > 0:
                record.percentage = (record.marks / record.max_marks) * 100
            else:
                record.percentage = 0.0

    @api.depends('percentage')
    def _compute_grade(self):
        for record in self:
            if record.percentage >= 90: record.grade = 'A+'
            elif record.percentage >= 80: record.grade = 'A'
            elif record.percentage >= 70: record.grade = 'B'
            elif record.percentage >= 60: record.grade = 'C'
            elif record.percentage >= 50: record.grade = 'D'
            else: record.grade = 'F'

    @api.depends('marks', 'session_id.pass_mark')
    def _compute_result(self):
        for record in self:
            pass_mark = record.session_id.pass_mark if record.session_id else 50.0
            record.result_status = 'pass' if record.marks >= pass_mark else 'fail'
