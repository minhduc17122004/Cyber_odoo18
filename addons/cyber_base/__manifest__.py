# -*- coding: utf-8 -*-
{
    "name": "CyberCore Base",
    "version": "1.0.0",
    "summary": "Nền tảng CyberCore ERP: menu, quyền, danh mục, UoM, mở rộng Product",
    "author": "CyberCore Team",
    "license": "LGPL-3",
    "category": "CyberCore",
    "depends": ["base", "product", "uom"],
    "data": [
        "security/cyber_groups.xml",
        "security/ir.model.access.csv",
        "data/product_category.xml",
        "data/uom_data.xml",
        "views/cyber_menus.xml",
        "views/product_views.xml",
    ],
    "installable": True,
    "application": True,
}