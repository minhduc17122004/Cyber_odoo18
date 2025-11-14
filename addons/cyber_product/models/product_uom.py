from odoo import models, fields

class CyberUOM(models.Model):
    _inherit = 'uom.uom'

    uom_type = fields.Selection([
        ('good', 'Hàng hóa'),
        ('component', 'Linh kiện'),
        ('service', 'Máy dịch vụ')
    ], string="Loại đơn vị")
