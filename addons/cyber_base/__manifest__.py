# cyber_base/__manifest__.py
{
    "name": "CyberCore Base",
    "version": "1.0",
    "depends": ["base", "product", "uom"],
    "author": "CyberCore Team",
    "summary": "Module cơ sở cho hệ thống CyberCore ERP",
    "data": [
        "security/cyber_groups.xml",
        "security/ir.model.access.csv",
        "data/product_category.xml",
        "views/cyber_menus.xml",
        "views/product_views.xml",
    ],
    "installable": True,
    "application": True,
}