from odoo import models, fields, api

class CyberMaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'  

    cyber_machine_id = fields.Many2one(
        'product.template',
        string='Máy',
        domain=[('is_machine', '=', True)],
        help='Máy/Thiết bị liên quan trong cyber cafe'
    )

    cyber_component_id = fields.Many2many(
        'product.template',
        string='Linh kiện',
        domain=[('is_component', '=', True)],
        help='Linh kiện liên quan trong cyber cafe'
    )

    expense_ids = fields.One2many(
        'cyber.expense',
        'maintenance_id',
        string="Chi phí liên quan"
    )

    @api.depends('stage_id')
    def _update_machine_status_based_on_stage(self):
        for rec in self:
            if rec.cyber_machine_id:
                if rec.stage_id and rec.stage_id.done:
                    rec.cyber_machine_id.write({'machine_status': 'active'})
                else:
                    rec.cyber_machine_id.write({'machine_status': 'maintenance'})

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.cyber_machine_id:
            record.cyber_machine_id.write({'machine_status': 'maintenance'})
        return record
    
    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals:
            self._update_machine_status_based_on_stage()
        return res
