from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Student(models.Model):
    _name = 'student.student'
    _description = 'Student'

    name = fields.Char(required=True)
    student_id = fields.Char(readonly=True, copy=False)

    age = fields.Integer()
    email = fields.Char()
    phone = fields.Char()
    note = fields.Text()

    course_id = fields.Many2one('student.course')
    class_id = fields.Many2one('student.class', string="Class")
    enrollment_date = fields.Date()

    state = fields.Selection([
        ('applicant', 'Applicant'),
        ('enrolled', 'Enrolled'),
        ('promoted', 'Promoted'),
        ('graduated', 'Graduated')
    ], default='applicant')

    attendance_ids = fields.One2many(
        'student.attendance',
        'student_id'
    )

    attendance_count = fields.Integer(
        compute="_compute_attendance_stats"
    )
    present_count = fields.Integer(
        compute="_compute_attendance_stats"
    )
    absent_count = fields.Integer(
        compute="_compute_attendance_stats"
    )
    attendance_percentage = fields.Float(
        compute="_compute_attendance_stats"
    )

    # New field for Enrollment History tab
    current_course_info = fields.Char(
        string="Current Enrollment",
        compute="_compute_current_course_info",
        store=True
    )

    def _compute_attendance_stats(self):
        for record in self:
            total = len(record.attendance_ids)
            present = len(record.attendance_ids.filtered(lambda a: a.status == 'present'))
            absent = len(record.attendance_ids.filtered(lambda a: a.status == 'absent'))

            record.attendance_count = total
            record.present_count = present
            record.absent_count = absent
            record.attendance_percentage = (present / total * 100) if total else 0

    @api.depends('course_id', 'enrollment_date', 'state')
    def _compute_current_course_info(self):
        for record in self:
            if record.course_id and record.enrollment_date:
                record.current_course_info = f"{record.course_id.name} ({record.enrollment_date}) - {record.state}"
            else:
                record.current_course_info = "Not enrolled"

    @api.model
    def create(self, vals):
        course = self.env['student.course'].browse(vals.get('course_id'))
        if course and course.capacity and len(course.student_ids) >= course.capacity:
            raise ValidationError("Course capacity reached.")

        if not vals.get('student_id'):
            vals['student_id'] = self.env['ir.sequence'].next_by_code('student.student') or 'STD000'

        return super(Student, self).create(vals)

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

    # State transition methods
    def action_enroll(self):
        for record in self:
            record.state = 'enrolled'
            record.enrollment_date = fields.Date.today()

    def action_promote(self):
        for record in self:
            record.state = 'promoted'

    def action_graduate(self):
        for record in self:
            record.state = 'graduated'

    def action_set_applicant(self):
        for record in self:
            record.state = 'applicant'
            record.enrollment_date = False