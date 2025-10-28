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
    username = fields.Char(related='account_id.username', string='Tên đăng nhập', readonly=True)

    type = fields.Selection([
        ('topup', 'Nạp tiền'),
        ('spend', 'Chi tiêu'),
    ], string='Loại giao dịch', required=True, default='topup')

    amount = fields.Float(string='Số tiền', digits=(10, 2), required=True)

    payment_method = fields.Selection([
        ('cash', 'Tiền mặt'),
        ('ewallet', 'Ví điện tử'),
        ('banking', 'Chuyển khoản ngân hàng'),
    ], string='Phương thức thanh toán', required=True, default='cash')

    create_date = fields.Datetime(string='Ngày tạo', readonly=True)
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

            # Cập nhật số dư
            account.balance += total_add

            # Cập nhật tổng số lần & ngày nạp gần nhất (nếu có field tương ứng)
            if hasattr(account, 'total_recharge'):
                account.total_recharge += transaction.amount
            if hasattr(account, 'last_topup_date'):
                account.last_topup_date = fields.Datetime.now()
             #  tính giờ chơi từ số tiền nạp
            added_hours = total_add / 20000.0  # 1 giờ = 20,000 VNĐ
            account.play_time_total += added_hours
            account.play_time_remaining += added_hours
            # 

        # Nếu là giao dịch chi tiêu
        elif transaction.type == 'spend':
            if transaction.amount > account.balance:
                raise ValidationError(_("Số dư không đủ để thực hiện giao dịch chi tiêu."))
            account.balance -= transaction.amount
            #  trừ thời gian chơi tương ứng với số tiền chi tiêu
            spent_hours = transaction.amount / 20000.0
            account.play_time_remaining -= spent_hours
            if account.play_time_remaining < 0:
                account.play_time_remaining = 0
            if hasattr(account, 'last_spend_date'):
                account.last_spend_date = fields.Datetime.now()
            # 

        # Lưu lại thay đổi
        account.sudo().write({
            'balance': account.balance,
            'play_time_total': account.play_time_total,
            'play_time_remaining': account.play_time_remaining,
        })

        return transaction