{
    'name': 'Cyber Account Management',
    'version': '1.0',
    'summary': 'Quản lý tài khoản khách hàng cho quán net',
    'sequence': 10,
    'description': """
Module quản lý tài khoản người dùng trong hệ thống quán net.
Bao gồm thông tin tài khoản, số dư, trạng thái, và lịch sử sử dụng cơ bản.
    """,
    'author': 'Quân Phan',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/cyber_account_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
