from odoo import models, fields, _

class CyberTransaction(models.Model):
    _name = 'cyber.transaction'
    _description = 'Transaction History'

    account_id = fields.Many2one(
        'cyber.account',
        string='Account',
        required=True,
        ondelete='cascade'
    )

    type = fields.Selection([
        ('topup', 'Top-up'),
        ('spend', 'Spend'),
    ], string='Transaction Type', default='topup')

    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        required=True
    )

    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('ewallet', 'E-wallet'),
        ('banking', 'Bank Transfer'),
        ('balance', 'Account Balance'),
    ], string='Payment Method', default='cash')

    create_date = fields.Datetime(
        string='Created On',
        default=fields.Datetime.now
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )