from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class StudentPortal(CustomerPortal):

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        user = request.env.user
        if user.has_group('student_management.group_teacher'):
            return request.redirect('/my/teacher')
        if user.has_group('student_management.group_parent'):
            return request.redirect('/my/parent')
        return super(StudentPortal, self).home(**kw)

    @http.route(['/my/teacher'], type='http', auth="user", website=True)
    def portal_teacher_dashboard(self, **kw):
        user = request.env.user
        if not user.has_group('student_management.group_teacher'):
            return request.redirect('/my')
        
        teacher = request.env['student.teacher'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not teacher:
            return request.render("student_management.portal_student_not_found", {})
            
        classes = request.env['student.class'].sudo().search([])
        # Retrieve assignments specific to teacher
        assignments = request.env['teacher.assignment'].sudo().search([('teacher_id', '=', teacher.id)])
        
        values = {
            'page_name': 'teacher_dashboard',
            'teacher': teacher,
            'classes': classes,
            'assignments': assignments,
            'default_url': '/my/teacher',
        }
        return request.render("student_management.portal_teacher_dashboard", values)

    @http.route(['/my/parent'], type='http', auth="user", website=True)
    def portal_parent_dashboard(self, **kw):
        user = request.env.user
        if not user.has_group('student_management.group_parent'):
            return request.redirect('/my')
            
        parent = request.env['student.parent'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not parent:
            return request.render("student_management.portal_student_not_found", {})
            
        children = parent.student_ids
        
        values = {
            'page_name': 'parent_dashboard',
            'parent': parent,
            'children': children,
            'default_url': '/my/parent',
        }
        return request.render("student_management.portal_parent_dashboard", values)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        # Determine the related student(s) based on user type
        students = self._get_students()
        student_ids = students.ids if students else []

        if 'grade_count' in counters:
            values['grade_count'] = request.env['student.grade'].sudo().search_count(
                [('student_id', 'in', student_ids)]
            ) if student_ids else 0
        if 'attendance_count' in counters:
            values['attendance_count'] = request.env['student.attendance'].sudo().search_count(
                [('student_id', 'in', student_ids)]
            ) if student_ids else 0
        if 'assignment_count' in counters:
            values['assignment_count'] = request.env['teacher.assignment'].sudo().search_count([]) if student_ids else 0
        if 'resource_count' in counters:
            values['resource_count'] = request.env['student.learning.resource'].sudo().search_count([]) if student_ids else 0

        return values

    def _get_students(self):
        user = request.env.user
        if user.has_group('student_management.group_student'):
            return request.env['student.student'].sudo().search([('user_id', '=', user.id)])
        elif user.has_group('student_management.group_parent'):
            return request.env['student.student'].sudo().search([('parent_ids.user_id', '=', user.id)])
        return request.env['student.student'].sudo().browse()

    @http.route(['/my/grades', '/my/grades/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_grades(self, page=1, student_id=None, **kw):
        students = self._get_students()

        if not students:
            return request.render("student_management.portal_student_not_found", {})

        current_student = students.filtered(lambda s: str(s.id) == student_id) if student_id else students[0]

        domain = [('student_id', '=', current_student.id)]
        GradeSudo = request.env['student.grade'].sudo()
        grade_count = GradeSudo.search_count(domain)
        pager = portal_pager(
            url="/my/grades",
            url_args={'student_id': current_student.id},
            total=grade_count,
            page=page,
            step=20
        )
        grades = GradeSudo.search(domain, limit=20, offset=pager['offset'])

        values = {
            'grades': grades,
            'page_name': 'grades',
            'pager': pager,
            'students': students,
            'current_student': current_student,
            'default_url': '/my/grades',
        }
        return request.render("student_management.portal_my_grades", values)

    @http.route(['/my/attendance', '/my/attendance/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_attendance(self, page=1, student_id=None, **kw):
        students = self._get_students()

        if not students:
            return request.render("student_management.portal_student_not_found", {})

        current_student = students.filtered(lambda s: str(s.id) == student_id) if student_id else students[0]

        domain = [('student_id', '=', current_student.id)]
        AttendanceSudo = request.env['student.attendance'].sudo()
        attendance_count = AttendanceSudo.search_count(domain)
        pager = portal_pager(
            url="/my/attendance",
            url_args={'student_id': current_student.id},
            total=attendance_count,
            page=page,
            step=20
        )
        attendances = AttendanceSudo.search(domain, order="date desc", limit=20, offset=pager['offset'])

        values = {
            'attendances': attendances,
            'page_name': 'attendance',
            'pager': pager,
            'students': students,
            'current_student': current_student,
            'default_url': '/my/attendance',
        }
        return request.render("student_management.portal_my_attendance", values)

    @http.route(['/my/assignments', '/my/assignments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_assignments(self, page=1, student_id=None, **kw):
        students = self._get_students()
        if not students:
            return request.render("student_management.portal_student_not_found", {})

        current_student = students.filtered(lambda s: str(s.id) == student_id) if student_id else students[0]

        domain = []
        AssignmentSudo = request.env['teacher.assignment'].sudo()
        assignment_count = AssignmentSudo.search_count(domain)
        pager = portal_pager(url="/my/assignments", url_args={'student_id': current_student.id}, total=assignment_count, page=page, step=20)
        assignments = AssignmentSudo.search(domain, order="due_date desc", limit=20, offset=pager['offset'])

        values = {
            'assignments': assignments,
            'page_name': 'assignments',
            'pager': pager,
            'students': students,
            'current_student': current_student,
            'default_url': '/my/assignments',
        }
        return request.render("student_management.portal_my_assignments", values)

    @http.route(['/my/resources', '/my/resources/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_resources(self, page=1, student_id=None, **kw):
        students = self._get_students()
        if not students:
            return request.render("student_management.portal_student_not_found", {})

        current_student = students.filtered(lambda s: str(s.id) == student_id) if student_id else students[0]

        domain = []
        ResourceSudo = request.env['student.learning.resource'].sudo()
        resource_count = ResourceSudo.search_count(domain)
        pager = portal_pager(url="/my/resources", url_args={'student_id': current_student.id}, total=resource_count, page=page, step=20)
        resources = ResourceSudo.search(domain, order="sequence", limit=20, offset=pager['offset'])

        values = {
            'resources': resources,
            'page_name': 'resources',
            'pager': pager,
            'students': students,
            'current_student': current_student,
            'default_url': '/my/resources',
        }
        return request.render("student_management.portal_my_resources", values)
