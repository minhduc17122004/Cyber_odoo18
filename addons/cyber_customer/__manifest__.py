{
    "name": "CyberCore Customer",
    "version": "1.0",
    "depends": ["base", "contacts", "cyber_base"],
    "author": "CyberCore Team",
    "summary": "Quản lý khách hàng và thành viên VIP của hệ thống CyberCore",
    "data": [
        "security/cyber_customer_groups.xml",
        "security/ir.model.access.csv",
        "views/cyber_customer_menu.xml",
        "views/cyber_customer_view.xml",
    ],
    "installable": True,
    "application": False,
}