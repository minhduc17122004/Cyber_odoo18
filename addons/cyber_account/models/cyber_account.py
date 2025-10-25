# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class CyberAccount(models.Model):
    _name = "cyber.account"
    _description = "Cyber Account"

    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)
    balance = fields.Float('Balance', digits=(10, 2), default=0.0)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='State', default='active')
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.username} ({record.balance:,.0f}đ)"
            result.append((record.id, name))
        return result
    

    # Relationship Fields 
    # discount_id = fields.Many2one(
    #     'cyber.discount.rate', 
    #     string='Discount Rate',
    #     ondelete='set null'
    # )

    customer_id = fields.Many2one(
        'res.partner', 
        string='Customer',
        ondelete='cascade'
    )

    # transaction_ids = fields.One2many(
    #     'cyber.transaction',
    #     'account_id',
    #     string='Transactions'
    # )

    # session_ids = fields.One2many(
    #     'cyber.session',
    #     'account_id',
    #     string='Sessions'
    # )

    @api.constrains('balance')
    def _check_balance(self):
        for rec in self:
            if rec.balance < 0:
                raise ValidationError(_("Account balance cannot be negative."))
