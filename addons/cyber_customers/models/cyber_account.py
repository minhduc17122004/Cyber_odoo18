# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CyberAccount(models.Model):
    _name = "cyber.account"
    _description = "Cyber Account"
    _rec_name = 'username'

    username = fields.Char('Tài khoản', required=True)
    password = fields.Char('Mật khẩu', required=True)
    balance = fields.Float(compute="_compute_balance", string='Số dư (VND)', digits=(10, 2), default=0.0)
    play_time_total = fields.Float('Thời gian chơi (giờ)', default=0.0)
    total_spent = fields.Float(string="Tổng chi tiêu (VND)", digits=(10, 2), default=0.0)
    total_recharge = fields.Float(string="Tổng nạp (VND)", digits=(10, 2), default=0.0)
    last_session_end = fields.Date(string="Thời gian chơi gần nhất")
    last_topup_date = fields.Date(string="Thời gian nạp tiền gần nhất")
    last_spend_date = fields.Date(string="Thời gian chi tiêu gần nhất")
    state = fields.Selection([
        ('active', 'Hoạt động'),
        ('inactive', 'Không hoạt động')
    ], string='Trạng thái', default='active')

    customer_id = fields.Many2one(
        'res.partner', 
        string='Khách hàng',
        required=True,
        ondelete='cascade'
    )

    @api.depends('total_recharge', 'total_spent')
    def _compute_balance(self):
        for account in self:
            account.balance = account.total_recharge - account.total_spent

    def update_last_dates(self):
        for rec in self:
            # Lấy ngày chơi cuối cùng bằng search phiên chơi với điều kiện account_id = rec.id
            last_session = self.env['cyber.session'].search(
                [('account_id', '=', rec.id), ('start_time', '!=', False)],
                order='start_time desc',
                limit=1
            )
            rec.last_session_end = last_session.start_time

            # Lấy ngày tiêu cuối cùng bằng search hóa đơn đã paid, liên kết account
            last_invoice = self.env['account.move'].search(
                [
                    ('account_id', '=', rec.id),
                    ('state', '=', 'posted'),
                    ('invoice_date', '!=', False)
                ],
                order='invoice_date desc',
                limit=1
            )
            rec.last_spend_date = last_invoice.invoice_date if last_invoice else False

    _sql_constraints =  [
        ('username_unique', 'unique(username)', 'Tên tài khoản đã tồn tại!') ]

    @api.constrains('username')
    def _check_username(self):
        for record in self:
            username = record.username or ''

            # Không dấu, không ký tự đặc biệt
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                raise ValidationError("Tên tài khoản chứa ký tự không hợp lệ!")