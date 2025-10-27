# -*- coding: utf-8 -*-
{
    'name': "Cyber Customer",
    'summary': "Module for Cyber Customer",
    'author': "Toan Nguyen",
    'category': 'Cyber',
    'version': '1.0.0',
    'depends': ['base', 'customer_segment'],
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
    ],
    "application": True,
    "installable": True,
}

