# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerSegment(http.Controller):
#     @http.route('/customer_segment/customer_segment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_segment/customer_segment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_segment.listing', {
#             'root': '/customer_segment/customer_segment',
#             'objects': http.request.env['customer_segment.customer_segment'].search([]),
#         })

#     @http.route('/customer_segment/customer_segment/objects/<model("customer_segment.customer_segment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_segment.object', {
#             'object': obj
#         })

