# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CyberInvoice(models.Model):
    _inherit = "account.move"

    _description = "Cyber Invoice (Kế thừa Account Move)"

    # Không required để tránh lỗi khi tạo thủ công
    journal_id = fields.Many2one(required=False)

    # Liên kết
    session_id = fields.Many2one('cyber.session', string="Phiên chơi", ondelete='set null')
    account_id = fields.Many2one("cyber.account", string="Tài khoản", ondelete="set null")
    customer_id = fields.Many2one('res.partner', string='Khách hàng', ondelete='cascade')

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
            rec.total_cost = total-(rec.discount_percent/100)*total+(rec.surcharge_percent/100)*total+(rec.tax_percent/100)*total

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

    @api.onchange('session_id')
    def _onchange_session_id(self):
        """
        Khi chọn session, tự động điền invoice lines
        """
        session = self.session_id
        if not session:
            self.customer_id = False
            self.account_id = False
            self.total_cost = 0.0
            self.duration = 0.0
            self.invoice_line_ids = [(5, 0, 0)]
            return

        # Kiểm tra session phải đã closed
        if session.session_state != 'closed':
            return {
                'warning': {
                    'title': _("Invalid Session"),
                    'message': _("Phiên chơi phải ở trạng thái 'Closed' để tạo hóa đơn.")
                }
            }
        # Điền customer & account từ session
        if session.account_id:
            self.account_id = session.account_id
            self.customer_id = session.account_id.customer_id or False
        else:
            self.account_id = False
            self.customer_id = False

        # Điền tổng chi phí và duration
        self.total_cost = session.total_sale or 0.0
        self.duration = session.duration or 0.0

        # Tạo invoice lines
        invoice_lines = []

        # Thêm dịch vụ máy (session service)
        if session.total_service > 0 and session.product_machine_id:
            invoice_lines.append((0, 0, {
                'product_id': session.product_machine_id.id,
                'quantity': session.duration,
                'price_unit': session.price_per_hour,
                'name': _("Machine: %s (%.2f hours)") % (session.product_machine_id.name, session.duration),
                'payment_method': 'account',
            }))

        # Thêm các orders trong session
        if session.order_ids:
            for order in session.order_ids:
                invoice_lines.append((0, 0, {
                    'product_id': order.product_id.id,
                    'quantity': order.quantity,
                    'price_unit': order.price_unit,
                    'name': order.product_id.name,
                    'payment_method': 'cash',
                }))

        # Gán invoice lines
        self.invoice_line_ids = [(5, 0, 0)]
        self.invoice_line_ids = invoice_lines
    
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
