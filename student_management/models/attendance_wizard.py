from odoo import models, fields, api

class AttendanceBatchWizard(models.TransientModel):
    _name = 'attendance.batch.wizard'
    _description = 'Batch Attendance Wizard'

    class_id = fields.Many2one('student.class', string="Class", required=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    session = fields.Selection([
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('full', 'Full Day')
    ], string="Session", required=True, default='full')
    teacher_id = fields.Many2one('student.teacher', string="Teacher/Recorder")
    
    attendance_line_ids = fields.One2many('attendance.batch.wizard.line', 'wizard_id', string="Students")

    @api.onchange('class_id')
    def _onchange_class_id(self):
        if self.class_id:
            students = self.env['student.student'].search([('class_id', '=', self.class_id.id)])
            lines = []
            for student in students:
                lines.append((0, 0, {
                    'student_id': student.id,
                    'status': 'present'
                }))
            self.attendance_line_ids = lines

    def action_mark_attendance(self):
        self.ensure_one()
        attendance_obj = self.env['student.attendance']
        for line in self.attendance_line_ids:
            attendance_obj.create({
                'student_id': line.student_id.id,
                'class_id': self.class_id.id,
                'date': self.date,
                'session': self.session,
                'teacher_id': self.teacher_id.id,
                'status': line.status,
                'note': line.note,
            })
        return {'type': 'ir.actions.act_window_close'}


class AttendanceBatchWizardLine(models.TransientModel):
    _name = 'attendance.batch.wizard.line'
    _description = 'Batch Attendance Wizard Line'

    wizard_id = fields.Many2one('attendance.batch.wizard', string="Wizard", ondelete='cascade')
    student_id = fields.Many2one('student.student', string="Student", required=True)
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused')
    ], string="Status", required=True, default='present')
    note = fields.Text(string="Behavioral Remark / Note")
