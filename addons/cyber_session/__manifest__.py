{
    'name': 'Cyber Session Management',
    'version': '1.0',
    'summary': 'Quản lý phiên chơi trong phòng net (Cyber Game)',
    'category': 'Cyber',
    'author': 'Duc Tran',
    'depends': ['base', 'mail', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/cyber_session_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
