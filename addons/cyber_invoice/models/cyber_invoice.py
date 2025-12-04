# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CyberInvoice(models.Model):
    _inherit = "account.move"

    _description = "Cyber Invoice (Kế thừa Account Move)"

    # Không required để tránh lỗi khi tạo thủ công
    journal_id = fields.Many2one(required=False)

    # Liên kết - QUAN TRỌNG: store=True để lưu vào database
    session_id = fields.Many2one(
        'cyber.session', 
        string="Phiên chơi", 
        ondelete='set null',
        store=True,
        copy=False
    )
    account_id = fields.Many2one(
        "cyber.account", 
        string="Tài khoản", 
        ondelete="set null",
        store=True,  # BẮT BUỘC để lưu vào DB
        copy=False,
        index=True
    )
    
    # Field để hiển thị khách hàng (computed từ account_id.customer_id)
    customer_display = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        compute='_compute_customer_display',
        store=True,
        readonly=True
    )

    # Dữ liệu
    total_cost = fields.Float(
        string='Tổng chi phí gốc',
        compute="_compute_total_cost",
        store=True,
        digits=(12, 2)
    )

    discount_percent = fields.Float(string='Giảm giá (%)', digits=(5, 2), default=0.0, store=True)
    surcharge_percent = fields.Float(string='Phụ phí (%)', digits=(5, 2), default=0.0, store=True)
    tax_percent = fields.Float(string='Thuế (%)', digits=(5, 2), default=0.0, store=True)

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
    @api.depends(
        "invoice_line_ids.price_unit",
        "invoice_line_ids.quantity",
        "discount_percent",
        "surcharge_percent",
        "tax_percent",
    )
    def _compute_total_cost(self):
        """
        Tính tổng dựa trên price_unit * quantity của invoice lines,
        sau đó áp dụng discount, surcharge, tax
        """
        for rec in self:
            base = 0.0
            for line in rec.invoice_line_ids:
                qty = line.quantity or 0.0
                price = line.price_unit or 0.0
                base += qty * price
            
            # Áp dụng thứ tự: discount -> surcharge -> tax
            net = base * (1 - (rec.discount_percent or 0.0) / 100.0)
            net = net * (1 + (rec.surcharge_percent or 0.0) / 100.0)
            net = net * (1 + (rec.tax_percent or 0.0) / 100.0)
            rec.total_cost = float(round(net, 2))

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

    # Compute customer display từ account_id
    @api.depends('account_id')
    def _compute_customer_display(self):
        for rec in self:
            if rec.account_id and rec.account_id.customer_id:
                rec.customer_display = rec.account_id.customer_id
            else:
                rec.customer_display = False

    @api.onchange('session_id')
    def _onchange_session_id(self):
        """
        Khi chọn session, tự động điền invoice lines và map partner_id từ account.customer_id
        """
        session = self.session_id
        if not session:
            self.partner_id = False
            self.account_id = False
            self.total_cost = 0.0
            self.duration = 0.0
            self.invoice_line_ids = [(5, 0, 0)]
            self.discount_percent = 0.0
            self.surcharge_percent = 0.0
            self.tax_percent = 0.0
            return

        # Kiểm tra session phải đã closed
        if session.session_state != 'closed':
            return {
                'warning': {
                    'title': _("Invalid Session"),
                    'message': _("Phiên chơi phải ở trạng thái 'Closed' để tạo hóa đơn.")
                }
            }

        # Điền account từ session (NHƯNG CHƯA SET partner_id)
        if session.account_id:
            self.account_id = session.account_id
        else:
            self.account_id = False

        # Điền tổng chi phí và duration
        self.total_cost = session.total_sale or 0.0
        self.duration = session.duration or 0.0

        # Reset adjustment fields
        self.discount_percent = 0.0
        self.surcharge_percent = 0.0
        self.tax_percent = 0.0

        # **QUAN TRỌNG**: Tạo invoice lines TRƯỚC khi set partner_id
        # Để tránh Odoo trigger onchange partner_id và làm sai amount
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

        #  invoice lines 
        self.invoice_line_ids = [(5, 0, 0)] + invoice_lines

        
        if session.account_id and session.account_id.customer_id:
            self.partner_id = session.account_id.customer_id
        else:
            self.partner_id = False

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create để đảm bảo partner_id được set từ account_id.customer_id
        """
        for vals in vals_list:
            # Nếu có account_id nhưng chưa có partner_id, map từ account
            if vals.get('account_id') and not vals.get('partner_id'):
                try:
                    account = self.env['cyber.account'].browse(vals['account_id'])
                    if account.customer_id:
                        vals['partner_id'] = account.customer_id.id
                    else:
                        raise ValidationError(
                            _("Account '%s' không có customer liên kết. "
                              "Vui lòng thêm customer cho account này.") 
                            % account.name
                        )
                except Exception as e:
                    raise ValidationError(_("Lỗi map partner từ account: %s") % str(e))
            
            # Kiểm tra partner_id là bắt buộc
            if not vals.get('partner_id'):
                raise ValidationError(
                    _("Khách hàng (Customer) là bắt buộc. "
                      "Vui lòng chọn session có account với customer.")
                )
        
        return super(CyberInvoice, self).create(vals_list)

    def write(self, vals):
        """
        Override write để map partner_id từ account_id khi cần
        và đảm bảo account_id được lưu khi confirm hóa đơn
        """
        # Nếu user update account_id mà không gửi partner_id, map nó
        if 'account_id' in vals and vals.get('account_id') and 'partner_id' not in vals:
            try:
                account = self.env['cyber.account'].browse(vals['account_id'])
                if account.customer_id:
                    vals = dict(vals)
                    vals['partner_id'] = account.customer_id.id
                else:
                    raise ValidationError(
                        _("Account '%s' không có customer liên kết.") 
                        % account.name
                    )
            except Exception as e:
                raise ValidationError(_("Lỗi map partner từ account: %s") % str(e))
        
        return super(CyberInvoice, self).write(vals)

    def action_post(self):
        # Force giữ field custom trước khi post
        for rec in self:
            if rec.account_id or rec.partner_id or rec.session_id:
                rec.sudo().write({
                    'account_id': rec.account_id.id if rec.account_id else False,
                    'partner_id': rec.partner_id.id if rec.partner_id else False,
                    'session_id': rec.session_id.id if rec.session_id else False,
                    'duration': rec.duration,
                    'total_cost': rec.total_cost,
                    'discount_percent': rec.discount_percent,
                    'surcharge_percent': rec.surcharge_percent,
                    'tax_percent': rec.tax_percent,
                })

        res = super(CyberInvoice, self).action_post()  
        return res



    def action_draft(self):
        """
        Override action_draft để reset về draft state
        """
        return super(CyberInvoice, self).action_draft()

    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    quantity = fields.Float(
        digits=(16, 3)
    )

    payment_method = fields.Selection(
        [
            ("account", "Account"),
            ("cash", "Cash"),
            ("bank", "Bank"),
        ],
        string="Phương thức thanh toán",
        default="cash",
        store=True
    )

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        payments = super()._create_payments()

        for payment in payments:
            moves = payment.reconciled_invoice_ids  # các hóa đơn được thanh toán bởi payment

            for invoice in moves:
                # Tính tổng account_spent dựa trên line có payment_method == "account"
                account_spent = 0.0
                for line in invoice.invoice_line_ids:
                    if line.payment_method == "account":
                        account_spent += line.price_subtotal

                # Cộng cho account nếu có
                if invoice.account_id and account_spent > 0:
                    invoice.account_id.total_spent += account_spent
                    invoice.account_id.update_last_dates()
                    invoice.account_id.play_time_total += invoice.duration

                # Cộng cho customer
                if invoice.partner_id:
                    invoice.partner_id.total_spent += payment.amount

        return payments
