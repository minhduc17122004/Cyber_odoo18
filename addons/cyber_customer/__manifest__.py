{
    "name": "CyberCore Customer",
    "version": "1.0.0",
    "summary": "Quản lý khách hàng của hệ thống CyberCore ERP",
    "author": "CyberCore Team",
    "license": "LGPL-3",
    "depends": ["base", "contacts", "cyber_base"],
    "data": [
        "security/cyber_customer_groups.xml",
        "security/ir.model.access.csv",
        "views/cyber_customer_menu.xml",
        "views/cyber_customer_views.xml",
    ],
    "installable": True,
    "application": False,
}