{
    'name': 'Cyber Session',
    'version': '1.0.0',
    'category': 'Cyber',
    'summary': 'Manage prepaid sessions, accounts, and transactions for cyber shops',
    'author': 'Minh Đức',
    'depends': ['base', 'mail', 'product', 'cyber_account'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/cyber_account_views.xml',
        # 'views/cyber_transaction_views.xml',
        'views/cyber_session_views.xml',
        'views/menu.xml',
        'data/cron_close_sessions.xml',
    ],
    'installable': True,
    'application': True,
}