# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CyberAccount(models.Model):
    _name = "cyber.account"
    _description = "Cyber Account"

    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)
    balance = fields.Float(compute="_compute_balance", string='Balance (VND)', digits=(16, 2), default=0.0, store=True)
    play_time_total = fields.Float('Play Time (hours)', default=0.0)
    play_time_remaining = fields.Float(compute="_compute_play_time_remaining", string='Play Time Remaining (hours)', default=0.0, store=True)
    play_time_remaining_seconds = fields.Float(string='Play Time Remaining (seconds)', compute="_compute_play_time_remaining", store=True)
    total_spent = fields.Float(string="Total Spent (VND)", digits=(16, 2), default=0.0)
    total_recharge = fields.Float(string="Total Recharge (VND)", digits=(16, 2), default=0.0)
    last_session_end = fields.Datetime(string="Last Session End")
    last_topup_date = fields.Datetime(string="Last Top-up Date")
    last_spend_date = fields.Datetime(string="Last Spend Date")
    state = fields.Selection([
        ('active', 'Hoạt động'),
        ('inactive', 'Không hoạt động'),
    ], string='State', default='active')

    customer_id = fields.Many2one(
        'cyber.customer', 
        string='Customer',
        required=True,
        ondelete='cascade'
    )
    display_name = fields.Char(
    string="Display Name",
    compute="_compute_display_name",
    store=False
)
    @api.depends('username')
    def _compute_display_name(self):
        """ hiển thị username thay cho 'cyber.account,ID'"""
        for record in self:
            record.display_name = record.username or f"Tài khoản #{record.id}"

    def write(self, vals):
        res = super().write(vals)
        for account in self:
            account.customer_id._calculate_totals()
        return res

    @api.model
    def create(self, vals):
        account = super().create(vals)
        if account.customer_id:
            account.customer_id._calculate_totals()
        return account
    
    def unlink(self):
        customers = self.mapped('customer_id')
        res = super().unlink()
        for customer in customers:
            customer._calculate_totals()
        return res

    
    @api.depends('total_recharge', 'total_spent')
    def _compute_balance(self):
        for account in self:
            account.balance = account.total_recharge - account.total_spent

    @api.depends('balance')
    def _compute_play_time_remaining(self):
        """Tính thời gian chơi còn lại dựa trên balance"""
        for account in self:
            # Tìm session đang chạy của account này
            session = self.env['cyber.session'].search([
                ('account_id', '=', account.id),
                ('state', '=', 'running')
            ], order='create_date desc', limit=1)

            if session and session.price_per_hour > 0:
                # Tính theo balance thực tế (không trừ cost_so_far)
                hours = account.balance / session.price_per_hour
                account.play_time_remaining = hours
                account.play_time_remaining_seconds = hours * 3600
            else:
                # Không có session đang chạy hoặc price = 0
                account.play_time_remaining = 0.0
                account.play_time_remaining_seconds = 0.0


    
class CyberCustomer(models.Model):
    _inherit = "cyber.customer"

    account_ids = fields.One2many(
        comodel_name='cyber.account',
        inverse_name='customer_id',
        string='Accounts'
    )

