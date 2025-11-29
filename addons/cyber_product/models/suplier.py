from odoo import models, fields

class CyberSupplier(models.Model):
    _inherit = 'res.partner'

    is_supplier_cyber = fields.Boolean(string="Là supplier Cyber")
    supplier_type = fields.Selection([
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện'),
        ('service', 'Máy dịch vụ')
    ], string="Loại supplier")
