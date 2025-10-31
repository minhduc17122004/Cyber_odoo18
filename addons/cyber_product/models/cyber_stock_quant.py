from odoo import models, fields, api

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
    move_ids = fields.One2many('stock.move', 'cyber_quant_id', string='Liên kết Move')

    @api.model
    def create_initial_stock(self, product, qty):
        """Tạo bản ghi tồn kho ban đầu"""
        quant = self.create({
            'product_id': product.id,
            'quantity': qty,
        })
        return quant

    def increase_stock(self, qty):
        self.quantity += qty
        self.last_update = fields.Datetime.now()

    def decrease_stock(self, qty):
        if qty > self.quantity:
            raise ValueError("Không đủ hàng tồn để xuất!")
        self.quantity -= qty
        self.last_update = fields.Datetime.now()
