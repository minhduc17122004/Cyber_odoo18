from odoo import models, fields, api, exceptions, _


class CyberSession(models.Model):
    _name = 'cyber.session'
    _description = 'Cyber Game Session'
    _inherit = ['mail.thread']

    name = fields.Char(string='Session Name', required=True, copy=False, default=lambda self: _('New'))
    account_id = fields.Many2one('cyber.account', string='Account', required=True, ondelete='cascade')
    machine_id = fields.Many2one('product.product', string='Machine', required=True, domain=[('is_machine', '=', True)])
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now)
    end_time = fields.Datetime(string='End Time')
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True)
    price_per_hour = fields.Float(string='Price per Hour', required=True)
    total_cost = fields.Monetary(string='Total Cost', currency_field='currency_id', compute='_compute_total_cost', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='Status', default='running', tracking=True)

    invoice_id = fields.Many2one('account.move', string='Invoice', ondelete='set null')

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = round(delta.total_seconds() / 3600, 2)
            else:
                rec.duration = 0

    @api.depends('duration', 'price_per_hour')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = round(rec.duration * rec.price_per_hour, 2)

    def action_close_session(self):
        for rec in self:
            if rec.state == 'closed':
                continue

            if not rec.end_time:
                rec.end_time = fields.Datetime.now()

            rec._compute_duration()
            rec._compute_total_cost()

            account = rec.account_id

            if account.balance < rec.total_cost:
                raise exceptions.UserError(_('Insufficient balance to close this session.'))

            account.balance -= rec.total_cost
            account.total_spent += rec.total_cost
            account.last_spend_date = fields.Datetime.now()
            account.current_session_id = rec.id
            rec.state = 'closed'