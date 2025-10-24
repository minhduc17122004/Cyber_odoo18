{
    'name': 'Cyber Product Management',
    'version': '1.0',
    'author': 'CONG SON',
    'category': 'CyberGame',
    'summary': 'Quản lý sản phẩm (Máy & Dịch vụ) cho quán game',
    'depends': ['base','product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}
