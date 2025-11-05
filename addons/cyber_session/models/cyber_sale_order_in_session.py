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
        - Tạo transaction chi tiêu tương ứng.
        - Trừ tiền account.
        - Tính lại total_cost & play_time_remaining.
        """
        order = super(CyberSaleOrderInSession, self).create(vals)
        session = order.session_id
        account = session.account_id

        if session.state != 'running':
            raise UserError(_("Không thể thêm order khi phiên đã đóng."))

        # ✅ Kiểm tra đủ tiền
        if account.balance < order.line_total:
            raise ValidationError(_("Số dư không đủ để mua sản phẩm này."))

        # ✅ Trừ tiền và ghi transaction
        account.sudo().write({
            'total_spent': account.total_spent + order.line_total,
        })
        account.sudo()._compute_balance()
        account.sudo()._compute_play_time_remaining()

        self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
            'account_id': account.id,
            'session_id': session.id,
            'amount': order.line_total,
            'type': 'spend',
            'payment_method': 'cash',
        })

        # ✅ Cập nhật session tổng chi phí
        session._compute_total_cost()

        # ✅ Tự động đóng nếu hết tiền
        session._auto_close_if_out_of_balance()

        return order

    def write(self, vals):
        """Khi cập nhật order (thay đổi số lượng, giá):
        - Cập nhật lại transaction tương ứng.
        - Tính lại balance và giờ chơi còn lại.
        """
        res = super(CyberSaleOrderInSession, self).write(vals)
        for rec in self:
            session = rec.session_id
            account = session.account_id
            if session.state != 'running':
                continue

            # ✅ Cập nhật lại transaction (nếu có thay đổi line_total)
            if 'quantity' in vals or 'price_unit' in vals:
                # Tìm transaction gắn với session (nếu có)
                tx = self.env['cyber.transaction'].search([
                    ('session_id', '=', session.id),
                    ('account_id', '=', account.id),
                    ('amount', '=', rec.line_total),
                    ('type', '=', 'spend')
                ], limit=1)
                if tx:
                    tx.sudo().write({'amount': rec.line_total})

                # ✅ Recompute balance & playtime
                account.sudo()._compute_balance()
                account.sudo()._compute_play_time_remaining()
                session._compute_total_cost()
                session._auto_close_if_out_of_balance()

        return res

    def unlink(self):
        """Khi xóa order:
        - Hoàn lại tiền (nếu cần).
        - Cập nhật balance và playtime.
        """
        for rec in self:
            session = rec.session_id
            account = session.account_id
            if session.state == 'running':
                # ✅ Hoàn tiền
                account.sudo().write({
                    'total_spent': max(0, account.total_spent - rec.line_total),
                })
                account.sudo()._compute_balance()
                account.sudo()._compute_play_time_remaining()

                # ✅ Xóa transaction liên quan
                tx = self.env['cyber.transaction'].search([
                    ('session_id', '=', session.id),
                    ('account_id', '=', account.id),
                    ('amount', '=', rec.line_total),
                    ('type', '=', 'spend')
                ])
                tx.unlink()

        res = super(CyberSaleOrderInSession, self).unlink()

        # ✅ Cập nhật lại tổng chi phí
        for session in self.mapped('session_id'):
            session._compute_total_cost()
        return res
