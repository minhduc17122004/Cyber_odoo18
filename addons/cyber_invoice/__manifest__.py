# -*- coding: utf-8 -*-
{
    'name': "Cyber Invoice",
    'summary': """Quản lý hóa đơn thanh toán""",
    'description': """Lưu trữ và quản lý các hóa đơn thanh toán của khách hàng, liên kết với giao dịch và thông tin khách hàng.""",
    'author': "MINH QUAN",
    'category': 'Cyber',
    'version': '1.0',
    'depends': [
        'base',
        'cyber_customer',
        'cyber_transaction',
        'cyber_session',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cyber_invoice_views.xml',
    ],
    'installable': True,
    'application': True,
}
