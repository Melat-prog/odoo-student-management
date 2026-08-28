from odoo import models, fields, api

class StudentDashboard(models.TransientModel):
    _name = 'student.dashboard'
    _description = 'Student Management Dashboard'

    name = fields.Char(default="Dashboard")
    
    student_count = fields.Integer(compute='_compute_stats')
    teacher_count = fields.Integer(compute='_compute_stats')
    course_count = fields.Integer(compute='_compute_stats')
    pending_submissions = fields.Integer(compute='_compute_stats')
    attendance_percentage = fields.Float(compute='_compute_stats')

    def _compute_stats(self):
        for record in self:
            record.student_count = self.env['student.student'].search_count([])
            record.teacher_count = self.env['student.teacher'].search_count([])
            record.course_count = self.env['student.course'].search_count([])
            record.pending_submissions = self.env['student.submission'].search_count([('state', '=', 'submitted')])
            
            # Calculate overall attendance percentage
            total_attendance = self.env['student.attendance'].search_count([])
            present_attendance = self.env['student.attendance'].search_count([('status', '=', 'present')])
            
            if total_attendance > 0:
                record.attendance_percentage = (present_attendance / total_attendance) * 100.0
            else:
                record.attendance_percentage = 0.0

    def action_view_students(self):
        return {
            'name': 'Students',
            'type': 'ir.actions.act_window',
            'res_model': 'student.student',
            'view_mode': 'list,form',
        }

    def action_view_teachers(self):
        return {
            'name': 'Teachers',
            'type': 'ir.actions.act_window',
            'res_model': 'student.teacher',
            'view_mode': 'list,form',
        }

    def action_view_courses(self):
        return {
            'name': 'Courses',
            'type': 'ir.actions.act_window',
            'res_model': 'student.course',
            'view_mode': 'list,form',
        }

    def action_view_submissions(self):
        return {
            'name': 'Pending Submissions',
            'type': 'ir.actions.act_window',
            'res_model': 'student.submission',
            'domain': [('state', '=', 'submitted')],
            'view_mode': 'list,form',
        }
