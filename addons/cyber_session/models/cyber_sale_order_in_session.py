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
        - ✅ KIỂM TRA balance TRƯỚC KHI tạo order
        - ✅ Tạo transaction chi tiêu
        - ✅ Trừ tiền qua transaction (transaction.create sẽ tự động update balance)
        - ✅ Tự động đóng phiên nếu hết tiền
        """
        # ✅ Tính line_total trước khi tạo record
        product = self.env['product.product'].browse(vals.get('product_id'))
        quantity = vals.get('quantity', 1.0)
        price_unit = vals.get('price_unit', product.list_price if product else 0.0)
        line_total = quantity * price_unit
        
        # ✅ Lấy session và account
        session = self.env['cyber.session'].browse(vals.get('session_id'))
        account = session.account_id

        if session.state != 'running':
            raise UserError(_("Không thể thêm order khi phiên đã đóng."))

        # ✅ KIỂM TRA balance TRƯỚC (undo automatic nếu không đủ)
        if account.balance < line_total:
            raise ValidationError(
                _("⚠️ Số dư không đủ để mua sản phẩm này!\n\nCần: %s VND\nCó: %s VND\nThiếu: %s VND") 
                % (line_total, account.balance, line_total - account.balance)
            )

        # ✅ Tạo order (AFTER validation)
        order = super(CyberSaleOrderInSession, self).create(vals)

        # ✅ Tạo transaction (transaction.create sẽ tự động update balance & total_spent)
        self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
            'account_id': account.id,
            'session_id': session.id,
            'amount': order.line_total,
            'type': 'spend',
            'payment_method': 'balance',
        })

        # ✅ Odoo sẽ tự động trigger:
        #    - _compute_balance() vì total_spent changed
        #    - _compute_end_time_expected() vì balance changed
        #    - _compute_total_cost() vì order_line_ids changed
        # ✅ end_time_expected sẽ được recalc → nếu <= now → _close_if_expired() sẽ đóng

        return order

    def write(self, vals):
        """Khi cập nhật order (thay đổi số lượng, giá):
        - Cập nhật lại transaction amount
        - Odoo sẽ tự động trigger balance & play_time_remaining recalculation
        """
        # ⚠️ Lưu old line_total TRƯỚC khi write
        old_amounts = {}
        for rec in self:
            old_amounts[rec.id] = rec.line_total
        
        res = super(CyberSaleOrderInSession, self).write(vals)
        
        for rec in self:
            session = rec.session_id
            account = session.account_id
            if session.state != 'running':
                continue

            # ✅ Nếu có thay đổi line_total, cập nhật transaction
            if 'quantity' in vals or 'price_unit' in vals:
                old_amount = old_amounts.get(rec.id, 0)
                new_amount = rec.line_total
                amount_diff = new_amount - old_amount
                
                if amount_diff != 0:
                    # Tìm transaction gắn với order này (search by old amount)
                    tx = self.env['cyber.transaction'].search([
                        ('session_id', '=', session.id),
                        ('account_id', '=', account.id),
                        ('amount', '=', old_amount),
                        ('type', '=', 'spend')
                    ], limit=1)
                    
                    if tx:
                        # Update transaction amount → triggers balance recalc
                        tx.sudo().write({'amount': new_amount})
                    else:
                        # Nếu không tìm thấy transaction cũ, tạo transaction cho diff
                        if amount_diff > 0:
                            self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
                                'account_id': account.id,
                                'session_id': session.id,
                                'amount': amount_diff,
                                'type': 'spend',
                                'payment_method': 'balance',
                            })
                
                # ✅ Odoo sẽ tự động trigger balance & play_time_remaining
                # ✅ Trigger session total_cost recalc (vì order_ids.line_total changed)
                # ✅ end_time_expected sẽ được recalc tự động

        return res

    def unlink(self):
        """Khi xóa order:
        - Xóa transaction tương ứng
        - Odoo sẽ tự động hoàn lại balance và play_time_remaining
        """
        # ⚠️ Lưu thông tin TRƯỚC khi xóa
        sessions_to_update = self.mapped('session_id')
        
        for rec in self:
            session = rec.session_id
            account = session.account_id
            if session.state == 'running':
                # ✅ Tìm và xóa transaction liên quan
                tx = self.env['cyber.transaction'].search([
                    ('session_id', '=', session.id),
                    ('account_id', '=', account.id),
                    ('amount', '=', rec.line_total),
                    ('type', '=', 'spend')
                ], limit=1, order='create_date desc')
                
                if tx:
                    # ⚠️ Hoàn lại total_spent TRƯỚC khi xóa transaction
                    account.sudo().write({
                        'total_spent': max(0, account.total_spent - tx.amount),
                    })
                    # ✅ Odoo sẽ tự động trigger _compute_balance() và _compute_play_time_remaining()
                    tx.sudo().unlink()

        res = super(CyberSaleOrderInSession, self).unlink()

        # ✅ Odoo sẽ tự động trigger _compute_total_cost() vì order_ids changed
        return res
