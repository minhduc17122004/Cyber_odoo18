from odoo import fields, models, api
from odoo.exceptions import ValidationError

class CyberStockPicking(models.Model):
    _inherit = "stock.picking"

    from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()

        for picking in self:
                    if picking.state != 'done':
                        continue

                    for move in picking.move_ids:
                        if not move.cyber_product_id:
                            continue

                        qty = move.product_uom_qty
                        if picking.picking_type_id.code == 'incoming':
                            move._update_cyber_quant(qty)
                        elif picking.picking_type_id.code == 'outgoing':
                            move._update_cyber_quant(-qty)

        return res

    @api.model
    def create(self, vals):
        context = self.env.context
        if context.get('default_operation_type'):
            vals['operation_type'] = context['default_operation_type']
        return super().create(vals)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        picking_type_code = self._context.get('picking_type_code', 'incoming')
        picking_type = self.env['stock.picking.type'].search([('code', '=', picking_type_code)], limit=1)
        if picking_type:
            res['picking_type_id'] = picking_type.id
        return res
