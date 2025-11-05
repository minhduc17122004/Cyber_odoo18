# -*- coding: utf-8 -*-
{
    'name': "Cyber Customer",
    'summary': "Quản lý khách hàng",
    'author': "HUU TOAN",
    'category': 'Cyber',
    'version': '1.0',
    'depends': ['base', 'customer_segment'],
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
    ],
    "application": True,
    "installable": True,
}

