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
    total_balance = fields.Float(string="Total Balance", digits=(10, 2), default=0.0)

    segment_id = fields.Many2one(
        'customer.segment',
        string='Phân khúc khách hàng',
    )
    segment_name = fields.Char(related="segment_id.segment_name", store=True)

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

                if customer.segment_id != segment.id:
                    customer.segment_id = segment.id
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

        customer.segment_id = segment.id
        return customer
    
    
    