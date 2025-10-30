from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = "product.category"

    category_type = fields.Selection([
        ('service', 'Máy vi tính'),
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện')
    ], string="Loại danh mục", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('default_category_type'):
            res['category_type'] = self._context['default_category_type']
        return res