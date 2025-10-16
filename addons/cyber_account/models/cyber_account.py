from odoo import models, fields, api

class CyberAccount(models.Model):
    _name = 'cyber.account'
    _description = 'Tài khoản khách hàng quán net'

    name = fields.Char(string="Tên tài khoản", required=True)
    username = fields.Char(string="Tên đăng nhập", required=True)
    password = fields.Char(string="Mật khẩu", required=True)
    balance = fields.Float(string="Số dư (VNĐ)", default=0.0)
    is_active = fields.Boolean(string="Đang hoạt động", default=True)
    phone = fields.Char(string="Số điện thoại")
    email = fields.Char(string="Email")

    # Giả sử mỗi tài khoản có thể thuộc một loại khách hàng
    account_type = fields.Selection([
        ('normal', 'Thường'),
        ('vip', 'VIP'),
    ], string="Loại tài khoản", default='normal')

    note = fields.Text(string="Ghi chú")
    customer_id = fields.Many2one(
        'cyber.customer', 
        string="Khách hàng",
        ondelete='cascade'
    )


    @api.depends('balance')
    def _compute_status(self):
        for rec in self:
            rec.status = 'Hết tiền' if rec.balance <= 0 else 'Còn tiền'

    status = fields.Char(string="Trạng thái", compute="_compute_status", store=True)
