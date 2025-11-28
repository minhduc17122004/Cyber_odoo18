# -*- coding: utf-8 -*-
{
    'name': "Cyber Invoice",
    'summary': """Quản lý hóa đơn thanh toán""",
    'description': """Lưu trữ và quản lý các hóa đơn thanh toán của khách hàng, liên kết với giao dịch và phiên""",
    'author': "MINH QUAN",
    'category': 'Cyber',
    'version': '1.0',
    'depends': [
        'base',
        'account',
        'cyber_customers',
        'cyber_topup',
        'cyber_session',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cyber_invoice_views.xml',
    ],
    'installable': True,
    'application': True,
}
