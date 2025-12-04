# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CyberTopup(models.Model):
    _name = "cyber.topup"
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

    amount = fields.Float(string='Số tiền nạp', digits=(10, 2), required=True)

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
                raise ValidationError(_("Số tiền nạp phải lớn hơn 0."))
            
    @api.model
    def create(self, vals):
        topup = super(CyberTopup, self).create(vals)
        account = topup.account_id

        if not account:
            raise ValidationError(_("Không tìm thấy tài khoản để cập nhật số dư."))

        # Lấy thông tin khách hàng và hạng (segment)
        customer = account.customer_id
        discount_rate = customer.segment_id.discount_rate if customer and customer.segment_id else 0.0

        # Tính số tiền cộng thêm (ví dụ discount_rate = 5 nghĩa là +5%)
        bonus = topup.amount * (discount_rate / 100.0)
        total_add = topup.amount + bonus
        # >>> ADD START: lưu lại bonus để hiển thị và dễ kiểm soát
        topup.bonus_amount = bonus
        # <<< ADD END

        # Cập nhật tổng số lần & ngày nạp gần nhất
        if hasattr(account, 'total_recharge'):
            account.total_recharge += total_add
        if hasattr(account, 'last_topup_date'):
            account.update_last_dates()

        # Lưu lại thay đổi
        account.sudo().write({
            'balance': account.balance,
            'total_spent': account.total_spent,
            'total_recharge': account.total_recharge,
        })

        return topup