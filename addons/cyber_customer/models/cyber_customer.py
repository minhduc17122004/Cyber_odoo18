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
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now, readonly=True)
    updated_at = fields.Datetime(string="Updated At", default=fields.Datetime.now, readonly=True)

    segment_id = fields.Many2one(
        'customer.segment',
        string='Phân khúc khách hàng',
        ondelete='set null'
    )
    segment_name = fields.Char(related="segment_id.segment_name", store=True)

    # ===========================
    # UPDATE SEGMENT
    # ===========================
    def _update_segment(self):
        """Recalculate customer segment based on total play time"""
        for customer in self:
            segment = self.env['customer.segment'].search(
                [
                    ('conditions_time', '<=', customer.total_play_time),
                    ('is_active', '=', True)
                ],
                order='conditions_time desc',
                limit=1
            )
            if segment and customer.segment_id != segment:
                customer.segment_id = segment.id

    # ===========================
    # OVERRIDE WRITE / CREATE
    # ===========================
    def write(self, vals):
        res = super(CyberCustomer, self).write(vals)
        if 'total_play_time' in vals or 'total_spent' in vals:
            self._update_segment()
        return res

    @api.model
    def create(self, vals):
        customer = super(CyberCustomer, self).create(vals)
        customer._update_segment()
        return customer

    # ===========================
    # SYNC FROM ACCOUNT / SESSION
    # ===========================
    def _calculate_totals(self):
        """Sync totals from all active accounts"""
        for customer in self:
            accounts = self.env['cyber.account'].search([
                ('customer_id', '=', customer.id)
            ])
            customer.total_play_time = sum(acc.play_time_total for acc in accounts)
            customer.total_spent = sum(acc.total_spent for acc in accounts)
            customer._update_segment()

    def update_from_session(self, session):
        """Called by cyber.session when a session closes"""
        for customer in self:
            if session.account_id.customer_id.id == customer.id:
                customer.total_play_time += session.duration
                customer.total_spent += session.total_cost
                customer._update_segment()
