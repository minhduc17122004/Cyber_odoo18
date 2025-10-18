from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CyberProduct(models.Model):
    _name = "cyber.product"
    _inherits = {'product.template': 'product_tmpl_id'}
    product_tmpl_id = fields.Many2one('product.template', required=True, ondelete='cascade')

    #Phân loại sản phẩm
    is_machine = fields.Boolean(string="Là máy dịch vụ", default=False)
    is_good = fields.Boolean(string="Là hàng hóa", default=False)
    is_component = fields.Boolean(string="Là linh kiện", default=False)

    #Thông tin chung
    name = fields.Char(string="Tên sản phẩm / thiết bị", required=True)
    uom_id = fields.Many2one('uom.uom', string="Đơn vị tính", required=True)
    list_price = fields.Float(string="Giá bán (VNĐ)")
    cost_price = fields.Float(string="Giá vốn (VNĐ)")
    quantity = fields.Float(string="Số lượng tồn", default=0.0)
    supplier_id = fields.Many2one("res.partner", string="Nhà cung cấp")
    is_active = fields.Boolean(string="Đang hoạt động", default=True)
    barcode = fields.Char(string="Mã vạch / định danh")

    #Service
    service_category_id = fields.Many2one("product.category", string="Loại máy")
    machine_status = fields.Selection([
        ('active', 'Hoạt động'),
        ('maintenance', 'Bảo trì'),
        ('offline', 'Ngoại tuyến'),
        ('in_use', 'Đang sử dụng')
    ], string="Trạng thái máy", default='active')
    machine_spec = fields.Text(string="Cấu hình phần cứng")
    location = fields.Char(string="Vị trí đặt máy")
    price_per_hour = fields.Float(string="Giá dịch vụ (VNĐ/giờ)")
    usage_hours = fields.Integer(string="Tổng giờ đã sử dụng")
    last_maintenance = fields.Date(string="Ngày bảo trì gần nhất")
    next_maintenance = fields.Date(string="Ngày bảo trì tiếp theo")
    serial_number = fields.Char(string="Số seri / mã định danh")
    ip_address = fields.Char(string="Địa chỉ IP")

    #Good
    good_category_id = fields.Many2one("product.category", string="Danh mục hàng hóa")
    tax_percent = fields.Float(string="Thuế VAT (%)")
    expiry_date = fields.Date(string="Ngày hết hạn")
    good_status = fields.Selection([
        ('available', 'Có sẵn'),
        ('running out', 'Gần hết'),
        ('no more', 'Hết')
    ], string="Trạng thái linh kiện", default='available')

    #Component
    component_category_id = fields.Many2one("product.category", string="Loại linh kiện")
    compatible_machine = fields.Text(string="Tương thích với máy")
    lifetime_hours = fields.Integer(string="Tuổi thọ (giờ)")
    component_status = fields.Selection([
        ('available', 'Có sẵn'),
        ('running out', 'Gần hết'),
        ('no more', 'Hết')
    ], string="Trạng thái linh kiện", default='available')

    #Ràng buộc chọn 1/3
    @api.constrains('is_machine', 'is_good', 'is_component')
    def _check_product_type_flags(self):
        for record in self:
            flags = [record.is_machine, record.is_good, record.is_component]
            if sum(flags) > 1:
                raise ValidationError("Chỉ được chọn một loại: Service, Good hoặc Component.")
            if sum(flags) == 0:
                raise ValidationError("Phải chọn một loại sản phẩm (Service, Good hoặc Component).")
