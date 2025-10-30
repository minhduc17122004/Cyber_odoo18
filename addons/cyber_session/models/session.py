from odoo import models, fields, api, exceptions, _

class CyberSession(models.Model):
    _name = 'cyber.session'
    _description = 'Cyber Game Session'
    _inherit = ['mail.thread']

    name = fields.Char(string='Session Name', required=True, default=lambda self: _('New'))
    account_id = fields.Many2one('cyber.account', string='Account', required=True, ondelete='cascade')
    # machine_id = fields.Many2one('product.product', string='Machine', required=True, domain=[('is_machine', '=', True)])
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now)
    end_time = fields.Datetime(string='End Time')
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True)
    price_per_hour = fields.Float(string='Price per Hour', required=True)
    total_cost = fields.Monetary(string='Total Cost', currency_field='currency_id', compute='_compute_total', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='Status', default='running', tracking=True)

    # ========================
    # COMPUTE METHODS
    # ========================
    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = round(delta.total_seconds() / 3600, 2)
            else:
                rec.duration = 0

    @api.depends('duration', 'price_per_hour')
    def _compute_total(self):
        for rec in self:
            rec.total_cost = round(rec.duration * rec.price_per_hour, 2)

    # ========================
    # ACTION METHODS
    # ========================
    def action_start(self):
        for rec in self:
            if rec.account_id.balance <= 0:
                raise exceptions.UserError(_('Insufficient balance. Please top up first.'))
            rec.start_time = fields.Datetime.now()
            rec.state = 'running'

    def action_end(self):
        for rec in self:
            if rec.state == 'closed':
                continue
            rec.end_time = fields.Datetime.now()
            rec._compute_duration()
            rec._compute_total()

            acc = rec.account_id
            if acc.balance < rec.total_cost:
                raise exceptions.UserError(_('Not enough balance to pay this session.'))

            # ==========================
            # UPDATE ACCOUNT
            # ==========================
            acc.play_time_total += rec.duration
            acc.total_spent += rec.total_cost
            acc.last_session_end = rec.end_time
            acc._compute_balance()

            # ==========================
            # CREATE TRANSACTION
            # ==========================
            self.env['cyber.transaction'].create_from_session(rec)

            # ==========================
            # UPDATE CUSTOMER
            # ==========================
            if acc.customer_id:
                acc.customer_id.update_from_session(rec)

            rec.state = 'closed'

    def _compare_last_session_create_date(self):
        for session in self:
            last_transaction = self.env['cyber.transaction'].search([
                ('account_id', '=', session.account_id.id),
                ('type', '=', 'spend')
            ], order='create_date desc', limit=1)

            if last_transaction:
                create_date = last_transaction.create_date
                session.account_id.last_spend_date = create_date

                if session.account_id.last_session_end and session.account_id.last_session_end >= create_date:
                    session.account_id.last_spend_date = session.account_id.last_session_end


    def action_close_session(self):
        for session in self:
            session.end_time = fields.Datetime.now()
            session.state = 'closed'
            
            if session.account_id:
                session.account_id.total_spent += session.total_cost
                session.account_id.play_time_total += session.duration
                session.account_id.last_session_end = session.end_time
                session._compare_last_session_create_date()
        return True