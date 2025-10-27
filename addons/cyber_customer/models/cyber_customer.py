# -*- coding: utf-8 -*-
from odoo import api, fields, models

class CyberCustomer(models.Model):
    _name = "cyber.customer"
    _inherits = {"res.partner": "partner_id"}   
    _description = "Cyber Customer"

    partner_id = fields.Many2one(
        "res.partner", 
        string="Partner", 
        required=True, 
        ondelete="cascade",
        auto_join=True
    )
    dob = fields.Date(string="Date of Birth")
    join_date = fields.Date(string="Join Date", default=fields.Date.context_today)
    total_play_time = fields.Float(string="Total Play Time (hours)", default=0.0)
    total_spent = fields.Float(string="Total Spent", digits=(10, 2), default=0.0)
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now, readonly=True)
    updated_at = fields.Datetime(string="Updated At", default=fields.Datetime.now, readonly=True)

    segment_id = fields.Many2one(
        'customer.segment',
        string='Phân khúc khách hàng',
        ondelete='set null'
    )
    segment_name = fields.Char(related="segment_id.segment_name", store=True)

    # account_ids = fields.One2many(
    #     'cyber.account',
    #     'customer_id',
    #     string='Accounts'
    # )

    @api.model
    def create(self, vals):
        """Khi tạo mới khách hàng:
        - Nếu chưa có segment_id: tự động gán phân khúc theo total_play_time
        - Nếu đã có segment_id: giữ nguyên (không ghi đè)
        """
        customer = super(CyberCustomer, self).create(vals)

        # Nếu chưa có phân khúc được chọn -> tự động tính
        if not customer.segment_id:
            segment = self.env['customer.segment'].search(
                [
                    ('conditions_time', '<=', customer.total_play_time),
                    ('is_active', '=', True)
                ],
                order='conditions_time desc',
                limit=1
            )
            if segment:
                customer.segment_id = segment.id

        return customer

    def write(self, vals):
        """Khi cập nhật giờ chơi -> tự động cập nhật phân khúc"""
        res = super(CyberCustomer, self).write(vals)

        if 'total_play_time' in vals:
            for customer in self:
                segment = self.env['customer.segment'].search(
                    [
                        ('conditions_time', '<=', customer.total_play_time),
                        ('is_active', '=', True)
                    ],
                    order='conditions_time desc',
                    limit=1
                )
                if segment and customer.segment_id != segment:
                    customer.segment_id = segment.id

        return res

    def _calculate_totals(self):
        """Tính tổng giờ chơi và tổng tiền của tất cả account"""
        for customer in self:
            accounts = self.env['cyber.account'].search([
                ('customer_id', '=', customer.id),
                ('state', '=', 'active')
            ])
            customer.total_play_time = sum(acc.play_time_total for acc in accounts)
            customer.total_spent = sum(acc.total_spent for acc in accounts)
