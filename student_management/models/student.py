from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Student(models.Model):
    _name = 'student.student'
    _description = 'Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    student_id = fields.Char(string="Student ID", readonly=True, copy=False)
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    age = fields.Integer(tracking=True)
    email = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    note = fields.Text()
    
    parent_ids = fields.Many2many('student.parent', 'student_parent_rel', 'student_id', 'parent_id', string="Parents / Guardians")

    course_id = fields.Many2one('student.course', string="Course", tracking=True)
    class_id = fields.Many2one('student.class', string="Class")
    enrollment_date = fields.Date(readonly=True)
    state = fields.Selection([
        ('applicant', 'Applicant'),
        ('enrolled', 'Enrolled'),
        ('promoted', 'Promoted'),
        ('graduated', 'Graduated')
    ], default='applicant', tracking=True)

    current_course_info = fields.Char(string="Current Enrollment", compute="_compute_current_course_info", store=True)

    partner_id = fields.Many2one('res.partner', string="Related Partner", ondelete='cascade', readonly=True)
    user_id = fields.Many2one('res.users', string="Portal User", help="Used for portal access")
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    total_fees = fields.Monetary(string="Total Fees", related='course_id.fees', store=True, currency_field='currency_id')
    amount_paid = fields.Monetary(string="Amount Paid", compute='_compute_payments', store=True, currency_field='currency_id')
    balance_amount = fields.Monetary(string="Balance", compute='_compute_payments', store=True, currency_field='currency_id')
    payment_status = fields.Selection([
        ('draft', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid')
    ], compute='_compute_payments', store=True)
    
    invoice_ids = fields.One2many('account.move', 'student_id', string="Invoices")

    attendance_ids = fields.One2many('student.attendance', 'student_id')
    attendance_count = fields.Integer(compute='_compute_attendance_stats')
    present_count = fields.Integer(compute='_compute_attendance_stats')
    absent_count = fields.Integer(compute='_compute_attendance_stats')
    attendance_percentage = fields.Float(compute='_compute_attendance_stats', aggregator="avg")

    grade_ids = fields.One2many('student.grade', 'student_id')
    exam_line_ids = fields.One2many('student.exam', 'student_id', string="Exam Lines")
    grade_count = fields.Integer(compute='_compute_cgpa', store=True)
    cgpa = fields.Float(string="CGPA", compute='_compute_cgpa', digits=(1, 2), store=True)

    @api.model
    def create(self, vals):
        if vals.get('course_id'):
            course = self.env['student.course'].browse(vals.get('course_id'))
            if course and course.capacity and len(course.student_ids) >= course.capacity:
                raise ValidationError(_("Registration failed: The course '%s' is full.", course.name))
        
        if not vals.get('student_id'):
            vals['student_id'] = self.env['ir.sequence'].next_by_code('student.student') or 'STD/NEW'
            
        return super(Student, self).create(vals)

    @api.depends('invoice_ids.payment_state', 'invoice_ids.amount_total', 'invoice_ids.amount_residual')
    def _compute_payments(self):
        for record in self:
            invoices = record.invoice_ids.filtered(lambda inv: inv.state == 'posted' and inv.move_type == 'out_invoice')
            
            total_invoiced = sum(invoices.mapped('amount_total'))
            total_due = sum(invoices.mapped('amount_residual'))
            record.amount_paid = total_invoiced - total_due
            record.balance_amount = total_due
            
            if record.amount_paid <= 0:
                record.payment_status = 'draft'
            elif record.balance_amount > 0:
                record.payment_status = 'partial'
            else:
                record.payment_status = 'paid'

    @api.depends('attendance_ids', 'attendance_ids.status')
    def _compute_attendance_stats(self):
        for rec in self:
            all_att = rec.attendance_ids
            if all_att:
                present = len(all_att.filtered(lambda x: x.status == 'present'))
                rec.attendance_count = len(all_att)
                rec.present_count = present
                rec.absent_count = len(all_att) - present
                rec.attendance_percentage = (present / len(all_att)) * 100
            else:
                rec.attendance_count = 0
                rec.present_count = 0
                rec.absent_count = 0
                rec.attendance_percentage = 0.0

    @api.depends('grade_ids.marks', 'grade_ids.max_marks', 'grade_ids.evaluation_type', 'exam_line_ids.marks')
    def _compute_cgpa(self):
        for record in self:
            # Only consider percentage evaluation types for CGPA from assignments
            valid_grades = [g for g in record.grade_ids if g.evaluation_type == 'percentage' and g.max_marks > 0]
            
            # Calculate points for assignments
            grade_points = sum((g.marks / g.max_marks) * 4.0 for g in valid_grades)
            
            # Legacy exam marks (assuming 100 max)
            exam_points = sum((e.marks / 100.0) * 4.0 for e in record.exam_line_ids)
            
            total_points = grade_points + exam_points
            record.grade_count = len(valid_grades) + len(record.exam_line_ids)
            
            if record.grade_count > 0:
                record.cgpa = total_points / record.grade_count
            else:
                record.cgpa = 0.0

    @api.depends('course_id', 'enrollment_date', 'state')
    def _compute_current_course_info(self):
        for record in self:
            if record.course_id and record.enrollment_date:
                record.current_course_info = f"{record.course_id.name} ({record.enrollment_date}) - {record.state}"
            else:
                record.current_course_info = "Not enrolled"

    def action_enroll(self):
        for record in self:
            record.state = 'enrolled'
            record.enrollment_date = fields.Date.today()
            self._create_enrollment_history('enrolled', "Student enrolled")
            
            # Auto-generate invoice if course has fees
            if record.course_id and record.course_id.fees > 0:
                self._generate_course_invoice(record)
        return True
                
    def _generate_course_invoice(self, student):
        if not student.partner_id:
            # Create a partner if none exists
            partner = self.env['res.partner'].create({
                'name': student.name,
                'email': student.email,
                'phone': student.phone,
                'is_company': False,
            })
            student.partner_id = partner.id
            
        invoice = self.env['account.move'].create({
            'partner_id': student.partner_id.id,
            'move_type': 'out_invoice',
            'student_id': student.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': f"Tuition Fee: {student.course_id.name}",
                'price_unit': student.course_id.fees,
                'quantity': 1,
            })],
        })
        # Optional: auto-post the invoice
        # invoice.action_post()
        return invoice

    @api.constrains('age')
    def _check_age(self):
        for student in self:
            if student.age < 0:
                raise ValidationError("Age cannot be negative.")

    def action_create_user(self):
        for record in self:
            if record.user_id:
                continue
            group_portal = self.env.ref('base.group_portal', raise_if_not_found=False)
            group_student = self.env.ref('student_management.group_student', raise_if_not_found=False)
            user = self.env['res.users'].create({
                'name': record.name,
                'login': record.email or f"{record.id}@student.local",
                'password': 'password123',
                'groups_id': [(6, 0, [g.id for g in (group_portal, group_student) if g])]
            })
            record.user_id = user.id

    def action_promote(self):
        for record in self:
            record.state = 'promoted'
            self._create_enrollment_history('promoted', "Student promoted")
        return True

    def action_graduate(self):
        for record in self:
            record.state = 'graduated'
            self._create_enrollment_history('graduated', "Student graduated")
        return True

    def action_set_applicant(self):
        for record in self:
            record.state = 'applicant'
            record.enrollment_date = False
        return True
            
    def _create_enrollment_history(self, state, note=''):
        for record in self:
            self.env['student.enrollment.history'].create({
                'student_id': record.id,
                'course_id': record.course_id.id,
                'class_id': record.class_id.id,
                'academic_year_id': record.class_id.academic_year_id.id if record.class_id else False,
                'grade_level_id': record.class_id.grade_level_id.id if record.class_id else False,
                'state': state,
                'note': note,
            })

    def action_view_attendance(self):
        return {
            'name': 'Attendance Logs',
            'type': 'ir.actions.act_window',
            'res_model': 'student.attendance',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id, 'default_course_id': self.course_id.id},
        }

    def action_view_grades(self):
        return {
            'name': 'Grade Transcripts',
            'type': 'ir.actions.act_window',
            'res_model': 'student.grade',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_assignments(self):
        return {
            'name': 'Assignments',
            'type': 'ir.actions.act_window',
            'res_model': 'teacher.assignment',
            'view_mode': 'list,form',
            'domain': [('class_id', '=', self.class_id.id)],
            'context': {'default_class_id': self.class_id.id},
        }
        
    def action_view_resources(self):
        return {
            'name': 'Learning Resources',
            'type': 'ir.actions.act_window',
            'res_model': 'student.learning.resource',
            'view_mode': 'list,form',
            'domain': ['|', ('course_id', '=', self.course_id.id), ('subject_id', 'in', self.class_id.subject_ids.ids)],
        }
        
    def action_view_invoices(self):
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id, 'default_move_type': 'out_invoice'},
        }


class StudentClass(models.Model):
    _name = 'student.class'
    _description = 'Class / Section'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Class Name", required=True, tracking=True)
    code = fields.Char(string="Code / Term")
    academic_year = fields.Char(string="Academic Year (Legacy)")
    
    # New Academic Structure Relationships
    academic_year_id = fields.Many2one('student.academic.year', string="Academic Year", tracking=True)
    term_id = fields.Many2one('student.term', string="Academic Term", domain="[('academic_year_id', '=', academic_year_id)]")
    grade_level_id = fields.Many2one('student.grade.level', string="Grade Level")
    
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    capacity = fields.Integer(string="Capacity")

    # Relationships merged from academic.py canonical version
    student_ids = fields.One2many('student.student', 'class_id', string="Students")
    subject_ids = fields.Many2many('student.subject', string="Subjects")
    schedule_ids = fields.One2many('student.class.schedule', 'class_id', string="Weekly Schedule")


class StudentClassSchedule(models.Model):
    _name = 'student.class.schedule'
    _description = 'Class Weekly Schedule'
    _order = 'start_time'
    
    class_id = fields.Many2one('student.class', string="Class", ondelete='cascade')
    classroom = fields.Char(string="Classroom")
    subject_id = fields.Many2one('student.course', string="Subject", required=True)
    teacher_id = fields.Many2one('student.teacher', string="Faculty")
    
    day = fields.Selection([
        ('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday')
    ], string="Day", required=True)
    
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")




class TeacherSalary(models.Model):
    _name = 'teacher.salary'
    _description = 'Teacher Salary Management'

    # CORRECTED LINE BELOW: Pointing relation directly to your custom model 'student.teacher'
    teacher_id = fields.Many2one('student.teacher', string="Teacher", required=True)
    date = fields.Date(string="Payment Date", default=fields.Date.today)
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'),
        ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="Salary Month", required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(string="Amount Paid", required=True, currency_field='currency_id')
    notes = fields.Text(string="Internal Notes")
    state = fields.Selection([('draft', 'Draft'), ('paid', 'Paid')], default='draft', string="Status")

    def action_pay(self):
        for record in self:
            record.state = 'paid'


class StudentSubject(models.Model):
    _name = 'student.subject'
    _description = 'Academic Subject'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Subject Name", required=True, tracking=True)
    code = fields.Char(string="Subject Code", tracking=True)
    description = fields.Text(string="Description")
    # teacher_id merged from academic.py canonical version
    teacher_id = fields.Many2one('student.teacher', string="Lead Teacher", tracking=True)
    resource_ids = fields.One2many('student.learning.resource', 'subject_id', string="Learning Resources")


class StudentTeacher(models.Model):
    _name = 'student.teacher'
    _description = 'Teacher Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Teacher Name", required=True, tracking=True)
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    email = fields.Char(string="Email", tracking=True)
    phone = fields.Char(string="Phone")
    specialization = fields.Char(string="Specialization")
    user_id = fields.Many2one('res.users', string="Related User")
    
    resume_file = fields.Binary(string="Resume File")
    resume_filename = fields.Char(string="Resume Filename")
    id_number = fields.Char(string="ID Number")
    bank_account = fields.Char(string="Bank Account")
    emergency_contact = fields.Char(string="Emergency Contact")
    address = fields.Text(string="Address")

    # Teacher Responsibilities & Academics
    allocation_ids = fields.One2many('student.teacher.assignment', 'teacher_id', string="Subject Allocations")
    schedule_ids = fields.One2many('student.class.schedule', 'teacher_id', string="Timetable")
    assignment_ids = fields.One2many('teacher.assignment', 'teacher_id', string="Class Assignments Given")
    attendance_ids = fields.One2many('student.attendance', 'teacher_id', string="Attendance Taken")

    def action_create_user(self):
        for record in self:
            if record.user_id:
                continue
            group_portal = self.env.ref('base.group_portal', raise_if_not_found=False)
            group_teacher = self.env.ref('student_management.group_teacher', raise_if_not_found=False)
            user = self.env['res.users'].create({
                'name': record.name,
                'login': record.email or f"{record.name.lower().replace(' ', '.')}@teacher.local",
                'groups_id': [(6, 0, [g.id for g in (group_portal, group_teacher) if g])]
            })
            record.user_id = user.id
            if record.email:
                user.partner_id.email = record.email
                user.with_context(create_user=True).action_reset_password()

class StudentTeacherAssignment(models.Model):
    _name = 'student.teacher.assignment'
    _description = 'Teacher Allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    teacher_id = fields.Many2one('student.teacher', string="Teacher", required=True, tracking=True)
    subject_id = fields.Many2one('student.subject', string="Subject", required=True, tracking=True)
    class_id = fields.Many2one('student.class', string="Class", required=True, tracking=True)
    semester = fields.Selection([
        ('semester_1', 'Semester 1'),
        ('semester_2', 'Semester 2'),
    ], string="Semester", tracking=True)
    academic_year = fields.Char(string="Academic Year", tracking=True)
    display_name = fields.Char(string="Allocation", compute='_compute_display_name', store=True)

    @api.depends('teacher_id', 'subject_id', 'class_id')
    def _compute_display_name(self):
        for record in self:
            if record.teacher_id and record.subject_id and record.class_id:
                record.display_name = (
                    f"{record.teacher_id.name} — {record.subject_id.name} "
                    f"({record.class_id.name})"
                )
            else:
                record.display_name = "New Allocation"