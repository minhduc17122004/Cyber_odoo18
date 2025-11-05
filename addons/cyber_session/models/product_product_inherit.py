# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = "product.product"

    is_machine = fields.Boolean(string="Is Machine", default=False)
