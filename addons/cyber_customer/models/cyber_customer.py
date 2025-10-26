# -*- coding: utf-8 -*-
from odoo import api, fields, models

class CyberCustomer(models.Model):
    _name = "cyber.customer"
    _inherits = {"res.partner": "partner_id"}   
    _description = "Cyber Customer"

    partner_id = fields.Many2one(
        "res.partner", 
        string="Partner", 
        required=True, 
        ondelete="cascade",
        auto_join=True
    )
    dob = fields.Date(string="Date of Birth")
    join_date = fields.Date(string="Join Date", default=fields.Date.context_today)
    total_play_time = fields.Float(string="Total Play Time (hours)", default=0.0)
    total_spent = fields.Float(string="Total Spent", digits=(10, 2), default=0.0)
    last_sesion_end = fields.Datetime(string="Last Session End")
    last_topup_date = fields.Datetime(string="Last Top-up Date")
    last_spend_date = fields.Datetime(string="Last Spend Date")
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now, readonly=True)
    updated_at = fields.Datetime(string="Updated At", default=fields.Datetime.now, readonly=True)

    segment_id = fields.Many2one(
        'customer.segment',
        string='Phân khúc khách hàng',
        ondelete='set null'
    )
    segment_name = fields.Char(related="segment_id.segment_name", store=True)

    # account_ids = fields.One2many(
    #     comodel_name='cyber.account',
    #     inverse_name='customer_id',
    #     string='Accounts'
    # )

    def write(self, vals):
        res = super(CyberCustomer, self).write(vals)

        if 'total_play_time' in vals:
            for customer in self:
                segment = self.env['customer.segment'].search(
                    [('conditions_time', '<=', customer.total_play_time),
                     ('is_active', '=', True)],
                    order='conditions_time desc',
                    limit=1
                )

                # Sửa đây: kiểm tra segment có tồn tại không
                new_segment_id = segment.id if segment else False
                if customer.segment_id.id != new_segment_id:
                    customer.segment_id = new_segment_id

        return res
    
    @api.model
    def create(self, vals):
        customer = super(CyberCustomer, self).create(vals)

        segment = self.env['customer.segment'].search(
            [('conditions_time', '<=', customer.total_play_time),
             ('is_active', '=', True)],
            order='conditions_time desc',
            limit=1
        )

        # Sửa đây: kiểm tra segment có tồn tại không
        if segment:
            customer.segment_id = segment.id
        else:
            customer.segment_id = False

        return customer
    
    def _calculate_totals(self):
        for customer in self:
            accounts = self.env['cyber.account'].search([
                ('customer_id', '=', customer.id), 
                ('state', '=', 'active')
            ])
            customer.total_play_time = sum(acc.play_time_total for acc in accounts)
            customer.total_spent = sum(acc.total_spent for acc in accounts)