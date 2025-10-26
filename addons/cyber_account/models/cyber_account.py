# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CyberAccount(models.Model):
    _name = "cyber.account"
    _description = "Cyber Account"

    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)
    balance = fields.Float('Balance', digits=(10, 2), default=0.0)
    play_time_total = fields.Float('Play Time (hours)', default=0.0)
    play_time_remaining = fields.Float('Play Time Remaining (hours)', default=0.0)
    total_spent = fields.Float(string="Total Spent", digits=(10, 2), default=0.0)
    total_recharge = fields.Float(string="Total Recharge", digits=(10, 2), default=0.0)
    last_session_end = fields.Datetime(string="Last Session End")
    last_topup_date = fields.Datetime(string="Last Top-up Date")
    last_spend_date = fields.Datetime(string="Last Spend Date")
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now, readonly=True)
    updated_at = fields.Datetime(string="Updated At", default=fields.Datetime.now, readonly=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
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
        for account in self:
            customer = account.customer_id
            res = super().unlink()
            customer._calculate_totals()
        return res


class CyberCustomer(models.Model):
    _inherit = "cyber.customer"

    account_ids = fields.One2many(
        comodel_name='cyber.account',
        inverse_name='customer_id',
        string='Accounts'
    )
