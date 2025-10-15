# -*- coding: utf-8 -*-
from odoo import models, fields

class CyberProductTemplate(models.Model):
    _inherit = "product.template"

    # Classification
    is_machine = fields.Boolean(string="Is Machine", default=False, help="Mark this product as a gaming machine/station.")
    is_cyber_service = fields.Boolean(string="Is Cyber Service", default=False, help="Food/drinks/other services sold at cyber cafe.")

    service_type = fields.Selection([
        ('food', 'Food'),
        ('drink', 'Drink'),
        ('other', 'Other'),
    ], string="Service Type")

    # Machine properties
    ip_address = fields.Char(string="IP Address")
    location = fields.Char(string="Location/Area")
    status = fields.Selection([
        ('available', 'Available'),
        ('playing', 'Playing'),
        ('maintenance', 'Maintenance'),
    ], string="Machine Status", default='available')
    last_maintenance = fields.Date(string="Last Maintenance")