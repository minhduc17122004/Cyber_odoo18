from odoo import models, fields, api

class CyberMaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'  

    cyber_machine_id = fields.Many2one(
        'product.product',
        string='Machine',
        domain=[('is_machine', '=', True)],
        help='Máy/Thiết bị liên quan trong cyber cafe'
    )
