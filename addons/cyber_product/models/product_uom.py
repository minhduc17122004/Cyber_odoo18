from odoo import models, fields

class CyberUOM(models.Model):
    _name = 'cyber.uom'
    _description = 'Đơn vị tính'

    name = fields.Char(string="Tên đơn vị tính", required=True)
    uom_type = fields.Selection([
        ('service', 'Máy tính'),
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện')
    ], string="Loại áp dụng", required=True)
    description = fields.Text(string="Mô tả thêm")
