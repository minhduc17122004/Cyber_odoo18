from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CyberStockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            if picking.state != 'done':
                continue
            for move in picking.move_ids:  # move_lines không có, dùng move_ids
                qty = move.product_uom_qty
                if not move.cyber_product_id:
                    continue  # bỏ qua nếu chưa liên kết Cyber Product
                if picking.picking_type_id.code == 'incoming':
                    move.cyber_product_id.quantity += qty
                elif picking.picking_type_id.code == 'outgoing':
                    move.cyber_product_id.quantity -= qty
        return res
