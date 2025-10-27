# -*- coding: utf-8 -*-
from odoo import models, fields

class CustomerSegment(models.Model):
    _name = 'customer.segment'
    _description = 'Customer Segment'

    segment_name = fields.Char(string='Tên phân khúc', required=True)
    discount_rate = fields.Float(string='Tỷ lệ chiết khấu (%)', required=True)
    is_active = fields.Boolean(string='Trạng thái', default=True)
    conditions_time = fields.Float(string='Thời gian chơi tối thiểu (giờ)', required=True, default=0.0)

    # customer_ids = fields.One2many(
    #     'cyber.customer',
    #     'segment_id',
    #     string='Khách hàng thuộc phân khúc'
    # )



