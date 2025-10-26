# -*- coding: utf-8 -*-
{
    'name': "Cyber Account",
    'summary': """Quản lý tài khoản khách hàng quán nét""",
    'description': """Quản lý thông tin khách hàng""",
    'author': "Minh Quân",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'product', 'customer_segment','cyber_customer'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cyber_account_views.xml',
        'views/cyber_customer_inherit_views.xml',
        ],
    # 'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
    
}

