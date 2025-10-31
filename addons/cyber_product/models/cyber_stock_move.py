from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CyberStockMove(models.Model):
    _inherit = "stock.move"

    cyber_product_id = fields.Many2one(
        'cyber.product',
        string="Sản phẩm Cyber",
        compute='_compute_cyber_product',
        store=True
    )
    is_cyber_move = fields.Boolean(string="Cyber Move", default=False)
    cyber_quant_id = fields.Many2one('cyber.stock.quant', string='Cyber Quant')

    is_machine = fields.Boolean(related='cyber_product_id.is_machine', store=True)
    is_good = fields.Boolean(related='cyber_product_id.is_good', store=True)
    is_component = fields.Boolean(related='cyber_product_id.is_component', store=True)

    @api.depends('product_id')
    def _compute_cyber_product(self):
        for move in self:
            cyber = self.env['cyber.product'].search([
                ('product_tmpl_id', '=', move.product_id.product_tmpl_id.id)
            ], limit=1)
            move.cyber_product_id = cyber.id if cyber else False

    @api.constrains('product_uom_qty', 'state')
    def _check_quantity(self):
        for move in self:
            if move.state == 'done' and move.picking_id.picking_type_id.code == 'outgoing':
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', move.product_id.id)
                ], limit=1)
                if quant and quant.quantity < move.product_uom_qty:
                    raise ValidationError(
                        f"Sản phẩm {move.product_id.display_name} không đủ tồn kho để xuất!"
                    )

    def _update_stock_quant(self, qty_change):
        """Cập nhật stock.quant và cyber_product.quantity"""
        for move in self:
            variant = move.product_id
            quant = self.env['stock.quant'].search([
                ('product_id', '=', variant.id)
            ], limit=1)
            if not quant:
                location = move.location_dest_id if qty_change > 0 else move.location_id
                quant = self.env['stock.quant'].create({
                    'product_id': variant.id,
                    'location_id': location.id,
                    'quantity': 0.0,
                    'in_date': fields.Datetime.now(),
                })
            quant.sudo().quantity += qty_change
            quant.sudo().write({'in_date': fields.Datetime.now()})

            # Cập nhật cyber_product
            if move.cyber_product_id:
                move.cyber_product_id.quantity += qty_change
                move.cyber_product_id.update_at = fields.Datetime.now()