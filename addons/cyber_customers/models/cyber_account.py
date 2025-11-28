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
    play_time_remaining = fields.Float( string= 'Thời gian còn lại (giờ)', default=0.0)
    play_time_remaining_seconds = fields.Float(string='Thời gian còn lại (giây)')
    total_spent = fields.Float(string="Tổng chi tiêu (VND)", digits=(10, 2), default=0.0)
    total_recharge = fields.Float(string="Tổng nạp (VND)", digits=(10, 2), default=0.0)
    last_session_end = fields.Datetime(string="Ngày chơi cuối cùng")
    last_topup_date = fields.Datetime(string="Ngày nạp cuối cùng")
    last_spend_date = fields.Datetime(string="Ngày tiêu cuối cùng")
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

    _sql_constraints =  [
        ('username_unique', 'unique(username)', 'Tên tài khoản đã tồn tại!') ]

    @api.constrains('username')
    def _check_username(self):
        for record in self:
            username = record.username or ''

            # Không dấu, không ký tự đặc biệt
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                raise ValidationError("Tên tài khoản chứa ký tự không hợp lệ!")

    # @api.depends('balance')
    # def _compute_play_time_remaining(self):
    #     for account in self:
    #         session = self.env['cyber.session'].search([
    #             ('account_id', '=', account.id),
    #             ('state', '=', 'running')
    #         ], order='create_date desc', limit=1)

    #         if session and session.price_per_hour > 0:
    #             hours = account.balance / session.price_per_hour
    #             account.play_time_remaining = hours
    #             account.play_time_remaining_seconds = hours * 3600
    #         else:
    #             account.play_time_remaining = 0.0
    #             account.play_time_remaining_seconds = 0.0