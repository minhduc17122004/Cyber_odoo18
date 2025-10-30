# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CyberInvoice(models.Model):
    _name = "cyber.invoice"
    _description = "Hóa đơn thanh toán"
    _order = "invoice_date desc"

    # ==== LIÊN KẾT ====
    customer_id = fields.Many2one(
        'cyber.customer',
        string='Khách hàng',
        required=True,
        ondelete='cascade'
    )

    transaction_id = fields.Many2one(
        'cyber.transaction',
        string='Giao dịch liên quan',
        ondelete='set null'
    )

    # ==== THÔNG TIN HÓA ĐƠN ====
    total_cost = fields.Float(string='Tổng chi phí', digits=(10, 2), required=True)
    discount_amount = fields.Float(string='Giảm giá', digits=(10, 2))
    surcharge = fields.Float(string='Phụ phí', digits=(10, 2))
    tax_amount = fields.Float(string='Thuế', digits=(10, 2))
    total_amount = fields.Float(string='Tổng tiền thanh toán', digits=(10, 2), compute='_compute_total_amount', store=True)

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='draft', required=True)

    invoice_date = fields.Datetime(string='Ngày lập hóa đơn', default=fields.Datetime.now, required=True)
    start_time = fields.Datetime(string='Bắt đầu')
    end_time = fields.Datetime(string='Kết thúc')
    duration = fields.Float(string='Thời lượng (giờ)', compute='_compute_duration', store=True)

    note = fields.Text(string='Ghi chú thêm')

    # ==== TÍNH TOÁN TỰ ĐỘNG ====
    @api.depends('total_cost', 'discount_amount', 'surcharge', 'tax_amount')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = (rec.total_cost or 0) - (rec.discount_amount or 0) + (rec.surcharge or 0) + (rec.tax_amount or 0)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                rec.duration = (rec.end_time - rec.start_time).total_seconds() / 3600.0
            else:
                rec.duration = 0.0

    # ==== RÀNG BUỘC DỮ LIỆU ====
    @api.constrains('total_cost')
    def _check_total_cost(self):
        for rec in self:
            if rec.total_cost <= 0:
                raise ValidationError(_("Tổng chi phí phải lớn hơn 0."))

    # ==== HÀNH ĐỘNG ====
    def action_confirm(self):
        """Xác nhận hóa đơn"""
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Chỉ có thể xác nhận hóa đơn ở trạng thái 'Nháp'."))
            rec.state = 'confirmed'

    def action_pay(self):
        """Đánh dấu hóa đơn đã thanh toán"""
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError(_("Chỉ có thể thanh toán hóa đơn sau khi đã xác nhận."))
            rec.state = 'paid'

    def action_cancel(self):
        """Hủy hóa đơn"""
        for rec in self:
            if rec.state == 'paid':
                raise ValidationError(_("Không thể hủy hóa đơn đã thanh toán."))
            rec.state = 'cancelled'
