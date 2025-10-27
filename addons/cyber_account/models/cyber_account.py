# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CyberAccount(models.Model):
    _name = "cyber.account"
    _description = "Cyber Account"

    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)

    balance = fields.Float(
        compute='_compute_balance',
        string='Balance',
        digits=(10, 2),
        store=True
    )
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

    transaction_ids = fields.One2many(
        comodel_name='cyber.transaction',
        inverse_name='account_id',
        string='Transactions'
    )

    session_ids = fields.One2many(
        comodel_name='cyber.session',
        inverse_name='account_id',
        string='Sessions'
    )

    # =======================================================
    # COMPUTE & DEPENDS
    # =======================================================
    @api.depends('total_spent', 'total_recharge')
    def _compute_balance(self):
        for account in self:
            account.balance = round(account.total_recharge - account.total_spent, 2)

    # =======================================================
    # TRANSACTION HOOKS
    # =======================================================
    @api.model
    def update_from_transaction(self, transaction):
        """Gọi khi cyber.transaction được tạo"""
        for account in self:
            if transaction.account_id.id != account.id:
                continue

            if transaction.type == 'topup':
                account.total_recharge += transaction.amount
                account.last_topup_date = fields.Datetime.now()

            elif transaction.type == 'spend':
                account.total_spent += transaction.amount
                account.last_spend_date = fields.Datetime.now()

            account._compute_balance()
            account.customer_id._calculate_totals()

    # =======================================================
    # SESSION HOOKS
    # =======================================================
    @api.model
    def update_from_session(self, session):
        """Gọi khi session kết thúc"""
        for account in self:
            if session.account_id.id != account.id:
                continue

            account.play_time_total += session.duration
            account.total_spent += session.total_cost
            account.last_session_end = session.end_time

            # Tạo transaction loại 'spend' tương ứng
            self.env['cyber.transaction'].create({
                'account_id': account.id,
                'session_id': session.id,
                'type': 'spend',
                'amount': session.total_cost,
                'payment_method': 'balance',
                'note': f"Tự động trừ tiền phiên chơi {session.name}",
            })

            account._compute_balance()
            account.customer_id._calculate_totals()

    # =======================================================
    # OVERRIDE CRUD
    # =======================================================
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


# =======================================================
# EXTEND CYBER CUSTOMER RELATIONSHIP
# =======================================================
class CyberCustomer(models.Model):
    _inherit = "cyber.customer"

    account_ids = fields.One2many(
        comodel_name='cyber.account',
        inverse_name='customer_id',
        string='Accounts'
    )