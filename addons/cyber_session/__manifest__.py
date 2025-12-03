# -*- coding: utf-8 -*-
{
    'name': "Cyber Session",
    'version': '1.0',
    'summary': 'Quản lý phiên chơi và đơn hàng trong phiên',
    'category': 'Cyber',
    'author': 'Minh Duc',
    'depends': ['base', 'mail', 'product', 'cyber_customers', 'cyber_product'],
    'data': [
        'security/ir.model.access.csv',
        'views/cyber_session_views.xml',
        'views/cyber_sale_order_in_session_views.xml',
        'views/menus.xml',
        'data/cron_close_sessions.xml',
    ],
    'installable': True,
    'application': True,
}
