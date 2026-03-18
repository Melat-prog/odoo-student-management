{
    'name': 'Student Management',
    'version': '1.0',
    'summary': 'Manage students',
    'author': 'Your Name',
    'category': 'Education',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/student_views.xml',
        'views/course_views.xml',
        'views/teacher_views.xml',
        'views/attendance_views.xml',
    ],
    'installable': True,
    'application': True,
}