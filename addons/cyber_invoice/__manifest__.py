# -*- coding: utf-8 -*-
{
    'name': "Cyber Invoice",
    'summary': """Quản lý hóa đơn thanh toán trong quán net""",
    'description': """Lưu trữ và quản lý các hóa đơn thanh toán của khách hàng, liên kết với giao dịch và thông tin khách hàng.""",
    'author': "Minh Quân",
    'category': 'Cyber Management',
    'version': '0.1',
    'depends': [
        'base',
        'cyber_customer',
        'cyber_transaction',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cyber_invoice_views.xml',
    ],
    'installable': True,
    'application': True,
}
