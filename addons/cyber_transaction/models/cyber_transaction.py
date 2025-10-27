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

    session_id = fields.Many2one(
        'cyber.session',
        string='Phiên chơi',
        ondelete='set null',
        help='Liên kết tới phiên chơi nếu giao dịch này là chi tiêu tự động.'
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
        ('balance', 'Số dư tài khoản'),
    ], string='Phương thức thanh toán', required=True, default='cash')

    create_date = fields.Datetime(string='Ngày tạo', default=fields.Datetime.now, readonly=True)

    note = fields.Text(string='Ghi chú')

    # ===================== VALIDATION =====================
    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Số tiền giao dịch phải lớn hơn 0."))

    # ===================== BUSINESS LOGIC =====================
    @api.model
    def create(self, vals):
        record = super(CyberTransaction, self).create(vals)
        account = record.account_id

        if record.type == 'topup':
            # Khi nạp tiền → cộng vào balance
            account.balance += record.amount
            account.total_recharge += record.amount
            account.last_topup_date = fields.Datetime.now()

        elif record.type == 'spend':
            # Khi chi tiêu → trừ tiền, chỉ khi chưa trừ
            if account.balance < record.amount:
                raise ValidationError(_("Số dư không đủ để trừ tiền."))
            account.balance -= record.amount
            account.total_spent += record.amount
            account.last_spend_date = fields.Datetime.now()

        return record

    # ===================== SESSION HOOK =====================
    @api.model
    def create_from_session(self, session):
        """
        Được gọi khi phiên chơi (cyber.session) kết thúc.
        Tự động tạo transaction loại 'spend'.
        """
        return self.create({
            'account_id': session.account_id.id,
            'session_id': session.id,
            'type': 'spend',
            'amount': session.total_cost,
            'payment_method': 'balance',
            'note': f'Chi phí phiên chơi {session.name}',
        })
