from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CyberStockQuant(models.Model):
    _name = 'cyber.stock.quant'
    _description = 'Cyber Stock Quant (Custom Warehouse Tracker)'

    cyber_product_id = fields.Many2one('cyber.product', string='Sản phẩm Cyber', required=True)
    product_id = fields.Many2one('product.template', string='Sản phẩm gốc')
    location_id = fields.Many2one(
        'stock.location',
        string='Địa điểm tồn kho',
        required=False,
        domain=[('usage', 'in', ['internal', 'transit'])],
        help="Kho hoặc vị trí vật lý nơi sản phẩm này đang được lưu trữ."
    )
    quantity = fields.Float(string='Số lượng tồn', default=0.0)
    reserved_quantity = fields.Float(string='Số lượng đã đặt', default=0.0)
    in_date = fields.Datetime(string='Ngày nhập')
    write_uid = fields.Many2one('res.users', string='Người cập nhật', readonly=True)
    write_date = fields.Datetime(string='Ngày cập nhật', readonly=True)
    note = fields.Text(string='Ghi chú')

    @api.model
    def create_initial_stock(self, product, qty):
        """Tạo bản ghi tồn kho ban đầu"""
        quant = self.create({
            'product_id': product.id,
            'quantity': qty,
        })
        return quant

    @api.constrains('quantity')
    def _check_positive(self):
        for rec in self:
            if rec.quantity < 0:
                raise ValidationError("Số lượng tồn không được âm.")

    def increase_stock(self, qty):
        self.ensure_one()
        self.quantity += qty
        self.in_date = fields.Datetime.now()

    def decrease_stock(self, qty):
        self.ensure_one()
        if qty > self.quantity:
            raise ValidationError("Không đủ tồn kho để xuất.")
        self.quantity -= qty
        self.in_date = fields.Datetime.now()

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs.mapped('cyber_product_id')._compute_good_status()
        return recs

    def write(self, vals):
        res = super().write(vals)
        self.mapped('cyber_product_id')._compute_good_status()
        return res

    def unlink(self):
        products = self.mapped('cyber_product_id')
        res = super().unlink()
        products._compute_good_status()
        return res