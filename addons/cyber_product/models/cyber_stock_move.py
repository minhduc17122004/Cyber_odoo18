from odoo import models, fields, api

class CyberStockMove(models.Model):
    _inherit = 'stock.move'

    # Field để user chọn cyber product (editable)
    cyber_product_id = fields.Many2one(
        'product.template',
        string="Sản phẩm Cyber",
        domain="['|', '|', ('is_machine', '=', True), ('is_good', '=', True), ('is_component', '=', True)]"
    )
    
    is_machine = fields.Boolean(
        string="Là máy dịch vụ",
        compute='_compute_product_flags',
        store=True,
        readonly=True
    )
    is_good = fields.Boolean(
        string="Là hàng hóa",
        compute='_compute_product_flags',
        store=True,
        readonly=True
    )
    is_component = fields.Boolean(
        string="Là linh kiện",
        compute='_compute_product_flags',
        store=True,
        readonly=True
    )
    
    is_cyber_move = fields.Boolean(
        string="Cyber Move",
        compute='_compute_is_cyber_move',
        store=True
    )

    @api.depends('cyber_product_id')
    def _compute_product_flags(self):
        """Compute các flag từ cyber_product_id"""
        for move in self:
            if move.cyber_product_id:
                move.is_machine = move.cyber_product_id.is_machine
                move.is_good = move.cyber_product_id.is_good
                move.is_component = move.cyber_product_id.is_component
            else:
                move.is_machine = False
                move.is_good = False
                move.is_component = False

    @api.depends('cyber_product_id')
    def _compute_is_cyber_move(self):
        """Tự động đánh dấu move là cyber move nếu có cyber_product_id"""
        for move in self:
            move.is_cyber_move = bool(move.cyber_product_id)

    @api.onchange('cyber_product_id')
    def _onchange_cyber_product_id(self):
        """Tự động gán product_id từ cyber_product_id"""
        if self.cyber_product_id:
            # Lấy variant đầu tiên của product template
            variant = self.cyber_product_id.product_variant_ids[:1]
            if variant:
                self.product_id = variant
                self.name = self.cyber_product_id.name
                
                # Tự động gán UOM dựa trên loại sản phẩm
                if self.cyber_product_id.is_good and self.cyber_product_id.uom_good_id:
                    self.product_uom = self.cyber_product_id.uom_good_id
                elif self.cyber_product_id.is_component and self.cyber_product_id.uom_component_id:
                    self.product_uom = self.cyber_product_id.uom_component_id
                else:
                    # Fallback: sử dụng UOM mặc định của product
                    self.product_uom = variant.uom_id
            else:
                # Nếu không có variant, cảnh báo user
                return {
                    'warning': {
                        'title': 'Cảnh báo',
                        'message': f'Sản phẩm "{self.cyber_product_id.name}" không có variant nào! Vui lòng tạo variant trước.'
                    }
                }

    @api.model
    def create(self, vals):
        """Override create để xử lý cyber_product_id"""
        if vals.get('cyber_product_id'):
            cyber_product = self.env['product.template'].browse(vals['cyber_product_id'])
            variant = cyber_product.product_variant_ids[:1]
            if variant:
                vals['product_id'] = variant.id
                if not vals.get('name'):
                    vals['name'] = cyber_product.name
        
        return super(CyberStockMove, self).create(vals)