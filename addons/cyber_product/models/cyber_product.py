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
    type = fields.Selection(related='product_tmpl_id.type', store=True, readonly=False, default='product')
    quant_ids = fields.One2many('cyber.stock.quant', 'cyber_product_id', string="Tồn kho")
    # Phân loại sản phẩm
    is_machine = fields.Boolean(string="Là máy dịch vụ", default=False)
    is_good = fields.Boolean(string="Là hàng hóa", default=False)
    is_component = fields.Boolean(string="Là linh kiện", default=False)
    quantity_init = fields.Float(
    string="Số lượng ban đầu",
    default=0.0,
    help="Chỉ nhập khi tạo sản phẩm mới. Sau khi lưu, hệ thống sẽ tự tạo phiếu nhập kho tương ứng.")

    # Thông tin chung bổ sung: Thoi gian Tao & Chinh sua & TTHD
    create_at = fields.Datetime(string="Ngày tạo", default=fields.Datetime.now)
    update_at = fields.Datetime(string="Cập nhật lần cuối", default=fields.Datetime.now)
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
        ('broken', 'Hỏng')
    ], string="Trạng thái máy", default='active')
    machine_using_status = fields.Selection([
        ('offline', 'Ngoại tuyến'),
        ('in_use', 'Đang sử dụng')
    ], string="Trạng thái hoạt động", default='offline')
    supplier_service_id = fields.Many2one(
        "res.partner",
        string="Nhà cung cấp",
        domain=[('supplier_type', '=', 'service')],
        context={'default_is_supplier_cyber': True, 'default_supplier_type': 'service'},
        ondelete='set null'
    )
    location = fields.Char(string="Vị trí đặt máy")
    price_per_hour = fields.Float(string="Giá dịch vụ (VNĐ/giờ)")
    usage_hours = fields.Integer(string="Tổng giờ đã sử dụng")
    last_maintenance = fields.Date(string="Ngày bảo trì gần nhất")
    next_maintenance = fields.Date(string="Ngày bảo trì tiếp theo")
    serial_number = fields.Char(string="Số seri / mã định danh")
    ip_address = fields.Char(string="Địa chỉ IP")

    # Chỉ số tổng quan máy----------------------------
    total_ratio = fields.Char()
    offline_ratio = fields.Char()
    in_use_ratio = fields.Char()
    maintenance_ratio = fields.Char()

    def compute_ratios(self):
        machines = self.env['cyber.product'].search([('is_machine','=',True)])
        total = len(machines)
        active = len([m for m in machines if m.machine_status == 'active'])
        maintenance = len([m for m in machines if m.machine_status == 'maintenance'])
        offline = len([m for m in machines if m.machine_using_status == 'offline'])
        in_use = len([m for m in machines if m.machine_using_status == 'in_use'])

        self.total_ratio = f"{active}/{total}" if total else "0/0"
        self.maintenance_ratio = f"{maintenance}/{total}" if total else "0/0"
        self.offline_ratio = f"{offline}/{active}" if active else "0/0"
        self.in_use_ratio = f"{in_use}/{active}" if active else "0/0"
    #--------------------------------------------



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
    ], string="Trạng thái hàng hóa", compute="_compute_good_status", store=True, readonly=True)

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
    ], string="Trạng thái linh kiện", compute="_compute_good_status", store=True, readonly=True)

    # Ràng buộc chọn 1/3 loại sản phẩm
    @api.constrains('is_machine', 'is_good', 'is_component')
    def _check_product_type_flags(self):
        for record in self:
            flags = [record.is_machine, record.is_good, record.is_component]
            if sum(flags) > 1:
                raise ValidationError("Chỉ được chọn một loại: Service, Good hoặc Component.")
            if sum(flags) == 0:
                raise ValidationError("Phải chọn một loại sản phẩm (Service, Good hoặc Component).")
    
   
    
    def write(self, vals):
        # --- Không cập nhật update_at nếu chỉ thay đổi quantity_init ---
        ignore_fields = {'quantity_init'}
        if not all(k in ignore_fields for k in vals.keys()):
            vals['update_at'] = fields.Datetime.now()

        return super(CyberProduct, self).write(vals)

    # --- Không cho sửa lại sau khi tạo ---
    @api.onchange('id')
    def _onchange_id_disable_quantity_init(self):
        if self.id:
            self.quantity_init = 0.0
    
    overview_button = fields.Boolean(string="Tổng quan máy", compute="_compute_overview_button")

    @api.depends()
    def _compute_overview_button(self):
        for rec in self:
            rec.overview_button = True

    def button_show_overview(self):
        self.compute_ratios()
        return {
            'name': 'Tổng quan máy',
            'type': 'ir.actions.act_window',
            'res_model': 'cyber.product',
            'view_mode': 'form',
            'view_id': self.env.ref('cyber_product.view_cyber_service_overview_form').id,
            'target': 'new',
            'domain': [('id', 'in', self.ids)],
        }
    
    # --- Nút mở danh sách stock.quant cho sản phẩm này ---
    def action_view_quants(self):
        self.ensure_one()
        variant = self.product_tmpl_id.product_variant_id
        domain = [('product_id', '=', variant.id)] if variant else [('id', '=', False)]
        return {
            'name': 'Tồn kho (Quants)',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'domain': domain,
            'target': 'current',
        }

    # --- Nút mở lịch sử move (phiếu nhập/xuất) cho sản phẩm này ---
    def action_view_moves(self):
        self.ensure_one()
        variant = self.product_tmpl_id.product_variant_id
        domain = [('product_id', '=', variant.id)] if variant else [('id', '=', False)]
        return {
            'name': 'Lịch sử nhập/xuất',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_mode': 'tree,form',
            'domain': domain,
            'target': 'current',
        }
    
    @api.model
    def create(self, vals):
        # 0. Nếu supplier_* được truyền là tên (string) -> tạo partner trước để gán vào vals
        if vals.get('supplier_service_id') and isinstance(vals.get('supplier_service_id'), str):
            vals['supplier_service_id'] = self._prepare_supplier_partner(vals.get('supplier_service_id'), 'service')
        if vals.get('supplier_good_id') and isinstance(vals.get('supplier_good_id'), str):
            vals['supplier_good_id'] = self._prepare_supplier_partner(vals.get('supplier_good_id'), 'good')
        if vals.get('supplier_component_id') and isinstance(vals.get('supplier_component_id'), str):
            vals['supplier_component_id'] = self._prepare_supplier_partner(vals.get('supplier_component_id'), 'component')

        # 1. Tạo product.template nếu chưa có
        if not vals.get('product_tmpl_id'):
            tmpl_vals = {
                'name': vals.get('name', 'Sản phẩm mới'),
                'list_price': vals.get('list_price', 0.0),
                'standard_price': vals.get('standard_price', 0.0),
                'barcode': vals.get('barcode', False),
                'type': 'good',
            }
            tmpl = self.env['product.template'].create(tmpl_vals)
            vals['product_tmpl_id'] = tmpl.id

        # 2. Ghi timestamp tạo/sửa nội bộ (riêng cho product info)
        vals['create_at'] = fields.Datetime.now()
        vals['update_at'] = fields.Datetime.now()

        # 3. Tạo CyberProduct
        product = super(CyberProduct, self).create(vals)

        # 4. Nếu có quantity_init => tạo 1 stock.move (phiếu nhập) để cập nhật tồn kho chuẩn
        quantity_init = vals.get('quantity_init', 0.0)
        if quantity_init > 0:
            variant = product.product_tmpl_id.product_variant_id
            if not variant:
                raise ValidationError("Không thể xác định biến thể sản phẩm (variant).")

            # Tạo record trong cyber.stock.quant
            self.env['cyber.stock.quant'].create({
                'cyber_product_id': product.id,
                'product_id': variant.id,
                'quantity': quantity_init,
                'in_date': fields.Datetime.now(),
            })
        return product

    def write(self, vals):
        # Không cập nhật update_at nếu chỉ thay đổi quantity_init
        ignore_fields = {'quantity_init'}
        if not all(k in ignore_fields for k in vals.keys()):
            vals['update_at'] = fields.Datetime.now()
        return super(CyberProduct, self).write(vals)

    def unlink(self):
        # Xóa product.template liên quan sau khi xóa cyber.product
        templates_to_delete = self.mapped('product_tmpl_id')
        res = super(CyberProduct, self).unlink()
        if templates_to_delete:
            templates_to_delete.unlink()
        return res

    # inverse suppliers: tạo partner nếu người dùng nhập trực tiếp record không có id (rare)
    def _inverse_supplier_service_id(self):
        for record in self:
            if record.supplier_service_id and isinstance(record.supplier_service_id, str):
                pid = self._prepare_supplier_partner(record.supplier_service_id, 'service')
                record.supplier_service_id = pid

    def _inverse_supplier_good_id(self):
        for record in self:
            if record.supplier_good_id and isinstance(record.supplier_good_id, str):
                pid = self._prepare_supplier_partner(record.supplier_good_id, 'good')
                record.supplier_good_id = pid

    def _inverse_supplier_component_id(self):
        for record in self:
            if record.supplier_component_id and isinstance(record.supplier_component_id, str):
                pid = self._prepare_supplier_partner(record.supplier_component_id, 'component')
                record.supplier_component_id = pid
    
    def _prepare_supplier_partner(self, name, supplier_type):
        """Tạo partner supplier cơ bản, trả về id partner."""
        if not name:
            return False
        partner = self.env['res.partner'].create({
            'name': name,
            'is_supplier_cyber': True,
            'supplier_type': supplier_type,
        })
        return partner.id
    
    @api.onchange('product_tmpl_id')
    def _onchange_force_type(self):
        # Ép type luôn là 'product' nếu user chọn template khác
        for rec in self:
            if rec.product_tmpl_id and rec.product_tmpl_id.type != 'product':
                rec.product_tmpl_id.type = 'product'