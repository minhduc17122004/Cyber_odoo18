from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CyberProductCategory(models.Model):
    _inherit = 'product.category'

    category_type = fields.Selection([
        ('service', 'Service'),
        ('good', 'Good'),
        ('component', 'Component')
    ], string="Loại category")
    
    price_list = fields.Float(string="Giá dịch vụ (VNĐ/giờ)")
    @api.onchange('category_type')
    def _onchange_category_type(self):
        if self.category_type != 'service':
            self.price_list = 0

    @api.constrains('category_type', 'price_list')
    def _check_price_list(self):
        for rec in self:
            if rec.category_type != 'service' and rec.price_list:
                raise ValidationError("Chỉ category dạng 'Service' mới được nhập giá dịch vụ.")
