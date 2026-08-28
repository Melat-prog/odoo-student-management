{
    'name': 'Student Management',
    'version': '1.0.1',
    'summary': 'Manage students, faculty, and academic operations',
    'author': 'Melat',
    'category': 'Education',
    'depends': ['base', 'mail', 'website', 'account', 'portal', 'auth_signup'],
    'data': [
        # Core Security Groups
        'security/student_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence_data.xml',
        
        # Reports 
        'report/student_report_actions.xml',
        'report/student_card_templates.xml',
        
        # Centralized Views
        'views/student_views.xml',
        'views/course_views.xml',
        'views/assignment_views.xml',
        'views/submission_views.xml',
        'views/academic_views.xml',
        'views/teacher_views.xml',
        'views/attendance_wizard_views.xml',
        'views/attendance_views.xml',
        'views/admission_views.xml',
        'views/grade_views.xml',
        'views/notice_views.xml',
        'views/ai_assistant_views.xml',
        'views/ai_learning_assistant_wizard_views.xml',
        'views/exam_views.xml',
        'views/parent_views.xml',
        'views/portal_templates.xml',
        'views/website_templates.xml',
        'views/dashboard_views.xml',
        'views/campus_life_views.xml',
        'data/website_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'student_management/static/src/css/student_management.css',
            'student_management/static/src/scss/ai_wizard.scss',
        ],
        'web.assets_frontend': [
            'student_management/static/src/css/style.css',
            'student_management/static/src/js/animations.js',
        ],
    },
    'installable': True,
    'application': True,
}