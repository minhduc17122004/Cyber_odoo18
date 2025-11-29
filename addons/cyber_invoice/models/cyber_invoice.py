def _post(self):
        """
        Override _post để gán income account cho TẤT CẢ lines
        Bỏ receivable/payable account trước khi post
        """
        for rec in self:
            company = self.env.company
            Account = self.env['account.account']
            
            # Tìm income account
            income_acc = Account.search([
                ('account_type', '=', 'income'),
                ('company_ids', 'in', company.id),
            ], limit=1)
            
            if not income_acc:
                income_acc = Account.search([
                    ('account_type', 'not in', ['asset_receivable', 'liability_payable']),
                    ('company_ids', 'in', company.id),
                ], limit=1)
            
            # Gán income account cho TẤT CẢ lines
            if income_acc:
                for line in rec.invoice_line_ids:
                    # Bỏ receivable/payable, dùng income account
                    if line.account_id.account_type in ['asset_receivable', 'liability_payable']:
                        line.account_id = income_acc.id
        
        return super()._post()# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CyberInvoice(models.Model):
    _inherit = "account.move"
    _description = "Cyber Invoice (Kế thừa Account Move)"

    journal_id = fields.Many2one(required=False)

    # ==== LIÊN KẾT ====  
    customer_id = fields.Many2one('res.partner', string='Khách hàng', ondelete='cascade')
    session_id = fields.Many2one('cyber.session', string="Phiên chơi", ondelete='set null')
    transaction_id = fields.Many2one('cyber.transaction', string='Giao dịch liên quan', ondelete='set null')
    account_id = fields.Many2one('cyber.account', string='Tài khoản', ondelete='set null')
    
    authorized_transaction_ids = fields.Many2many(
        'account.payment', 
        string='Authorized Transactions',
        compute='_compute_dummy'
    )
    transaction_count = fields.Integer(string='Transaction Count')

    # ==== THÔNG TIN RIÊNG ====  
    discount_percent = fields.Float(string='Giảm giá (%)', digits=(5, 2), default=0.0)
    surcharge_percent = fields.Float(string='Phụ phí (%)', digits=(5, 2), default=0.0)
    tax_percent = fields.Float(string='Thuế (%)', digits=(5, 2), default=0.0)
    total_cost = fields.Float(string='Tổng chi phí gốc', digits=(10, 2))
    duration = fields.Float(string='Thời lượng (giờ)', compute='_compute_duration', store=True)
    note_cyber = fields.Text(string='Ghi chú thêm')

    # ==== COMPUTE ====  
    @api.depends('total_cost', 'discount_percent', 'surcharge_percent', 'tax_percent')
    def _compute_total_amount(self):
        """Ghi đè logic tính tổng tiền"""
        for rec in self:
            base = rec.total_cost or 0.0
            discount = base * (rec.discount_percent or 0.0) / 100
            surcharge = base * (rec.surcharge_percent or 0.0) / 100
            tax = base * (rec.tax_percent or 0.0) / 100
            rec.amount_total = base - discount + surcharge + tax

    @api.depends('invoice_date', 'session_id.start_time', 'session_id.end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.session_id and rec.session_id.start_time and rec.session_id.end_time:
                rec.duration = (rec.session_id.end_time - rec.session_id.start_time).total_seconds() / 3600.0
            else:
                rec.duration = 0.0

    def _compute_dummy(self):
        for rec in self:
            rec.authorized_transaction_ids = False

    # ==== ONCHANGE: Auto-fill khi chọn session ====
    @api.onchange('session_id')
    def _onchange_session_id(self):
        """
        Khi chọn session, tự động điền invoice lines
        """
        session = self.session_id
        if not session:
            self.customer_id = False
            self.account_id = False
            self.transaction_id = False
            self.total_cost = 0.0
            self.duration = 0.0
            self.invoice_line_ids = [(5, 0, 0)]
            return

        # Kiểm tra session phải đã closed
        if session.state != 'closed':
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

        # Điền transaction liên quan
        self.transaction_id = session.transaction_id or False

        # Điền tổng chi phí và duration
        self.total_cost = session.total_cost or 0.0
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
                'payment_method': 'cash',
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

    # ==== OVERRIDE CREATE ====  
    @api.model
    def create(self, vals):
        """Tự gán sổ nhật ký mặc định nếu chưa có"""
        # Đặt move_type nếu chưa có (out_invoice = hóa đơn bán hàng)
        if not vals.get('move_type'):
            vals['move_type'] = 'out_invoice'
        
        if vals.get('customer_id'):
            vals['partner_id'] = vals.get('customer_id')

        if not vals.get("journal_id"):
            journal = self._get_or_create_sales_journal()
            vals['journal_id'] = journal.id

        # Thêm due date
        if not vals.get('invoice_date_due'):
            from datetime import datetime, timedelta
            vals['invoice_date_due'] = datetime.now().date() + timedelta(days=30)

        return super(CyberInvoice, self).create(vals)

    @api.model
    def default_get(self, fields_list):
        """Đảm bảo khi mở form lần đầu, journal_id đã có"""
        res = super(CyberInvoice, self).default_get(fields_list)
        
        if 'journal_id' in fields_list and not res.get('journal_id'):
            journal = self._get_or_create_sales_journal()
            res['journal_id'] = journal.id
            
        return res

    @api.model
    def _get_or_create_sales_journal(self):
        """Tìm hoặc tạo sales journal"""
        company = self.env.company
        journal = self.env['account.journal'].search([
            ('company_id', '=', company.id),
            ('type', '=', 'sale')
        ], limit=1)

        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'Cyber Sales Journal',
                'code': 'CYBS',
                'type': 'sale',
                'company_id': company.id,
            })
        
        return journal

    def write(self, vals):
        """Update partner_id nếu customer_id thay đổi"""
        if 'customer_id' in vals:
            vals['partner_id'] = vals.get('customer_id')
        return super().write(vals)


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

    @api.model_create_multi
    def create(self, vals_list):
        """
        TỰ ĐỘNG gán account cho tất cả invoice lines
        Tìm account income mặc định, không raise error
        """
        company = self.env.company
        Account = self.env['account.account']
        
        # Tìm account income
        income_acc = Account.search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', company.id),
            ('deprecated', '=', False),
        ], limit=1)
        
        if not income_acc:
            # Fallback: lấy bất kỳ account
            income_acc = Account.search([
                ('company_ids', 'in', company.id),
                ('deprecated', '=', False),
            ], limit=1)
        
        # Gán account cho tất cả lines không có account
        for vals in vals_list:
            if not vals.get('account_id') and income_acc:
                vals['account_id'] = income_acc.id
        
        return super().create(vals_list)