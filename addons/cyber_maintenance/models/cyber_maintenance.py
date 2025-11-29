from odoo import models, fields, api

class CyberMaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'  

    cyber_machine_id = fields.Many2one(
        'product.product',
        string='Máy',
        domain=[('is_machine', '=', True)],
        help='Máy/Thiết bị liên quan trong cyber cafe'
    )

    expense_ids = fields.One2many(
        'cyber.expense',
        'maintenance_id',
        string="Chi phí liên quan"
    )
