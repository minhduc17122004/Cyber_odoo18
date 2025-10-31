from odoo import models, fields

class CyberSession(models.Model):
    _name = 'cyber.session'
    _description = 'Dummy Cyber Session (for temporary dev use)'

    name = fields.Char(string="Tên phiên")
