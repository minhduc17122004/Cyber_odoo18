from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = "product.category"

    category_type = fields.Selection([
        ('Service', 'Máy vi tính'),
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện')
    ], string="Loại danh mục", required=True, default='good')
