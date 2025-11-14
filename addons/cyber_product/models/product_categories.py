from odoo import models, fields

class CyberProductCategory(models.Model):
    _inherit = 'product.category'

    category_type = fields.Selection([
        ('service', 'Service'),
        ('good', 'Good'),
        ('component', 'Component')
    ], string="Loại category")
    
    price_per_hours = fields.Float(string="Giá dịch vụ (VNĐ/giờ)")
