# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CyberSaleOrderInSession(models.Model):
    _name = 'cyber.sale_order_in_session'
    _description = 'Order in Cyber Session'
    _order = 'id desc'

    session_id = fields.Many2one('cyber.session', string='Session', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Float(string='Quantity', required=True, default=1.0, digits=(16, 2))
    price_unit = fields.Float(string='Unit Price (VND)', required=True, digits=(16, 2))
    line_total = fields.Float(string='Line Total (VND)', compute='_compute_line_total', store=True, digits=(16, 2))

    @api.depends('qty', 'price_unit')
    def _compute_line_total(self):
        for rec in self:
            rec.line_total = round((rec.qty or 0.0) * (rec.price_unit or 0.0), 2)

    # ========================
    # MAIN RULE: kiểm tra balance_in_session_temp khi tạo order
    # ========================
    @api.model
    def create(self, vals):
        session = self.env['cyber.session'].browse(vals.get('session_id'))
        if not session:
            raise UserError(_("Session không hợp lệ."))
        
        if session.state == 'draft':
            raise UserError(_("Không thể tạo order khi session đang ở trạng thái Draft. Vui lòng Start session trước."))
        
        if session.state != 'running':
            raise UserError(_("Session đã đóng, không thể tạo order."))

        # Tính line_total tạm nếu caller không truyền
        qty = vals.get('qty', 1.0) or 0.0
        price_unit = vals.get('price_unit', 0.0) or 0.0
        new_order_total = round(qty * price_unit, 2) if 'line_total' not in vals else round(vals['line_total'], 2)

        # Tính realtime:
        #   service_cost_so_far + total_order_so_far
        #   balance_in_session_now = acc.balance - service_cost_so_far - total_order_so_far
        service_cost_so_far = session._service_cost_so_far()
        total_order_so_far = session._current_total_order()
        acc_balance_now = session.account_id.balance or 0.0

        balance_in_session_temp = round(acc_balance_now - service_cost_so_far - total_order_so_far, 2)

        # So sánh theo yêu cầu:
        # - Nếu new_order_total < balance_in_session_temp  → cho tạo order
        # - Nếu new_order_total == balance_in_session_temp → tạo order, tạo 2 transaction (order + service), đóng session
        # - Nếu new_order_total  > balance_in_session_temp → chặn
        if new_order_total > balance_in_session_temp:
            raise UserError(_("Không đủ tiền còn lại trong phiên để tạo order này. Còn: %s VND, Order: %s VND")
                            % (balance_in_session_temp, new_order_total))

        # Cho tạo order
        order = super(CyberSaleOrderInSession, self).create(vals)

        # ✅ TẠO TRANSACTION NGAY CHO ORDER (không đợi đóng session)
        if session.account_id and new_order_total > 0:
            self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
                'account_id': session.account_id.id,
                'session_id': session.id,
                'amount': new_order_total,
                'type': 'spend',
                'payment_method': 'balance',
                'note': f'order (Order ID: {order.id})'
            })

        # Nếu sau order số dư còn lại = 0 → đóng phiên
        equal_after = abs(new_order_total - balance_in_session_temp) < 0.005  # so gần bằng
        if equal_after and session.account_id:
            # Transaction cho SERVICE (toàn bộ tới hiện tại)
            session._create_service_transaction_if_needed(service_cost_so_far, when_label='close-by-order')

            # Đóng session
            session.with_context(skip_check=True).sudo().write({
                'end_time': fields.Datetime.now(),
                'state': 'closed',
            })
            session._finalize_close(when_label='close-by-order')
            session.message_post(body=_("🔒 Session closed because balance reached zero after order."))

        else:
            # Không đóng, nhưng cập nhật end_time_expected theo số dư mới nhất
            session._compute_end_time_expected()

        return order

    # Bảo vệ: không cho sửa phá vỡ nguyên tắc số dư
    def write(self, vals):
        # Cho phép sửa nhẹ (ghi chú, liên kết) nhưng chặn thay đổi làm giảm line_total nếu dẫn đến âm quỹ
        if any(k in vals for k in ('qty', 'price_unit', 'line_total')):
            for rec in self:
                session = rec.session_id
                
                # Kiểm tra state của session
                if session.state == 'draft':
                    raise UserError(_("Không thể chỉnh sửa order khi session đang ở trạng thái Draft."))
                
                if session.state != 'running':
                    raise UserError(_("Không thể chỉnh sửa order vì session đã đóng."))

                new_qty = vals.get('qty', rec.qty)
                new_price = vals.get('price_unit', rec.price_unit)
                new_line_total = round(vals.get('line_total', new_qty * new_price), 2)

                # Tính lại balance_in_session_temp nếu line_total thay đổi
                service_cost_so_far = session._service_cost_so_far()
                other_orders_total = round(sum(session.order_ids.filtered(lambda r: r.id != rec.id).mapped('line_total')), 2)
                acc_balance_now = session.account_id.balance or 0.0
                balance_in_session_temp = round(acc_balance_now - service_cost_so_far - other_orders_total, 2)

                if new_line_total > balance_in_session_temp:
                    raise UserError(_("Sửa order vượt quá số tiền còn lại trong phiên. Còn: %s VND, Order mới: %s VND")
                                    % (balance_in_session_temp, new_line_total))

                # Tính delta (phần chênh lệch)
                delta = round(new_line_total - rec.line_total, 2)
                
                # Cập nhật order
                res = super(CyberSaleOrderInSession, self).write(vals)

                # ✅ TẠO TRANSACTION CHO PHẦN CHÊNH LỆCH (nếu có)
                if delta != 0 and session.account_id:
                    if delta > 0:
                        # Tăng order → tạo transaction spend thêm
                        self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
                            'account_id': session.account_id.id,
                            'session_id': session.id,
                            'amount': delta,
                            'type': 'spend',
                            'payment_method': 'balance',
                            'note': f'order-edit (+{delta}) (Order ID: {rec.id})'
                        })
                    else:
                        # Giảm order → tạo transaction refund (topup)
                        self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
                            'account_id': session.account_id.id,
                            'session_id': session.id,
                            'amount': abs(delta),
                            'type': 'topup',
                            'payment_method': 'balance',
                            'note': f'order-edit-refund ({delta}) (Order ID: {rec.id})'
                        })

                # Nếu chỉnh sửa làm vừa khít số dư → đóng phiên
                equal_after = abs(new_line_total - balance_in_session_temp) < 0.005
                if equal_after and session.account_id:
                    # Service tới hiện tại
                    session._create_service_transaction_if_needed(service_cost_so_far, when_label='close-by-order-edit')

                    # Đóng
                    session.with_context(skip_check=True).sudo().write({
                        'end_time': fields.Datetime.now(),
                        'state': 'closed',
                    })
                    session._finalize_close(when_label='close-by-order-edit')
                    session.message_post(body=_("🔒 Session closed because balance reached zero after order edit."))
                else:
                    session._compute_end_time_expected()

                return res
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.session_id and rec.session_id.state != 'running':
                raise UserError(_("Không thể xóa order vì session đã đóng."))
        return super().unlink()
