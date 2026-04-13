{
    'name': 'Student Management',
    'version': '1.0',
    'summary': 'Manage students',
    'author': 'Your Name',
    'category': 'Education',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/student_views.xml',
        'views/course_views.xml',
        'views/teacher_views.xml',
        'views/attendance_views.xml',
        'views/academic_views.xml',
        'views/admission_views.xml',
        'views/assignment_views.xml',
        'views/submission_views.xml',
        
    ],
    'installable': True,
    'application': True,
}