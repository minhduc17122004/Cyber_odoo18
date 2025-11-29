# -*- coding: utf-8 -*-
{
    'name': "Cyber Topup",
    'summary': """Quản lý giao dịch nạp tiền tài khoản""",
    'description': """Lưu trữ và quản lý các giao dịch nạp tiền của tài khoản khách hàng.""",
    'author': "MINH QUAN",
    'category': 'Cyber',
    'version': '1.0',
    'depends': [
        'base',          
        'cyber_customers',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cyber_topup_views.xml',
    ],
    'installable': True,
    'application': True,
}
