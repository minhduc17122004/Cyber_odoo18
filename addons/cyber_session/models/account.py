from odoo import models, fields


class CyberAccount(models.Model):
    _name = 'cyber.account'
    _description = 'Prepaid Account'

    name = fields.Char(string='Username', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer')
    balance = fields.Monetary(string='Balance', currency_field='currency_id', default=0.0)
    total_recharge = fields.Monetary(string='Total Recharge', currency_field='currency_id', default=0.0)
    total_spent = fields.Monetary(string='Total Spent', currency_field='currency_id', default=0.0)
    play_time_total = fields.Float(string='Total Play Time (hours)', default=0.0)
    last_spend_date = fields.Datetime(string='Last Spend Date')
    last_topup_date = fields.Datetime(string='Last Top-up Date')
    current_session_id = fields.Many2one('cyber.session', string='Current Session', ondelete='set null')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)