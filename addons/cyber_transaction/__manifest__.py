# -*- coding: utf-8 -*-
{
    'name': "Cyber Transaction",
    'summary': """Quản lý giao dịch tài khoản trong quán net""",
    'description': """Lưu trữ và quản lý các giao dịch nạp tiền, chi tiêu của tài khoản khách hàng.""",
    'author': "Minh Quân",
    'category': 'Cyber',
    'version': '0.1',
    'depends': [
        'base',         
        'cyber_account', 
        'cyber_customer',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cyber_transaction_views.xml',
    ],
    'installable': True,
    'application': True,
}
