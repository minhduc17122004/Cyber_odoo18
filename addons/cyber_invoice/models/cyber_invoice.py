# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CyberInvoice(models.Model):
    _inherit = "account.move"

    _description = "Cyber Invoice (Kế thừa Account Move)"

    # Không required để tránh lỗi khi tạo thủ công
    journal_id = fields.Many2one(required=False)

    # Liên kết
    customer_id = fields.Many2one('res.partner', string='Khách hàng', ondelete='cascade')
    session_id = fields.Many2one('cyber.session', string="Phiên chơi", ondelete='set null')
    transaction_id = fields.Many2one('cyber.transaction', string='Giao dịch liên quan', ondelete='set null')

    # Dữ liệu
    total_cost = fields.Float(
        string='Tổng chi phí gốc',
        compute="_compute_total_cost",
        store=True,
        digits=(12, 2)
    )

    discount_percent = fields.Float(string='Giảm giá (%)', digits=(5, 2), default=0.0)
    surcharge_percent = fields.Float(string='Phụ phí (%)', digits=(5, 2), default=0.0)
    tax_percent = fields.Float(string='Thuế (%)', digits=(5, 2), default=0.0)

    duration = fields.Float(string='Thời lượng (giờ)', compute='_compute_duration', store=True)
    note_cyber = fields.Text(string='Ghi chú thêm')

    # Account
    account_id = fields.Many2one("cyber.account", string="Tài khoản", ondelete="set null")

    # Invoice date mặc định 
    invoice_payment_term_id = fields.Many2one(
        "account.payment.term",
        default=lambda self: None      # Immediate Payment
    )

    invoice_date = fields.Date(
        default=lambda self: fields.Date.today()
    )

    # Compute: Tổng chi phí gốc
    @api.depends("invoice_line_ids", "invoice_line_ids.quantity", "invoice_line_ids.product_id")
    def _compute_total_cost(self):
        for rec in self:
            total = 0.0
            for line in rec.invoice_line_ids:
                qty = line.quantity or 0
                cost = line.product_id.standard_price or 0
                total += qty * cost
            rec.total_cost = total

    # Không cho tạo 2 invoice từ 1 session
    @api.constrains("session_id")
    def _check_unique_session_invoice(self):
        for rec in self:
            if rec.session_id:
                existed = self.search([
                    ("session_id", "=", rec.session_id.id),
                    ("id", "!=", rec.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "!=", "cancel")
                ], limit=1)

                if existed:
                    raise ValidationError(_("Phiên chơi này đã được tạo hóa đơn trước đó."))

    # Compute duration
    @api.depends('session_id.start_time', 'session_id.end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.session_id and rec.session_id.start_time and rec.session_id.end_time:
                rec.duration = (rec.session_id.end_time - rec.session_id.start_time).total_seconds() / 3600.0
            else:
                rec.duration = 0.0

    # Fill data khi chọn session
    @api.onchange('session_id')
    def _onchange_session_id(self):
        session = self.session_id
        if not session:
            return

        if session.customer_id:
            self.customer_id = session.customer_id

        if session.account_id:
            self.account_id = session.account_id

# Thêm payment method ở invoice line
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payment_method = fields.Selection(
        [
            ("account", "Account"),
            ("cash", "Cash"),
            ("bank", "Bank"),
        ],
        string="Phương thức thanh toán",
        default="cash",
    )
