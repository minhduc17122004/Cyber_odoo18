# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CyberInvoice(models.Model):
    _inherit = "account.move"
    _description = "Cyber Invoice (Kế thừa Account Move)"


    # Bỏ required=True để không ép buộc form
    journal_id = fields.Many2one(required=False)

    # ==== LIÊN KẾT ====
    customer_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        required=True,
        ondelete='cascade'
    )
    session_id = fields.Many2one(
        'cyber.session',
        string="Phiên chơi",
        ondelete='set null'
    )
    transaction_id = fields.Many2one(
        'cyber.transaction',
        string='Giao dịch liên quan',
        ondelete='set null'
    )


    # ==== LIÊN KẾT ====  
    customer_id = fields.Many2one('cyber.customer', string='Khách hàng', ondelete='cascade')
    session_id = fields.Many2one('cyber.session', string="Phiên chơi", ondelete='set null')
    transaction_id = fields.Many2one('cyber.transaction', string='Giao dịch liên quan', ondelete='set null')
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

    # ==== OVERRIDE CREATE ====  
    @api.model
    def create(self, vals):
        """Tự gán sổ nhật ký mặc định nếu chưa có"""
        if not vals.get("journal_id"):
            # tìm 1 journal bất kỳ có type = 'general'
            journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
            if not journal:
                # Nếu chưa có journal nào, tạo tạm 1 cái
                journal = self.env['account.journal'].create({
                    'name': 'Cyber Default Journal',
                    'code': 'CYB',
                    'type': 'general',
                    'company_id': self.env.company.id,
                })
            vals['journal_id'] = journal.id
        return super(CyberInvoice, self).create(vals)
    @api.model
    def default_get(self, fields_list):
        """Đảm bảo khi mở form lần đầu, journal_id đã có để tránh lỗi default journal not found."""
        res = super(CyberInvoice, self).default_get(fields_list)
        # Nếu form/flow cần journal_id và chưa có, ta ưu tiên tìm journal 'general' của company
        if 'journal_id' in fields_list and not res.get('journal_id'):
            company_id = self.env.company.id
            journal = self.env['account.journal'].search(
                [('company_id', '=', company_id), ('type', '=', 'general')], limit=1)
            if not journal:
                # Tạo tạm 1 journal tránh lỗi (như bạn muốn, không cần user thao tác)
                journal = self.env['account.journal'].create({
                    'name': 'Cyber Default Journal',
                    'code': 'CYB',
                    'type': 'general',
                    'company_id': company_id,
                })
            res['journal_id'] = journal.id
        return res
