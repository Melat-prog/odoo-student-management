from odoo import models, fields, api

class StudentCourse(models.Model):
    _name = 'student.course'
    _description = 'Student Course'

    name = fields.Char(string="Course Name", required=True)
    code = fields.Char(string="Course Code")
    active = fields.Boolean(string='Active', default=True)
    
    # NEW: Grade selection
    grade = fields.Selection([
        ('grade_9', 'Grade 9'),
        ('grade_10', 'Grade 10'),
        ('grade_11', 'Grade 11'),
        ('grade_12', 'Grade 12'),
        ('university', 'University Level')
    ], string="Target Grade")

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    fees = fields.Monetary(string="Course Fees", currency_field='currency_id')
    duration = fields.Integer(string="Duration")
    duration_unit = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ], string="Unit")
    
    description = fields.Text(string="Description")
    capacity = fields.Integer(string="Maximum Students")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed')
    ], string="Status", default='draft')

    teacher_id = fields.Many2one('student.teacher', string="Course Instructor")
    
    # NEW: Additional Teachers Tab relationship
    additional_teacher_ids = fields.Many2many('student.teacher', string="Assistant Teachers")
    
    # NEW: Lesson Plan relationship
    lesson_plan_ids = fields.One2many('student.course.lesson', 'course_id', string="Lesson Plan")
    resource_ids = fields.One2many('student.learning.resource', 'course_id', string="Learning Resources")

    student_ids = fields.One2many('student.student', 'course_id', string="Registered Students")
    student_count = fields.Integer(string="Total Student Count", compute="_compute_student_count")

    @api.depends('student_ids')
    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)

    def action_view_students(self):
        return {
            'name': 'Students',
            'type': 'ir.actions.act_window',
            'res_model': 'student.student',
            'view_mode': 'list,form',
            'domain': [('course_id', '=', self.id)],
        }

    def action_open_course(self):
        for record in self:
            record.state = 'open'

    def action_close_course(self):
        for record in self:
            record.state = 'closed'

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'

    @api.model
    def _register_hook(self):
        super()._register_hook()
        # Deactivate the default Odoo contactus page to allow our custom redirect to trigger
        try:
            contact_page = self.env['website.page'].sudo().search([('url', '=', '/contactus')])
            if contact_page:
                contact_page.write({'active': False})
        except Exception:
            pass

# NEW MODEL FOR THE LESSON PLAN TAB
class StudentCourseLesson(models.Model):
    _name = 'student.course.lesson'
    _description = 'Course Lesson Plan'
    _order = 'sequence'

    sequence = fields.Integer(string="Sequence", default=10)
    course_id = fields.Many2one('student.course', string="Course", ondelete='cascade')
    name = fields.Char(string="Lesson Topic", required=True)
    content = fields.Text(string="Key Objectives")
    duration_minutes = fields.Integer(string="Duration (Mins)")

# student.subject, student.class, and student.teacher.assignment models
# are defined canonically in models/student.py — do not redefine here.

class StudentLearningResource(models.Model):
    _name = 'student.learning.resource'
    _description = 'Learning Resource'
    _order = 'sequence, id'
    
    name = fields.Char(string="Title", required=True)
    sequence = fields.Integer(default=10)
    
    resource_type = fields.Selection([
        ('document', 'Document (PDF, Word, etc.)'),
        ('video', 'Video (YouTube, MP4)'),
        ('link', 'External Link/Website'),
        ('other', 'Other')
    ], string="Type", required=True, default='document')
    
    description = fields.Text(string="Description")
    
    subject_id = fields.Many2one('student.subject', string="Subject")
    course_id = fields.Many2one('student.course', string="Course")
    
    file_attachment = fields.Binary(string="File Attachment")
    file_name = fields.Char(string="File Name")
    
    url = fields.Char(string="Resource URL")
    
    visibility = fields.Selection([
        ('public', 'Public'),
        ('students', 'Enrolled Students Only'),
        ('teachers', 'Teachers Only')
    ], string="Visibility", default='students')
    
    active = fields.Boolean(default=True)