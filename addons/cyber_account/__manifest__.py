# -*- coding: utf-8 -*-
{
    'name': "Cyber Account",
    'summary': """Quản lý tài khoản khách hàng quán nét""",
    'description': """Quản lý thông tin khách hàng""",
    'author': "Minh Quân",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'product', 'cyber_customer', 'customer_segment'
    ],
    'data': ['security/ir.model.access.csv',
    'views/cyber_account_views.xml',
    'views/cyber_customer_inherit_view.xml',
    ],
    # 'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
    
}

