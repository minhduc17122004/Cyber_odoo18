# -*- coding: utf-8 -*-
{
    'name': "Cyber Invoice",
    'summary': """Quản lý hóa đơn thanh toán""",
    'description': """Lưu trữ và quản lý các hóa đơn thanh toán của khách hàng, liên kết với giao dịch và phiên""",
    'author': "MINH QUAN",
    'category': 'Cyber',
    'version': '1.0',
    'depends': [
        'base',
        'account',
        'cyber_customers',
        'cyber_topup',
        'cyber_session',
    ],
    'data': [
        'security/ir.model.access.csv',
        # NOTE: Đã chuyển nội dung từ cyber_invoice_views.xml vào cyber_invoice_customer.xml
        # NOTE: Đã xóa cyber_invoice_supplier.xml
        'views/cyber_invoice_customer.xml',  # File root chính
        'views/cyber_invoice_report.xml',
    ],
    'installable': True,
    'application': True,
}
