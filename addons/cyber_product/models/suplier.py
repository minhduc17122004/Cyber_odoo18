from odoo import models, fields

class Supplier(models.Model):
    _inherit = "res.partner"

    is_supplier_cyber = fields.Boolean(string="Là nhà cung cấp cho Cyber", default=False)
    supplier_type = fields.Selection([
        ('service', 'Máy tính'),
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện')
    ], string="Loại áp dụng", required=True)
    supplier_note = fields.Text(string="Ghi chú")
