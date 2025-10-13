from odoo import models, fields

class CyberCustomer(models.Model):
    _inherit = "res.partner"

    total_balance = fields.Monetary(string="Tổng số dư", currency_field="currency_id", default=0.0)
    join_date = fields.Date(string="Ngày tham gia", default=fields.Date.today)
    total_play_time = fields.Float(string="Tổng giờ chơi (h)", default=0.0)
    DOB = fields.Date(string="Ngày sinh")
    phone_num = fields.Char(string="Số điện thoại")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id.id)