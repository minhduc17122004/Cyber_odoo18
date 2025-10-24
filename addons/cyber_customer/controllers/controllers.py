# -*- coding: utf-8 -*-
# from odoo import http


# class CyberCustomer(http.Controller):
#     @http.route('/cyber_customer/cyber_customer', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cyber_customer/cyber_customer/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cyber_customer.listing', {
#             'root': '/cyber_customer/cyber_customer',
#             'objects': http.request.env['cyber_customer.cyber_customer'].search([]),
#         })

#     @http.route('/cyber_customer/cyber_customer/objects/<model("cyber_customer.cyber_customer"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cyber_customer.object', {
#             'object': obj
#         })

