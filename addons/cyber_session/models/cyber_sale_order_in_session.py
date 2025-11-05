from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CyberSaleOrderInSession(models.Model):
    _name = 'cyber.sale_order_in_session'
    _description = 'Đơn hàng trong phiên chơi'

    session_id = fields.Many2one(
        comodel_name='cyber.session',
        string='Phiên chơi',
        ondelete='cascade',
        required=True
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Sản phẩm',
        required=True
    )
    quantity = fields.Float(
        string='Số lượng',
        default=1.0,
        digits=(12, 2)
    )
    price_unit = fields.Float(
        string='Đơn giá (VND)',
        digits=(16, 2)
    )
    line_total = fields.Float(
        string='Thành tiền (VND)',
        compute='_compute_line_total',
        store=True,
        digits=(16, 2)
    )
    note = fields.Char(string='Ghi chú')

    # ========================
    # COMPUTE
    # ========================
    @api.depends('quantity', 'price_unit')
    def _compute_line_total(self):
        """Tính thành tiền = số lượng × đơn giá"""
        for rec in self:
            rec.line_total = rec.quantity * rec.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Tự động điền giá bán khi chọn sản phẩm"""
        for rec in self:
            if rec.product_id:
                rec.price_unit = rec.product_id.list_price

    # ========================
    # VALIDATION
    # ========================
    def _validate_balance_sufficient(self, session, additional_cost=0):
        """
        Kiểm tra balance có đủ để chi trả cho session sau khi thêm order.
        
        Args:
            session: cyber.session record
            additional_cost: Chi phí thêm vào (cost của order mới/cập nhật)
            
        Raises:
            ValidationError: Nếu balance không đủ
        """
        if not session or session.state != 'running':
            return
        
        # Tính session cost REAL-TIME (vì session đang chạy, chưa có end_time)
        if session.start_time:
            from odoo import fields as odoo_fields
            now = odoo_fields.Datetime.now()
            time_played_seconds = (now - session.start_time).total_seconds()
            time_played_hours = time_played_seconds / 3600.0
            session_cost = time_played_hours * session.price_per_hour
        else:
            session_cost = 0.0
        
        # Tính chi phí đơn hàng
        current_orders_cost = sum(session.order_ids.mapped('line_total'))
        orders_cost = current_orders_cost + additional_cost
        
        # Tổng chi phí dự kiến
        projected_total_cost = session_cost + orders_cost
        
        # Kiểm tra balance
        current_balance = session.account_id.balance
        
        if current_balance < projected_total_cost:
            raise ValidationError(_(
                "⚠️ Không thể thêm sản phẩm này vào phiên chơi!\n\n"
                "📊 Chi tiết:\n"
                "💳 Số dư hiện tại: {:,.0f} VND\n"
                "💰 Chi phí phiên chơi (đã chơi): {:,.0f} VND\n"
                "🛒 Chi phí đơn hàng (hiện tại): {:,.0f} VND\n"
                "➕ Chi phí thêm vào: {:,.0f} VND\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📈 Tổng chi phí dự kiến: {:,.0f} VND\n"
                "❌ Thiếu: {:,.0f} VND\n\n"
                "💡 Vui lòng nạp thêm tiền hoặc giảm số lượng sản phẩm."
            ).format(
                current_balance,
                session_cost,
                current_orders_cost,
                additional_cost,
                projected_total_cost,
                projected_total_cost - current_balance
            ))

    # ========================
    # CRUD OPERATIONS
    # ========================
    @api.model
    def create(self, vals):
        """
        Override create để kiểm tra balance trước khi tạo order.
        Nếu balance không đủ → raise error → transaction rollback (undo).
        """
        # Tạo record tạm để tính line_total
        temp_order = self.new(vals)
        temp_order._compute_line_total()
        
        # Lấy session
        session = self.env['cyber.session'].browse(vals.get('session_id'))
        
        # Kiểm tra balance (với chi phí của order mới)
        self._validate_balance_sufficient(session, temp_order.line_total)
        
        # Nếu pass validation → tạo order thật
        order = super(CyberSaleOrderInSession, self).create(vals)
        
        # Force recompute total_cost của session
        if order.session_id and order.session_id.state == 'running':
            order.session_id.invalidate_recordset(['total_cost'])
        
        return order

    def write(self, vals):
        """
        Override write để kiểm tra balance trước khi cập nhật order.
        Nếu balance không đủ → raise error → transaction rollback (undo).
        """
        for rec in self:
            if rec.session_id and rec.session_id.state == 'running':
                # Tính chi phí cũ
                old_cost = rec.line_total
                
                # Tính chi phí mới (giả lập update)
                temp_rec = rec.copy_data()[0]
                temp_rec.update(vals)
                temp_order = self.new(temp_rec)
                temp_order._compute_line_total()
                new_cost = temp_order.line_total
                
                # Tính chi phí thêm vào (có thể âm nếu giảm)
                additional_cost = new_cost - old_cost
                
                # Kiểm tra balance
                self._validate_balance_sufficient(rec.session_id, additional_cost)
        
        # Nếu pass validation → cập nhật thật
        res = super(CyberSaleOrderInSession, self).write(vals)
        
        # Force recompute total_cost
        for rec in self:
            if rec.session_id and rec.session_id.state == 'running':
                rec.session_id.invalidate_recordset(['total_cost'])
        
        return res

    def unlink(self):
        """
        Override unlink để cập nhật lại total_cost của session sau khi xóa order.
        """
        sessions = self.mapped('session_id').filtered(lambda s: s.state == 'running')
        
        res = super(CyberSaleOrderInSession, self).unlink()
        
        # Force recompute total_cost
        for session in sessions:
            session.invalidate_recordset(['total_cost'])
        
        return res