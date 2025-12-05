from odoo import models, fields, api

class CyberPicking(models.Model):
    _inherit = 'stock.picking'

    is_cyber_picking = fields.Boolean(
        string="Cyber Picking",
        compute='_compute_is_cyber_picking',
        store=True
    )
    
    # Số lượng cyber moves trong picking
    cyber_move_count = fields.Integer(
        string="Số lượng Cyber Moves",
        compute='_compute_cyber_move_count'
    )
    @api.depends('move_ids_without_package.is_cyber_move')
    def _compute_is_cyber_picking(self):
        """Tự động đánh dấu picking là cyber nếu có ít nhất 1 cyber move"""
        for picking in self:
            picking.is_cyber_picking = any(
                move.is_cyber_move for move in picking.move_ids_without_package
            )

    @api.depends('move_ids_without_package.is_cyber_move')
    def _compute_cyber_move_count(self):
        """Đếm số lượng cyber moves"""
        for picking in self:
            picking.cyber_move_count = sum(
                1 for move in picking.move_ids_without_package
                if move.is_cyber_move
            )

    def action_view_cyber_moves(self):
        """Action button: xem các cyber moves"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cyber Moves',
            'res_model': 'stock.move',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('picking_id', '=', self.id), ('is_cyber_move', '=', True)],
        }

    @api.model
    def create(self, vals):
        # Nếu context có flag 'is_cyber_picking', tự động set True
        if self.env.context.get('is_cyber_picking'):
            vals['is_cyber_picking'] = True
        return super().create(vals)