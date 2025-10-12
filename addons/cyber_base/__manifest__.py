{
    'name': 'CyberCore Base',
    'version': '1.0.0',
    'summary': 'Module nền tảng cho hệ thống CyberCore ERP',
    'sequence': 1,
    'category': 'CyberCore',
    'author': 'CyberCore Team',
    'website': 'https://github.com/minhduc17122004/ERP',
    'depends': ['base'],
    'data': [
        'security/cyber_groups.xml',
        'security/ir.model.access.csv',
        'data/cyber_menus.xml',
        'views/cyber_base_views.xml',
    ],
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
}