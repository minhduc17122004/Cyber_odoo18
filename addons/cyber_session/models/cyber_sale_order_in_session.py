from odoo import models, fields, api
from odoo.exceptions import UserError

class CyberSaleOrderInSession(models.Model):
    _name = 'cyber.sale_order_in_session'
    _description = 'Sale Order in Session'

    session_id = fields.Many2one('cyber.session', string='Session', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price')
    line_total = fields.Float(string='Line Total', compute='_compute_line_total', store=True)
    note = fields.Char(string='Ghi chú')

    @api.depends('quantity', 'price_unit')
    def _compute_line_total(self):
        for rec in self:
            rec.line_total = rec.quantity * rec.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Tự động điền giá bán khi chọn sản phẩm"""
        for rec in self:
            if rec.product_id:
                rec.price_unit = rec.product_id.list_price

    @api.model
    def create(self, vals):
        """Khi tạo order mới, kiểm tra và tự động đóng session nếu hết tiền"""
        order = super(CyberSaleOrderInSession, self).create(vals)
        if order.session_id and order.session_id.state == 'running':
            # Tính lại total_cost và kiểm tra balance
            order.session_id._compute_total_cost()
            order.session_id._auto_close_if_out_of_balance()
        return order

    def write(self, vals):
        """Khi cập nhật order (thay đổi số lượng, giá), kiểm tra balance"""
        res = super(CyberSaleOrderInSession, self).write(vals)
        for rec in self:
            if rec.session_id and rec.session_id.state == 'running':
                # Tính lại total_cost và kiểm tra balance
                rec.session_id._compute_total_cost()
                rec.session_id._auto_close_if_out_of_balance()
        return res

    def unlink(self):
        """Khi xóa order, cập nhật lại total_cost của session"""
        sessions = self.mapped('session_id').filtered(lambda s: s.state == 'running')
        res = super(CyberSaleOrderInSession, self).unlink()
        # Sau khi xóa, tính lại total_cost
        for session in sessions:
            session._compute_total_cost()
        return res

    def action_add_order(self):
        """Tạo order trong phiên chơi"""
        for rec in self:
            if rec.session_id.state != 'running':
                raise UserError("Không thể thêm order khi phiên đã đóng.")
            rec.session_id._compute_total_cost()