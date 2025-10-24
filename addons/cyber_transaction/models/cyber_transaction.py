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
    username = fields.Char(related='account_id.username', string='Username', store=True)

    invoice_id = fields.Integer(string='Mã hóa đơn')

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

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Số tiền giao dịch phải lớn hơn 0."))
