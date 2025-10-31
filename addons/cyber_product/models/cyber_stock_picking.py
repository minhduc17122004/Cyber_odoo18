from odoo import models, api

class CyberStockPicking(models.Model):
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
                    move._update_stock_quant(qty)
                elif picking.picking_type_id.code == 'outgoing':
                    move._update_stock_quant(-qty)

        return res
