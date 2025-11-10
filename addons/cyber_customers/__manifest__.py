# -*- coding: utf-8 -*-
{
    'name': "Cyber Customers",
    'summary': """Quản lý khách hàng, tài khoản, loại khách hàng quán game""",
    'description': """Quản lý thông tin khách hàng""",
    'author': "Toàn Nguyễn",
    'category': 'Cyber',
    'version': '0.1',
    'depends': ['base', 'product'],
    'data': [   'security/ir.model.access.csv',
                'views/customer_segments_views.xml',
                'views/cyber_account_views.xml',
                'views/cyber_customer_views.xml',
                'views/menus.xml'
    ],
    'installable': True,
    'application': True,
    
}

