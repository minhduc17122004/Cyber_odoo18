# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CyberTransaction(models.Model):
    _name = "cyber.transaction"
    _description = "Giao dịch tài khoản"
    _order = "create_date desc"

    account_id = fields.Many2one(
        'cyber.account',
        string='Tài khoản',
        required=True,
        ondelete='cascade'
    )

    # Điều này giúp biết transaction nào thuộc về session nào.
    session_id = fields.Many2one(
        'cyber.session',
        string='Phiên chơi liên quan',
        ondelete='set null'
    )

    type = fields.Selection([
        ('topup', 'Nạp tiền'),
        ('spend', 'Chi tiêu'),
    ], string='Loại giao dịch', required=True, default='topup')

    amount = fields.Float(string='Số tiền', digits=(10, 2), required=True)

    payment_method = fields.Selection([
        ('cash', 'Tiền mặt'),
        ('ewallet', 'Ví điện tử'),
        ('banking', 'Chuyển khoản ngân hàng'),
        ('balance', 'Từ số dư tài khoản'),  # ✅ Thêm option mới
    ], string='Phương thức thanh toán', required=True, default='cash')

    create_date = fields.Datetime(string='Ngày tạo', readonly=True)
    
    # ✅ Field note để phân biệt transaction (tránh duplicate)
    note = fields.Char(string='Ghi chú', help="Ví dụ: service:auto, service:manual, order:1234")
    
    # >>> ADD START: thêm field hiển thị số tiền bonus thực tế
    bonus_amount = fields.Float(string='Số tiền khuyến mãi (₫)', readonly=True, default=0.0)
    # <<< ADD END

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Số tiền giao dịch phải lớn hơn 0."))
    @api.model
    def create(self, vals):
        transaction = super(CyberTransaction, self).create(vals)
        account = transaction.account_id

        if not account:
            raise ValidationError(_("Không tìm thấy tài khoản để cập nhật số dư."))

        # Nếu là giao dịch nạp tiền
        if transaction.type == 'topup':
            # Lấy thông tin khách hàng và hạng (segment)
            customer = account.customer_id
            discount_rate = customer.segment_id.discount_rate if customer and customer.segment_id else 0.0

            # Tính số tiền cộng thêm (ví dụ discount_rate = 5 nghĩa là +5%)
            bonus = transaction.amount * (discount_rate / 100.0)
            total_add = transaction.amount + bonus
            # >>> ADD START: lưu lại bonus để hiển thị và dễ kiểm soát
            transaction.bonus_amount = bonus
            # <<< ADD END

            # ✅ Cập nhật total_recharge (balance sẽ tự động được tính từ computed field)
            account.sudo().write({
                'total_recharge': account.total_recharge + total_add,
                'last_topup_date': transaction.create_date,
            })

        # Nếu là giao dịch chi tiêu
        elif transaction.type == 'spend':
            if not self.env.context.get('from_session') and transaction.amount > account.balance:
                raise ValidationError(_("Số dư không đủ để thực hiện giao dịch chi tiêu."))
            
            # ✅ Cập nhật total_spent (balance sẽ tự động được tính từ computed field)
            account.sudo().write({
                'total_spent': account.total_spent + transaction.amount,
                'last_spend_date': transaction.create_date,
            })

        # ✅ Odoo sẽ tự động trigger _compute_balance() vì total_spent/total_recharge changed
        # ✅ Odoo sẽ tự động trigger _compute_play_time_remaining() vì balance changed

        return transaction