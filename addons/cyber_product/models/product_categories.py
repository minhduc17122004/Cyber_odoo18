from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductCategory(models.Model):
    _inherit = "product.category"

    category_type = fields.Selection([
        ('service', 'Máy vi tính'),
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện')
    ], string="Loại danh mục", required=True)
    price_per_hours = fields.Float(string="Giá dịch vụ (VNĐ/giờ)")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('default_category_type'):
            res['category_type'] = self._context['default_category_type']
        return res

    price_per_hours_readonly = fields.Boolean(compute="_compute_price_per_hours_readonly")

    @api.depends('category_type')
    def _compute_price_per_hours_readonly(self):
        for rec in self:
            rec.price_per_hours_readonly = rec.category_type != 'service'
    #@api.constrains('price_per_hours', 'category_type')
    #def _check_price_per_hours_service(self):
    #    for rec in self:
    #        if rec.category_type != 'service' and rec.price_per_hours:
    #            raise ValidationError("Chỉ category loại service mới được nhập giá dịch vụ.")
    