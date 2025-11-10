# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CyberInvoice(models.Model):
    _name = "cyber.invoice"
    _description = "Hóa đơn thanh toán"
    _order = "invoice_date desc"

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

    # ==== THÔNG TIN HÓA ĐƠN ====
    total_cost = fields.Float(string='Tổng chi phí', digits=(10, 2), required=True)

    # chuyển sang phần trăm (%)
    discount_percent = fields.Float(string='Giảm giá (%)', digits=(5, 2), default=0.0)
    surcharge_percent = fields.Float(string='Phụ phí (%)', digits=(5, 2), default=0.0)
    tax_percent = fields.Float(string='Thuế (%)', digits=(5, 2), default=0.0)

    total_amount = fields.Float(
        string='Tổng tiền thanh toán',
        digits=(10, 2),
        compute='_compute_total_amount',
        store=True
    )

    invoice_date = fields.Datetime(string='Ngày lập hóa đơn', default=fields.Datetime.now, required=True)
    start_time = fields.Datetime(string='Bắt đầu')
    end_time = fields.Datetime(string='Kết thúc')
    duration = fields.Float(string='Thời lượng (giờ)', compute='_compute_duration', store=True)

    note = fields.Text(string='Ghi chú thêm')

    # ==== TÍNH TOÁN ====
    @api.depends('total_cost', 'discount_percent', 'surcharge_percent', 'tax_percent')
    def _compute_total_amount(self):
        for rec in self:
            base = rec.total_cost or 0
            discount = base * (rec.discount_percent or 0) / 100
            surcharge = base * (rec.surcharge_percent or 0) / 100
            tax = base * (rec.tax_percent or 0) / 100
            rec.total_amount = base - discount + surcharge + tax

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                rec.duration = (rec.end_time - rec.start_time).total_seconds() / 3600.0
            else:
                rec.duration = 0.0

    # ==== RÀNG BUỘC ====
    @api.constrains('total_cost')
    def _check_total_cost(self):
        for rec in self:
            if rec.total_cost <= 0:
                raise ValidationError(_("Tổng chi phí phải lớn hơn 0."))

    # @api.onchange('session_id')
    # def _onchange_session_id(self):
    #     """Tự động lấy giao dịch liên quan khi chọn session"""
    #     for rec in self:
    #         if rec.session_id and rec.session_id.transaction_id:
    #             rec.transaction_id = rec.session_id.transaction_id
    #         else:
    #             rec.transaction_id = False
