from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class CyberSaleOrderInSession(models.Model):
    _name = 'cyber.sale_order_in_session'
    _description = 'Sale Order in Session'
    _order = 'id desc'

    session_id = fields.Many2one('cyber.session', string='Session', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, domain=[('is_good', '=', True)])
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price (VND)', digits=(16, 0))
    line_total = fields.Float(string='Line Total (VND)', compute='_compute_line_total', store=True, digits=(16, 0))
    note = fields.Char(string='Ghi chú')
    order_state = fields.Selection([
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('canceled', 'Canceled')
    ], string='Order Status', default='in_progress', required=True, tracking=True)

    @api.depends('quantity', 'price_unit', 'order_state')
    def _compute_line_total(self):
        for rec in self:
            # Chỉ tính line_total khi order ở trạng thái 'done'
            # Order in_progress hoặc canceled sẽ có line_total = 0
            if rec.order_state == 'done':
                rec.line_total = rec.quantity * rec.price_unit
            else:
                rec.line_total = 0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Tự động điền giá bán khi chọn sản phẩm"""
        for rec in self:
            if rec.product_id:
                rec.price_unit = rec.product_id.list_price

    # ==================================================
    # OVERRIDES
    # ==================================================
    @api.model
    def create(self, vals):
        """Khi tạo order mới: kiểm tra trạng thái session và trigger recompute"""
        order = super(CyberSaleOrderInSession, self).create(vals)
        session = order.session_id

        # Kiểm tra session có được phép thêm order không
        if session.session_state == 'closed':
            raise UserError(_("Không thể thêm order khi phiên đã đóng."))

        # Trigger session recompute để cập nhật các field computed
        session._compute_total_order()

        return order

    def write(self, vals):
        """Khi cập nhật order: kiểm tra canceled và trigger recompute"""
        # Không cho phép sửa order đã hủy (trừ field order_state)
        for rec in self:
            if rec.order_state == 'canceled' and any(key != 'order_state' for key in vals.keys()):
                raise UserError(_("Không thể sửa order đã hủy."))
        
        res = super(CyberSaleOrderInSession, self).write(vals)
        
        # Trigger recompute khi có thay đổi quantity, price_unit, hoặc order_state
        for rec in self:
            session = rec.session_id
            if session.session_state != 'running':
                continue

            if 'quantity' in vals or 'price_unit' in vals or 'order_state' in vals:
                session._compute_total_order()

        return res

    def _create_stock_move_for_order(self):
        """
        Tự động tạo phiếu xuất kho (stock.move) khi order được đánh dấu là 'done'
        Để cập nhật lại tồn kho (stock.quant)
        """
        self.ensure_one()
        
        # Kiểm tra product có phải là good không
        if not self.product_id or not self.product_id.is_good:
            return
        
        # Kiểm tra xem đã tạo stock move cho order này chưa (tránh tạo trùng lặp)
        existing_move = self.env['stock.move'].search([
            ('origin', '=', f'cyber.sale_order_in_session,{self.id}')
        ], limit=1)
        
        if existing_move:
            return
        
        # Lấy warehouse mặc định
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        if not warehouse:
            raise UserError(_("Không tìm thấy kho. Vui lòng thiết lập kho trước."))
        
        # Lấy picking type cho phiếu xuất (outgoing)
        picking_type = warehouse.out_type_id
        if not picking_type:
            raise UserError(_("Không tìm thấy kiểu phiếu xuất. Vui lòng thiết lập trong kho."))
        
        try:
            # Tạo phiếu xuất kho (picking)
            picking_vals = {
                'picking_type_id': picking_type.id,
                'partner_id': self.session_id.partner_id.id if self.session_id.partner_id else False,
                'location_id': warehouse.lot_stock_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id or warehouse.lot_stock_id.id,
                'origin': f'cyber.sale_order_in_session,{self.id}',
            }
            picking = self.env['stock.picking'].create(picking_vals)
            
            # Tạo stock move trong picking
            move_vals = {
                'picking_id': picking.id,
                'product_id': self.product_id.id,
                'name': self.product_id.name,
                'quantity_done': self.quantity,
                'product_uom': self.product_id.uom_id.id,
                'location_id': warehouse.lot_stock_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id or warehouse.lot_stock_id.id,
                'origin': f'cyber.sale_order_in_session,{self.id}',
            }
            
            move = self.env['stock.move'].create(move_vals)
            
            # Tự động confirm phiếu xuất
            picking.action_confirm()
            
            # Tự động đánh dấu tất cả dòng là 'done'
            for line in picking.move_ids:
                line.quantity_done = line.product_qty
            
            # Tự động validate phiếu xuất
            picking.button_validate()
            
            # Log thông tin
            self.session_id.message_post(
                body=_("Tự động tạo phiếu xuất kho cho order: %s x %s") % (
                    self.product_id.name, self.quantity
                )
            )
            
        except Exception as e:
            raise UserError(_(
                "Lỗi khi tạo phiếu xuất kho tự động:\n%s"
            ) % str(e))

    def unlink(self):
        """Khi xóa order: trigger session recompute"""
        # Lưu lại danh sách sessions cần update trước khi xóa
        sessions_to_update = self.mapped('session_id')
        res = super(CyberSaleOrderInSession, self).unlink()

        # Trigger recompute cho các sessions đã lưu
        for session in sessions_to_update:
            if session.exists():
                session._compute_total_order()
        
        return res
