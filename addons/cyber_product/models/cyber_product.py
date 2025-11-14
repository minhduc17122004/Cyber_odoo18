from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CyberProduct(models.Model):
    _inherit = 'product.template'
    
    # ============ PHÂN LOẠI SẢN PHẨM ============
    is_machine = fields.Boolean(string="Là máy dịch vụ", default=False)
    is_good = fields.Boolean(string="Là hàng hóa", default=False)
    is_component = fields.Boolean(string="Là linh kiện", default=False)
    
    is_active = fields.Boolean(string="Đang hoạt động", default=True)
    
    # ============ SERVICE/MACHINE FIELDS ============
    service_category_id = fields.Many2one(
        "product.category",
        string="Loại máy",
        domain=[('category_type', '=', 'service')]
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
    
    location = fields.Char(string="Vị trí đặt máy")
    usage_hours = fields.Integer(string="Tổng giờ đã sử dụng", default=0)
    last_maintenance = fields.Date(string="Ngày bảo trì gần nhất")
    next_maintenance = fields.Date(string="Ngày bảo trì tiếp theo")
    ip_address = fields.Char(string="Địa chỉ IP")
    
    # ============ GOOD FIELDS ============
    good_category_id = fields.Many2one(
        "product.category",
        string="Danh mục hàng hóa",
        domain=[('category_type', '=', 'good')]
    )
    uom_good_id = fields.Many2one(
        "uom.uom",
        string="Đơn vị tính hàng hóa",
        domain=[('uom_type', '=', 'good')]
    )
    supplier_good_id = fields.Many2one(
        "res.partner",
        string="Nhà cung cấp hàng hóa",
        domain=[('supplier_type', '=', 'good')],
        context={'default_is_supplier_cyber': True, 'default_supplier_type': 'good'},
        ondelete='set null'
    )
    tax_percent = fields.Float(string="Thuế VAT (%)", default=0.0)
    expiry_date = fields.Date(string="Ngày hết hạn")
    min_stock_good = fields.Float(
        string="Tồn kho tối thiểu",
        default=0.0,
        help="Nếu tồn kho nhỏ hơn hoặc bằng mức này => Cảnh báo sắp hết."
    )
    good_status = fields.Selection([
        ('available', 'Có sẵn'),
        ('running_out', 'Gần hết'),
        ('no_more', 'Hết')
    ], string="Trạng thái hàng hóa", compute="_compute_good_status", store=True)
    
    # ============ COMPONENT FIELDS ============
    component_category_id = fields.Many2one(
        "product.category",
        string="Loại linh kiện",
        domain=[('category_type', '=', 'component')]
    )
    uom_component_id = fields.Many2one(
        "uom.uom",
        string="Đơn vị tính linh kiện",
        domain=[('uom_type', '=', 'component')]
    )
    supplier_component_id = fields.Many2one(
        "res.partner",
        string="Nhà cung cấp linh kiện",
        domain=[('supplier_type', '=', 'component')],
        context={'default_is_supplier_cyber': True, 'default_supplier_type': 'component'},
        ondelete='set null'
    )
    lifetime_hours = fields.Integer(string="Tuổi thọ (giờ)", default=0)
    min_stock_component = fields.Float(
        string="Tồn kho tối thiểu",
        default=0.0,
        help="Nếu tồn kho nhỏ hơn hoặc bằng mức này => Cảnh báo sắp hết."
    )
    component_status = fields.Selection([
        ('available', 'Có sẵn'),
        ('running_out', 'Gần hết'),
        ('no_more', 'Hết')
    ], string="Trạng thái linh kiện", compute="_compute_component_status", store=True)
    
    # ============ CONSTRAINTS ============
    @api.constrains('is_machine', 'is_good', 'is_component')
    def _check_product_type_flags(self):
        """Ràng buộc: chỉ được chọn 1 trong 3 loại sản phẩm"""
        for record in self:
            flags = [record.is_machine, record.is_good, record.is_component]
            count = sum(flags)
            if count > 1:
                raise ValidationError("Chỉ được chọn một loại: Service, Good hoặc Component.")
            if count == 0:
                raise ValidationError("Phải chọn một loại sản phẩm (Service, Good hoặc Component).")
    
    # ============ SERVICE ONCHANGE METHODS ============
    @api.onchange('service_category_id')
    def _onchange_service_category(self):
        """Tự động áp giá từ Category Service"""
        for rec in self:
            if rec.service_category_id and rec.service_category_id.category_type == 'service':
                if rec.service_category_id.price_per_hours:
                    rec.price_per_hours = rec.service_category_id.price_per_hours
            else:
                rec.price_per_hours = 0.0
    
    # ============ COMPUTE METHODS ============
    @api.depends('qty_available', 'min_stock_good')
    def _compute_good_status(self):
        """Tự động xác định trạng thái hàng hóa"""
        for rec in self:
            if rec.is_good:
                if rec.qty_available <= 0:
                    rec.good_status = 'no_more'
                elif rec.qty_available <= rec.min_stock_good:
                    rec.good_status = 'running_out'
                else:
                    rec.good_status = 'available'
            else:
                rec.good_status = False

    @api.depends('qty_available', 'min_stock_component')
    def _compute_component_status(self):
        """Tự động xác định trạng thái linh kiện"""
        for rec in self:
            if rec.is_component:
                if rec.qty_available <= 0:
                    rec.component_status = 'no_more'
                elif rec.qty_available <= rec.min_stock_component:
                    rec.component_status = 'running_out'
                else:
                    rec.component_status = 'available'
            else:
                rec.component_status = False
    
    # ============ CRUD METHODS ============
    @api.model
    def create(self, vals):
        """Override create để xử lý supplier và category"""
        # Xử lý supplier_good_id nếu là string
        if vals.get('supplier_good_id') and isinstance(vals.get('supplier_good_id'), str):
            vals['supplier_good_id'] = self._prepare_supplier_partner(
                vals.get('supplier_good_id'), 'good'
            )
        
        # Xử lý supplier_component_id nếu là string
        if vals.get('supplier_component_id') and isinstance(vals.get('supplier_component_id'), str):
            vals['supplier_component_id'] = self._prepare_supplier_partner(
                vals.get('supplier_component_id'), 'component'
            )
        
        # Tự động gán giá dịch vụ từ category
        if vals.get('service_category_id'):
            category = self.env['product.category'].browse(vals['service_category_id'])
            if category.category_type == 'service' and category.price_per_hours:
                vals['price_per_hours'] = category.price_per_hours
        
        
        return super(CyberProduct, self).create(vals)
    
    # ============ HELPER METHODS ============
    def _prepare_supplier_partner(self, name, supplier_type):
        """Tạo partner supplier, trả về id"""
        if not name:
            return False
        partner = self.env['res.partner'].create({
            'name': name,
            'is_supplier_cyber': True,
            'supplier_type': supplier_type,
        })
        return partner.id
    
    # ============ ACTION BUTTONS ============
    def action_view_stock_moves(self):
        """Xem lịch sử nhập/xuất kho"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lịch sử nhập/xuất',
            'res_model': 'stock.move',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('product_id.product_tmpl_id', '=', self.id)],
            'context': {'default_product_id': self.product_variant_id.id},
        }
    
    def action_view_stock_quants(self):
        """Xem tồn kho theo location"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tồn kho sản phẩm',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('product_id.product_tmpl_id', '=', self.id)],
            'context': {'default_product_id': self.product_variant_id.id},
        }
    
    def button_show_machine_overview(self):
        """Hiển thị tổng quan máy (chỉ cho service)"""
        return {
            'name': 'Tổng quan máy dịch vụ',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'form',
            'view_id': self.env.ref('cyber_product.view_cyber_service_overview_form').id,
            'target': 'new',
            'res_id': self.id,
        }
    
    @api.onchange('is_machine', 'is_good', 'is_component')
    def _onchange_product_type(self):
        for rec in self:
            if rec.is_machine:
                rec.is_good = False
                rec.is_component = False
            elif rec.is_good:
                rec.is_machine = False
                rec.is_component = False
            elif rec.is_component:
                rec.is_machine = False
                rec.is_good = False
    def _onchange_product_type_lock_fields(self):
        for rec in self:
            if rec.is_machine:
                rec.is_good = rec.is_component = False
                rec.good_category_id = rec.uom_good_id = rec.supplier_good_id = False
                rec.tax_percent = rec.expiry_date = rec.min_stock_good = 0
                rec.good_status = False
                rec.component_category_id = rec.uom_component_id = rec.supplier_component_id = False
                rec.lifetime_hours = rec.min_stock_component = 0
                rec.component_status = False

            elif rec.is_good:
                rec.is_machine = rec.is_component = False
                rec.service_category_id = False
                rec.machine_status = 'active'
                rec.machine_using_status = 'offline'
                rec.location = rec.price_per_hours = rec.usage_hours = 0
                rec.last_maintenance = rec.next_maintenance = False
                rec.ip_address = False
                rec.component_category_id = rec.uom_component_id = rec.supplier_component_id = False
                rec.lifetime_hours = rec.min_stock_component = 0
                rec.component_status = False

            elif rec.is_component:
                rec.is_machine = rec.is_good = False
                rec.service_category_id = False
                rec.machine_status = 'active'
                rec.machine_using_status = 'offline'
                rec.location = rec.price_per_hours = rec.usage_hours = 0
                rec.last_maintenance = rec.next_maintenance = False
                rec.ip_address = False
                rec.good_category_id = rec.uom_good_id = rec.supplier_good_id = False
                rec.tax_percent = rec.expiry_date = rec.min_stock_good = 0
                rec.good_status = False
