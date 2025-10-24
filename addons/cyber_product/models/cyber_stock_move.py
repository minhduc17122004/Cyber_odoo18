from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CyberStockMove(models.Model):
    _inherit = "stock.move"

    # Liên kết với cyber.product dựa trên product.template
    cyber_product_id = fields.Many2one(
        'cyber.product',
        string="Sản phẩm Cyber",
        compute='_compute_cyber_product',
        store=True
    )

    # Các trường bổ sung lấy từ cyber.product
    is_machine = fields.Boolean(related='cyber_product_id.is_machine', string="Là máy", store=True)
    is_good = fields.Boolean(related='cyber_product_id.is_good', string="Là hàng hóa", store=True)
    is_component = fields.Boolean(related='cyber_product_id.is_component', string="Là linh kiện", store=True)

    # Compute cyber_product_id dựa trên product.template
    @api.depends('product_id')
    def _compute_cyber_product(self):
        for move in self:
            cyber = self.env['cyber.product'].search(
                [('product_tmpl_id', '=', move.product_id.product_tmpl_id.id)], limit=1)
            move.cyber_product_id = cyber.id if cyber else False

    # Override onchange để tránh lỗi partner_ref
    @api.onchange('product_id')
    def _onchange_product_id_override(self):
        for move in self:
            product = move.product_id
            # Nếu có nhà cung cấp, có thể lấy tên theo seller_ids
            if product.seller_ids:
                move.name = product.seller_ids[0].product_name or product.name
            else:
                move.name = product.name

    # Constraint kiểm tra tồn kho khi xuất kho
    @api.constrains('product_uom_qty', 'state')
    def _check_quantity(self):
        for move in self:
            if move.state == 'done' and move.picking_id.picking_type_id.code == 'outgoing':
                if move.product_id.sudo().quantity < move.product_uom_qty:
                    raise ValidationError(
                        f"Sản phẩm {move.product_id.name} không đủ tồn kho để xuất!"
                    )
