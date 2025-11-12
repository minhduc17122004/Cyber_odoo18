from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class CyberSaleOrderInSession(models.Model):
    _name = 'cyber.sale_order_in_session'
    _description = 'Sale Order in Session'

    session_id = fields.Many2one('cyber.session', string='Session', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price (VND)', digits=(16, 0))
    line_total = fields.Float(string='Line Total (VND)', compute='_compute_line_total', store=True, digits=(16, 0))
    note = fields.Char(string='Ghi chú')

    @api.depends('quantity', 'price_unit')
    def _compute_line_total(self):
        for rec in self:
            rec.line_total = rec.quantity * rec.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Tự động điền giá bán khi chọn sản phẩm"""
        for rec in self:
            if rec.product_id:
                rec.price_unit = rec.product_id.list_price

    # ==================================================
    # OVERRIDES
    # ==================================================
    @api.model
    def create(self, vals):
        """Khi tạo order mới trong session:
        - Kiểm tra available_balance
        - Tạo transaction chi tiêu
        - Trigger session recompute
        - Auto-close nếu hết tiền
        """
        order = super(CyberSaleOrderInSession, self).create(vals)
        session = order.session_id
        account = session.account_id

        if session.state != 'running':
            raise UserError(_("Không thể thêm order khi phiên đã đóng."))

        # ✅ Kiểm tra available_balance >= line_total (theo Requirement 8.1)
        if session.available_balance < order.line_total:
            raise ValidationError(_("Số dư không đủ để mua sản phẩm này."))

        # ✅ Tạo transaction chi tiêu
        self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
            'account_id': account.id,
            'session_id': session.id,
            'amount': order.line_total,
            'type': 'spend',
            'payment_method': 'cash',
        })

        # ✅ Trigger session recompute (sẽ tự động cập nhật available_balance, time_remaining, etc.)
        session._compute_total_order()
        session._compute_total_cost()

        # ✅ Tự động đóng nếu hết tiền
        session._auto_close_if_out_of_balance()

        return order

    def write(self, vals):
        """Khi cập nhật order (thay đổi số lượng, giá):
        - Trigger session recompute
        - Auto-close nếu cần
        """
        res = super(CyberSaleOrderInSession, self).write(vals)
        for rec in self:
            session = rec.session_id
            if session.state != 'running':
                continue

            # ✅ Trigger session recompute khi có thay đổi
            if 'quantity' in vals or 'price_unit' in vals:
                session._compute_total_order()
                session._compute_total_cost()
                session._auto_close_if_out_of_balance()

        return res

    def unlink(self):
        """Khi xóa order:
        - Xóa transaction liên quan
        - Trigger session recompute
        """
        sessions_to_update = self.mapped('session_id')
        
        for rec in self:
            session = rec.session_id
            if session.state == 'running':
                # ✅ Xóa transaction liên quan
                tx = self.env['cyber.transaction'].search([
                    ('session_id', '=', session.id),
                    ('account_id', '=', session.account_id.id),
                    ('amount', '=', rec.line_total),
                    ('type', '=', 'spend')
                ], limit=1)
                if tx:
                    tx.unlink()

        res = super(CyberSaleOrderInSession, self).unlink()

        # ✅ Trigger session recompute sau khi xóa
        for session in sessions_to_update:
            if session.exists():
                session._compute_total_order()
                session._compute_total_cost()
        
        return res
