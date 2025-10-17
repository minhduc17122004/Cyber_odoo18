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
