from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CyberSaleOrderInSession(models.Model):
    _name = 'cyber.sale_order_in_session'
    _description = 'Sale Order in Session'
    _order = 'id desc'

    # ========================
    # FIELDS
    # ========================
    session_id = fields.Many2one(
        'cyber.session',
        string='Session',
        ondelete='cascade',
        required=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain=[('is_good', '=', True)]
    )
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        digits=(16, 3)
    )
    price_unit = fields.Float(
        string='Unit Price (VND)',
        digits=(16, 0)
    )
    line_total = fields.Float(
        string='Line Total (VND)',
        compute='_compute_line_total',
        store=True,
        digits=(16, 0)
    )
    note = fields.Char(string='Ghi chú')
    order_state = fields.Selection(
        [
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('canceled', 'Canceled')
        ],
        string='Order Status',
        default='in_progress',
        required=True,
        tracking=True
    )

    # ========================
    # COMPUTE METHODS
    # ========================
    @api.depends('quantity', 'price_unit', 'order_state')
    def _compute_line_total(self):
        """Chỉ tính line_total khi order ở trạng thái 'done'"""
        for rec in self:
            rec.line_total = rec.quantity * rec.price_unit if rec.order_state == 'done' else 0

    # ========================
    # ONCHANGE METHODS
    # ========================
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Tự động điền giá bán khi chọn sản phẩm"""
        if self.product_id:
            self.price_unit = self.product_id.list_price

    # ========================
    # CRUD OVERRIDES
    # ========================
    @api.model
    def create(self, vals):
        """Khi tạo order mới: kiểm tra trạng thái session và trigger recompute"""
        # Kiểm tra session có được phép thêm order không
        if 'session_id' in vals:
            session = self.env['cyber.session'].browse(vals['session_id'])
            if session.session_state == 'closed':
                raise UserError(_("Không thể thêm order khi phiên đã đóng."))

        order = super(CyberSaleOrderInSession, self).create(vals)
        
        # Trigger session recompute để cập nhật các field computed
        order.session_id._compute_total_order()

        return order

    def write(self, vals):
        """Khi cập nhật order: kiểm tra canceled và trigger recompute"""
        # Không cho phép sửa order đã hủy (trừ field order_state)
        for rec in self:
            if rec.order_state == 'canceled' and any(key != 'order_state' for key in vals.keys()):
                raise UserError(_("Không thể sửa order đã hủy."))
        
        res = super(CyberSaleOrderInSession, self).write(vals)
        
        # Trigger recompute khi có thay đổi quantity, price_unit, hoặc order_state
        if any(key in vals for key in ['quantity', 'price_unit', 'order_state']):
            for rec in self:
                if rec.session_id.session_state == 'running':
                    rec.session_id._compute_total_order()

        return res

    def unlink(self):
        """Khi xóa order: trigger session recompute"""
        # Lưu lại danh sách sessions cần update trước khi xóa
        sessions_to_update = self.mapped('session_id')
        res = super(CyberSaleOrderInSession, self).unlink()

        # Trigger recompute cho các sessions đã lưu
        for session in sessions_to_update:
            if session.exists():
                session._compute_total_order()
        
        return res
