{
    'name': 'Cyber Product',
    'version': '1.0',
    'author': 'CONG SON',
    'category': 'Cyber',
    'summary': 'Quản lý sản phẩm (Máy & Dịch vụ) cho quán game',
    'depends': ['base','product','uom','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/categories_views.xml',
        'views/uom_views.xml',
        'views/supplier_views.xml',
        'views/stock_moveP_views.xml',
        'views/stock_quant_views.xml',
    ],
    'installable': True,
    'application': True,
}
