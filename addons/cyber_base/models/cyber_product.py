# -*- coding: utf-8 -*-
from odoo import models, fields

class CyberProductTemplate(models.Model):
    _inherit = "product.template"

    # Phân loại dùng chung
    is_machine = fields.Boolean(string="Máy chơi (Cyber)", default=False, help="Đánh dấu sản phẩm là máy/quầy chơi.")
    is_cyber_service = fields.Boolean(string="Dịch vụ Cyber", default=False, help="Đồ ăn/uống/khác bán kèm.")

    service_type = fields.Selection([
        ('food', 'Đồ ăn'),
        ('drink', 'Đồ uống'),
        ('other', 'Khác'),
    ], string="Loại dịch vụ")

    # Thuộc tính cho máy
    ip_address = fields.Char(string="IP máy")
    location = fields.Char(string="Vị trí/Khu vực")
    status = fields.Selection([
        ('available', 'Sẵn sàng'),
        ('playing', 'Đang chơi'),
        ('maintenance', 'Bảo trì'),
    ], string="Trạng thái máy", default='available')
    last_maintenance = fields.Date(string="Bảo trì lần cuối")