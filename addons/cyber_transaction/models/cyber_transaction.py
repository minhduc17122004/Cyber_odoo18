# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


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

    session_id = fields.Many2one(
        'cyber.session',
        string='Phiên chơi liên quan',
        ondelete='set null'
    )

    type = fields.Selection([
        ('topup', 'Nạp tiền'),
        ('spend', 'Chi tiêu'),
    ], string='Loại giao dịch', required=True, default='topup')

    amount = fields.Float(string='Số tiền (₫)', digits=(10, 2), required=True)
    payment_method = fields.Selection([
        ('cash', 'Tiền mặt'),
        ('ewallet', 'Ví điện tử'),
        ('banking', 'Chuyển khoản ngân hàng'),
        ('balance', 'Trừ từ tài khoản')
    ], string='Phương thức thanh toán', required=True, default='cash')

    create_date = fields.Datetime(string='Thời gian giao dịch', readonly=True)
    bonus_amount = fields.Float(string='Số tiền khuyến mãi (₫)', readonly=True, default=0.0)

    # ===========================================
    # VALIDATION
    # ===========================================
    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Số tiền giao dịch phải lớn hơn 0."))

    # ===========================================
    # MAIN LOGIC
    # ===========================================
    @api.model
    def create(self, vals):
        transaction = super(CyberTransaction, self).create(vals)
        account = transaction.account_id

        if not account:
            raise ValidationError(_("Không tìm thấy tài khoản để cập nhật số dư."))

        # ===============================
        # GIAO DỊCH NẠP TIỀN
        # ===============================
        if transaction.type == 'topup':
            customer = account.customer_id
            discount_rate = 0.0
            if customer and customer.segment_id:
                discount_rate = getattr(customer.segment_id, 'discount_rate', 0.0)

            # Cập nhật số tiền khuyến mãi
            bonus = transaction.amount * (discount_rate / 100.0)
            total_add = transaction.amount + bonus
            transaction.sudo().write({'bonus_amount': bonus})

            # Cập nhật số tiền nạp và thời gian nạp
            account.sudo().write({
                'total_recharge': account.total_recharge + total_add,
                'last_topup_date': transaction.create_date or fields.Datetime.now(),
            })

        # ===============================
        # GIAO DỊCH CHI TIÊU
        # ===============================
        elif transaction.type == 'spend':
            # Kiểm tra số dư (trừ khi từ session đã kiểm tra rồi)
            if not self.env.context.get('from_session'):
                if transaction.amount > account.balance:
                    raise UserError(_(
                        "Số dư không đủ để thực hiện giao dịch chi tiêu.\n"
                        "Số dư hiện tại: %s VND\n"
                        "Số tiền cần chi tiêu: %s VND"
                    ) % (account.balance, transaction.amount))

            # Cập nhật số tiền chi tiêu và thời gian chi tiêu
            account.sudo().write({
                'total_spent': account.total_spent + transaction.amount,
                'last_spend_date': transaction.create_date or fields.Datetime.now(),
            })

        # ===============================
        # CẬP NHẬT SỐ DƯ TỰ ĐỘNG
        # ===============================
        account._compute_balance()

        # Đảm bảo số dư không âm
        if account.balance < 0:
            raise UserError(_("Cảnh báo: số dư không thể âm. Kiểm tra dữ liệu giao dịch."))

        return transaction
