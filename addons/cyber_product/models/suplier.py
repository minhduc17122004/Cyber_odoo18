from odoo import models, fields, api

class Supplier(models.Model):
    _inherit = "res.partner"

    is_supplier_cyber = fields.Boolean(string="Là nhà cung cấp cho Cyber", default=False)
    supplier_type = fields.Selection([
        ('service', 'Máy tính'),
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện')
    ], string="Loại áp dụng")
    supplier_note = fields.Text(string="Ghi chú")

    @api.model
    def create(self, vals):
        # Nếu không có cờ is_supplier_cyber, thì tự động bật nếu có supplier_type
        if vals.get('supplier_type') and not vals.get('is_supplier_cyber'):
            vals['is_supplier_cyber'] = True

        # Nếu context có default_supplier_type mà form không truyền, thì gán vào
        ctx = self.env.context
        if ctx.get('default_supplier_type') and not vals.get('supplier_type'):
            vals['supplier_type'] = ctx['default_supplier_type']
            vals['is_supplier_cyber'] = True

        partner = super().create(vals)
        return partner
