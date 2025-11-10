from odoo import models, fields, api

class CyberCustomer(models.Model):
    _inherit = 'res.partner'  # Kế thừa model gốc

    dob = fields.Date(string="Ngày sinh")
    join_date = fields.Date(string="Ngày tham gia", default=fields.Date.context_today)
    total_play_time = fields.Float(string="Thời gian đã chơi (giờ)", compute='_compute_totals', default=0.0)
    total_spent = fields.Float(string="Tổng chi tiêu (VND)", compute='_compute_totals', digits=(10, 2), default=0.0)
    total_recharge = fields.Float(string="Tổng nạp (VND)", compute='_compute_totals', digits=(10, 2), default=0.0)

    segment_id = fields.Many2one(
        'customer.segment',
        string='Phân khúc',
        ondelete='set null'
    )

    account_ids = fields.One2many(
        'cyber.account',
        'customer_id',
        string='Accounts'
    )

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._update_segment()
        return record

    def write(self, vals):
        res = super().write(vals)
        self._update_segment()
        return res

    def _update_segment(self):
        for customer in self:

            segment = self.env['customer.segment'].search([
                ('conditions_time', '<=', customer.total_play_time),
                ('is_active', '=', True)
            ], order='conditions_time desc', limit=1)

            if segment and customer.segment_id != segment:
                customer.segment_id = segment

    @api.depends('account_ids.total_spent', 'account_ids.total_recharge', 'account_ids.play_time_total', 'account_ids.state')
    def _compute_totals(self):
        for customer in self:
            accounts = customer.account_ids.filtered(lambda a: a.state == 'active')

            total_play = sum(account.play_time_total for account in accounts)
            total_spent = sum(account.total_spent for account in accounts)
            total_recharge = sum(account.total_recharge for account in accounts)

            customer.total_play_time = total_play
            customer.total_spent = total_spent
            customer.total_recharge = total_recharge
            customer._update_segment()



