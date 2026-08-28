from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website


class AmherstSchoolWebsite(http.Controller):

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def index(self, **kw):
        courses = request.env['student.course'].sudo().search([], limit=6)
        teachers = request.env['student.teacher'].sudo().search([], limit=4)
        return request.render('student_management.homepage_full_institutional', {
            'courses': courses,
            'teachers': teachers,
            'total_students': request.env['student.student'].sudo().search_count([]),
            'total_courses': request.env['student.course'].sudo().search_count([]),
            'total_teachers': request.env['student.teacher'].sudo().search_count([]),
        })

    @http.route('/about', type='http', auth='public', website=True)
    def about_us(self, **kw):
        teachers = request.env['student.teacher'].sudo().search([], limit=6)
        return request.render('student_management.about_us_page', {
            'teachers': teachers,
        })

    @http.route('/academics', type='http', auth='public', website=True)
    def academics(self, **kw):
        return request.render('student_management.academics_page', {})

    @http.route('/courses', type='http', auth='public', website=True)
    def courses(self, **kw):
        courses = request.env['student.course'].sudo().search([])
        return request.render('student_management.courses_page', {'courses': courses})

    @http.route('/research', type='http', auth='public', website=True)
    def research(self, **kw):
        return request.render('student_management.research_page', {})

    @http.route('/campus-life', type='http', auth='public', website=True)
    def campus_life(self, **kw):
        activities = request.env['campus.life.activity'].sudo().search([('is_published', '=', True)])
        categories = [
            ('clubs', 'Student Clubs'),
            ('athletics', 'Athletics'),
            ('arts', 'Arts & Culture'),
            ('housing', 'Housing'),
        ]
        return request.render('student_management.campus_life_page', {
            'activities': activities,
            'categories': categories,
        })

    @http.route('/campus-life/<int:activity_id>', type='http', auth='public', website=True)
    def campus_life_detail(self, activity_id, **kw):
        activity = request.env['campus.life.activity'].sudo().browse(activity_id)
        if not activity.exists() or not activity.is_published:
            return request.not_found()
        return request.render('student_management.campus_life_detail_page', {
            'activity': activity,
        })

    @http.route('/contact', type='http', auth='public', website=True)
    def contact(self, **kw):
        return request.render('student_management.contact_page', {})

    @http.route('/contact/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def contact_submit(self, **post):
        name = post.get('name', '').strip()
        phone = post.get('phone', '').strip()
        email = post.get('email', '').strip()
        subject = post.get('subject', '').strip()
        question = post.get('question', '').strip()

        # Create a mail.mail record as a standard inquiry failsafe log
        try:
            request.env['mail.mail'].sudo().create({
                'subject': f"Contact Inquiry: {subject or 'General Inquiry'}",
                'email_from': email,
                'email_to': 'info@nextgen.edu',
                'body_html': f"""
                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>Phone:</strong> {phone}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Subject:</strong> {subject}</p>
                    <p><strong>Question:</strong> {question}</p>
                """,
            })
        except Exception:
            pass

        return request.render('student_management.contact_success', {
            'name': name,
        })


    @http.route('/school/programs', type='http', auth='public', website=True)
    def school_programs(self, **kw):
        courses = request.env['student.course'].sudo().search([])
        return request.render('student_management.school_programs', {
            'courses': courses,
        })

    @http.route('/school/admissions', type='http', auth='public', website=True)
    def school_admissions(self, **kw):
        classes = request.env['student.class'].sudo().search([])
        return request.render('student_management.school_admissions_form', {
            'classes': classes,
        })

    @http.route('/school/admissions/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def school_admissions_submit(self, **post):
        first_name = post.get('first_name', '').strip()
        last_name = post.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip() or 'Anonymous Applicant'
        class_id = post.get('class_id')

        request.env['admission.application'].sudo().create({
            'name': full_name,
            'email': post.get('email', '').strip(),
            'phone': post.get('phone', '').strip(),
            'applied_class_id': int(class_id) if class_id and class_id.isdigit() else False,
            'notes': f"Previous School: {post.get('previous_school', '')}" if post.get('previous_school') else False,
        })
        return request.render('student_management.school_admissions_success', {})


class WebsiteInherit(Website):

    @http.route('/contactus', type='http', auth='public', website=True, sitemap=False)
    def contactus(self, **kwargs):
        return request.redirect('/contact', code=301)
