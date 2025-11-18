from odoo import models, fields


class CyberUOMCategory(models.Model):
    _inherit = 'uom.category'
    
    cyber_category_type = fields.Selection([
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện'),
        ('service', 'Máy dịch vụ')
    ], string="Loại danh mục")


class CyberUOM(models.Model):
    _inherit = 'uom.uom'

    cyber_uom_type = fields.Selection([
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện'),
        ('service', 'Máy dịch vụ')
    ], string="Loại đơn vị")
