from odoo import models, fields, api

class CyberCustomer(models.Model):
    _inherit = "res.partner"

    member_type = fields.Selection([
        ('normal', 'Thành viên thường'),
        ('vip', 'Thành viên VIP'),
        ('banned', 'Cấm tài khoản'),
    ], default='normal', string="Loại thành viên")

    balance = fields.Float(string="Số dư tài khoản", default=0.0)
    join_date = fields.Date(string="Ngày tham gia", default=fields.Date.today)
    total_play_time = fields.Float(string="Tổng giờ chơi (giờ)", default=0.0)
    note = fields.Text(string="Ghi chú thêm")

    def action_recharge_balance(self):
        """Tăng số dư ảo để test"""
        for rec in self:
            rec.balance += 10000

    def action_deduct_balance(self):
        """Giảm số dư ảo"""
        for rec in self:
            rec.balance -= 5000
