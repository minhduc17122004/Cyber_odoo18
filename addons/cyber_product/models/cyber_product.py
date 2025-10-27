from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CyberProduct(models.Model):
    _name = "cyber.product"
    _description = "Cyber Product"
    _inherits = {'product.template': 'product_tmpl_id'}

    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Sản phẩm gốc",
        required=True,
        ondelete='cascade'
    )

    # Phân loại sản phẩm
    is_machine = fields.Boolean(string="Là máy dịch vụ", default=False)
    is_good = fields.Boolean(string="Là hàng hóa", default=False)
    is_component = fields.Boolean(string="Là linh kiện", default=False)

    # Thông tin chung bổ sung
    quantity = fields.Float(string="Số lượng tồn", default=0.0)
    is_active = fields.Boolean(string="Đang hoạt động", default=True)

    # Service fields
    service_category_id = fields.Many2one(
        "product.category",
        string="Loại máy",
        domain=[('category_type', '=', 'service')],
        inverse="_inverse_supplier_service_id"
    )
    machine_status = fields.Selection([
        ('active', 'Hoạt động'),
        ('maintenance', 'Bảo trì'),
        ('offline', 'Ngoại tuyến'),
        ('in_use', 'Đang sử dụng')
    ], string="Trạng thái máy", default='active')
    supplier_service_id = fields.Many2one(
        "res.partner",
        string="Nhà cung cấp",
        domain=[('supplier_type', '=', 'service')],
        context={'default_is_supplier_cyber': True, 'default_supplier_type': 'service'},
        ondelete='set null'
    )
    machine_spec = fields.Text(string="Cấu hình phần cứng")
    location = fields.Char(string="Vị trí đặt máy")
    price_per_hour = fields.Float(string="Giá dịch vụ (VNĐ/giờ)")
    usage_hours = fields.Integer(string="Tổng giờ đã sử dụng")
    last_maintenance = fields.Date(string="Ngày bảo trì gần nhất")
    next_maintenance = fields.Date(string="Ngày bảo trì tiếp theo")
    serial_number = fields.Char(string="Số seri / mã định danh")
    ip_address = fields.Char(string="Địa chỉ IP")

    # Good fields
    good_category_id = fields.Many2one(
        "product.category",
        string="Danh mục hàng hóa",
        domain=[('category_type', '=', 'good')]
    )
    uom_good_id = fields.Many2one(
        "cyber.uom",
        string="Đơn vị tính hàng hóa",
        domain=[('uom_type', '=', 'good')]
    )
    supplier_good_id = fields.Many2one(
        "res.partner",
        string="Nhà cung cấp",
        domain=[('supplier_type', '=', 'good')],
        context={'default_is_supplier_cyber': True, 'default_supplier_type': 'good'},
        ondelete='set null'
    )
    tax_percent = fields.Float(string="Thuế VAT (%)")
    expiry_date = fields.Date(string="Ngày hết hạn")
    good_status = fields.Selection([
        ('available', 'Có sẵn'),
        ('running out', 'Gần hết'),
        ('no more', 'Hết')
    ], string="Trạng thái hàng hóa", default='available')

    # Component fields
    component_category_id = fields.Many2one(
        "product.category",
        string="Loại linh kiện",
        domain=[('category_type', '=', 'component')]
    )
    uom_component_id = fields.Many2one(
        "cyber.uom",
        string="Đơn vị tính linh kiện",
        domain=[('uom_type', '=', 'component')]
    )
    supplier_component_id = fields.Many2one(
        "res.partner",
        string="Nhà cung cấp",
        domain=[('supplier_type', '=', 'component')],
        context={'default_is_supplier_cyber': True, 'default_supplier_type': 'component'},
        ondelete='set null'
    )
    compatible_machine = fields.Text(string="Tương thích với máy")
    lifetime_hours = fields.Integer(string="Tuổi thọ (giờ)")
    component_status = fields.Selection([
        ('available', 'Có sẵn'),
        ('running out', 'Gần hết'),
        ('no more', 'Hết')
    ], string="Trạng thái linh kiện", default='available')

    # Ràng buộc chọn 1/3 loại sản phẩm
    @api.constrains('is_machine', 'is_good', 'is_component')
    def _check_product_type_flags(self):
        for record in self:
            flags = [record.is_machine, record.is_good, record.is_component]
            if sum(flags) > 1:
                raise ValidationError("Chỉ được chọn một loại: Service, Good hoặc Component.")
            if sum(flags) == 0:
                raise ValidationError("Phải chọn một loại sản phẩm (Service, Good hoặc Component).")
            
    @api.model
    def create(self, vals):
        # 1. Tạo product_tmpl_id nếu chưa có
        if not vals.get('product_tmpl_id'):
            tmpl_vals = {
                'name': vals.get('name', 'Sản phẩm mới'),
                'list_price': vals.get('list_price', 0.0),
                'standard_price': vals.get('cost_price', 0.0),
                'barcode': vals.get('barcode', False),
            }
            tmpl = self.env['product.template'].create(tmpl_vals)
            vals['product_tmpl_id'] = tmpl.id

        # 2. Tạo partner tự động cho Service
        if vals.get('supplier_service_id') and isinstance(vals['supplier_service_id'], str):
            partner_vals = {
                'name': vals['supplier_service_id'],
                'is_supplier_cyber': True,
                'supplier_type': 'service'
            }
            partner = self.env['res.partner'].create(partner_vals)
            vals['supplier_service_id'] = partner.id

        # 3. Tạo partner tự động cho Good
        if vals.get('supplier_good_id') and isinstance(vals['supplier_good_id'], str):
            partner_vals = {
                'name': vals['supplier_good_id'],
                'is_supplier_cyber': True,
                'supplier_type': 'good'
            }
            partner = self.env['res.partner'].create(partner_vals)
            vals['supplier_good_id'] = partner.id

        # 4. Tạo partner tự động cho Component
        if vals.get('supplier_component_id') and isinstance(vals['supplier_component_id'], str):
            partner_vals = {
                'name': vals['supplier_component_id'],
                'is_supplier_cyber': True,
                'supplier_type': 'component'
            }
            partner = self.env['res.partner'].create(partner_vals)
            vals['supplier_component_id'] = partner.id

        return super(CyberProduct, self).create(vals)
    
    def _inverse_supplier_service_id(self):
        for record in self:
            if record.supplier_service_id and not record.supplier_service_id.id:
                partner = self.env['res.partner'].create({
                    'name': record.supplier_service_id.name,
                    'supplier_type': 'service',
                    'is_supplier_cyber': True
                })
                record.supplier_service_id = partner.id

    def _inverse_supplier_good_id(self):
        for record in self:
            if record.supplier_good_id and not record.supplier_good_id.id:
                partner = self.env['res.partner'].create({
                    'name': record.supplier_good_id.name,
                    'supplier_type': 'good',
                    'is_supplier_cyber': True
                })
                record.supplier_good_id = partner.id

    def _inverse_supplier_component_id(self):
        for record in self:
            if record.supplier_component_id and not record.supplier_component_id.id:
                partner = self.env['res.partner'].create({
                    'name': record.supplier_component_id.name,
                    'supplier_type': 'component',
                    'is_supplier_cyber': True
                })
                record.supplier_component_id = partner.id