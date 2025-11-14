from odoo import models, fields

class CyberStockQuant(models.Model):
    _inherit = 'stock.quant'

    cyber_product_id = fields.Many2one('product.template', string="Sản phẩm Cyber")
