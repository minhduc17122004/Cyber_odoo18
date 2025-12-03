from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CyberSession(models.Model):
    _name = 'cyber.session'
    _description = 'Cyber Game Session'
    _inherit = ['mail.thread']
    _order = 'name desc'

    # ========================
    # FIELDS
    # ========================
    name = fields.Char(string='Session ID', required=True, readonly=True, copy=False, default='New')
    account_id = fields.Many2one('cyber.account', string='Account', required=True, ondelete='cascade')
    product_machine_id = fields.Many2one('product.product', string='Machine', domain=[('is_machine', '=', True)], required=True)
    start_time = fields.Datetime(string='Start Time', default=lambda self: fields.Datetime.now())
    end_time = fields.Datetime(string='End Time')
    end_time_expected = fields.Datetime(string='Expected End Time', compute='_compute_end_time_expected', store=True)
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True, digits=(12, 6))
    price_per_hour = fields.Float(
        string='Price per Hour (VND)',
        related='product_machine_id.list_price',
        store=True,
        readonly=True,
        digits=(16, 2)
    )
    total_sale = fields.Float(string='Total Sale (VND)', compute='_compute_total_sale', store=True, digits=(16, 0))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    session_state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='Session Status', default='draft', tracking=True)

    order_ids = fields.One2many('cyber.sale_order_in_session', 'session_id', string='Orders in Session')
    picking_ids = fields.One2many(
        'stock.picking',
        compute='_compute_picking_ids',
        string='Stock Pickings'
    )

    # ========================
    # NEW COMPUTED FIELDS
    # ========================
    time_played = fields.Float(
        string='Time Played (hours)',
        compute='_compute_time_played',
        store=True,
        tracking=True,
        digits=(12, 6)
    )
    
    time_remaining = fields.Float(
        string='Time Remaining (hours)',
        compute='_compute_time_remaining',
        store=True,
        tracking=True,
        digits=(12, 6)
    )
    
    total_service = fields.Float(
        string='Total Service Cost (VND)',
        compute='_compute_total_service',
        store=True,
        tracking=True,
        digits=(16, 0)
    )
    
    total_order = fields.Float(
        string='Total Order Cost (VND)',
        compute='_compute_total_order',
        store=True,
        tracking=True,
        digits=(16, 0)
    )

    # ========================
    # COMPUTE METHODS
    # ========================
    @api.depends('order_ids')
    def _compute_picking_ids(self):
        """Lấy danh sách picking được tạo từ session này"""
        for session in self:
            pickings = self.env['stock.picking'].search([
                ('origin', '=', f'cyber.session,{session.id}')
            ])
            session.picking_ids = pickings

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Tính thời lượng phiên chơi"""
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = delta.total_seconds() / 3600
            else:
                rec.duration = 0.0

    @api.depends('start_time', 'session_state')
    def _compute_time_played(self):
        """Tính thời gian đã chơi (giờ)"""
        for rec in self:
            if rec.session_state == 'running' and rec.start_time:
                delta = fields.Datetime.now() - rec.start_time
                rec.time_played = delta.total_seconds() / 3600
            else:
                rec.time_played = 0.0

    @api.depends('account_id.balance', 'price_per_hour')
    def _compute_time_remaining(self):
        """Tính thời gian còn lại (giờ) - chỉ dựa trên balance của account"""
        for rec in self:
            if rec.account_id and rec.account_id.balance > 0 and rec.price_per_hour > 0:
                rec.time_remaining = rec.account_id.balance / rec.price_per_hour
            else:
                rec.time_remaining = 0.0

    @api.depends('duration', 'price_per_hour', 'session_state')
    def _compute_total_service(self):
        """Tính chi phí dịch vụ (giờ chơi)"""
        for rec in self:
            if rec.session_state == 'closed':
                rec.total_service = round(rec.duration * rec.price_per_hour, 0)
            else:
                rec.total_service = 0.0

    @api.depends('order_ids.line_total', 'order_ids.order_state')
    def _compute_total_order(self):
        """Tính tổng chi phí đơn hàng - chỉ tính các order đã hoàn thành"""
        for rec in self:
            done_orders = rec.order_ids.filtered(lambda o: o.order_state == 'done')
            rec.total_order = round(sum(done_orders.mapped('line_total')), 0)

    @api.depends('total_service', 'total_order')
    def _compute_total_sale(self):
        """Tổng chi phí = total_service + total_order"""
        for rec in self:
            rec.total_sale = round(rec.total_service + rec.total_order, 0)

    @api.depends('start_time', 'time_remaining')
    def _compute_end_time_expected(self):
        """Tính thời gian kết thúc dự kiến dựa trên time_remaining"""
        for rec in self:
            if rec.start_time and rec.time_remaining > 0:
                rec.end_time_expected = rec.start_time + timedelta(hours=rec.time_remaining)
            else:
                rec.end_time_expected = False

    # ==========================
    # AUTO CLOSE MECHANISM
    # ==========================
    def _auto_close_if_out_of_balance(self):
        """Kiểm tra và tự động đóng phiên nếu hết tiền hoặc hết thời gian"""
        for rec in self:
            if rec.session_state != 'running':
                continue
            
            now = fields.Datetime.now()
            should_close = False
            reason = None
            
            if rec.account_id and rec.account_id.balance <= 0:
                should_close = True
                reason = 'low_balance'
            elif rec.end_time_expected and now >= rec.end_time_expected:
                should_close = True
                reason = 'time_expired'
            
            if should_close and reason:
                rec.action_close_session(auto=True, reason=reason)

    # ==========================
    # CLOSE SESSION ACTION
    # ==========================
    def action_close_session(self, auto=False, reason=None):
        """Đóng phiên thủ công hoặc tự động. Nếu auto=True và balance không đủ, cắt duration"""
        for rec in self:
            # Kiểm tra phiên phải đang running
            if rec.session_state != 'running':
                raise UserError(_("Chỉ có thể đóng phiên đang chạy"))
            
            # Kiểm tra không có order nào đang in_progress
            in_progress_orders = rec.order_ids.filtered(lambda o: o.order_state == 'in_progress')
            if in_progress_orders:
                order_names = ', '.join(in_progress_orders.mapped('product_id.name'))
                raise UserError(_(
                    "Không thể đóng phiên khi còn đơn hàng đang thực hiện.\n"
                    "Các sản phẩm: %s\n"
                    "Vui lòng hoàn thành hoặc hủy các đơn hàng này trước."
                ) % order_names)
            
            # Lưu lại duration cũ trước khi đóng phiên để tính usage_hours
            old_duration = rec.duration
            
            if auto and rec.account_id:
                available_for_service = rec.account_id.balance - rec.total_order
                
                if available_for_service < 0:
                    available_for_service = 0
                
                if rec.price_per_hour > 0:
                    max_duration_hours = available_for_service / rec.price_per_hour
                    
                    if rec.start_time:
                        current_duration = (fields.Datetime.now() - rec.start_time).total_seconds() / 3600
                        
                        if current_duration > max_duration_hours:
                            adjusted_end_time = rec.start_time + timedelta(hours=max_duration_hours)
                            rec.write({
                                'end_time': adjusted_end_time,
                                'session_state': 'closed'
                            })
                        else:
                            rec.write({
                                'end_time': fields.Datetime.now(),
                                'session_state': 'closed'
                            })
                    else:
                        rec.write({
                            'end_time': fields.Datetime.now(),
                            'session_state': 'closed'
                        })
                else:
                    rec.write({
                        'end_time': fields.Datetime.now(),
                        'session_state': 'closed'
                    })
            else:
                rec.write({
                    'end_time': fields.Datetime.now(),
                    'session_state': 'closed'
                })
            
            # Tính lại các field computed cho session
            rec._compute_duration()
            rec._compute_total_service()
            rec._compute_total_sale()
            
            # ========================
            # CẬP NHẬT USAGE_HOURS CHO MÁY
            # ========================
            rec._update_machine_usage_hours(old_duration)
            
            # Post message vào chatter
            if auto:
                if reason:
                    message = _("Session auto-closed due to %s") % reason
                else:
                    message = _("Session auto-closed")
                rec.message_post(body=message)
            else:
                rec.message_post(body=_("Session closed manually"))
            
            # ========================
            # CẬP NHẬT TRẠNG THÁI MÁY
            # ========================
            if rec.product_machine_id and hasattr(rec.product_machine_id, 'machine_using_status'):
                rec.product_machine_id.product_tmpl_id.with_context(skip_readonly=True).write({
                    'machine_using_status': 'offline'
                })
                rec.message_post(body=_("✅ Máy được đặt thành: <b>Ngoại tuyến</b>"))
            
            # ========================
            # TỰ ĐỘNG TẠO PHIẾU XUẤT KHO
            # ========================
            rec._create_stock_picking_from_orders()
        
        return True

    # ==========================
    # CẬP NHẬT USAGE HOURS CHO MÁY
    # ==========================
    def _update_machine_usage_hours(self, old_duration):
        """
        Cập nhật tổng giờ sử dụng của máy sau khi đóng phiên
        Chỉ cập nhật phần thời gian mới (duration hiện tại - duration cũ)
        
        Args:
            old_duration: Duration trước khi đóng phiên
        """
        self.ensure_one()
        
        if not self.product_machine_id:
            return
        
        # Lấy product template từ product variant
        product_template = self.product_machine_id.product_tmpl_id
        
        if not product_template or not product_template.is_machine:
            return
        
        # Tính thời gian sử dụng mới (duration sau khi đóng - duration trước đó)
        new_usage = self.duration - old_duration
        
        # Làm tròn thành số nguyên giờ
        new_usage_hours = int(round(new_usage))
        
        if new_usage_hours > 0:
            # Cập nhật usage_hours của máy với context skip_readonly
            current_usage = product_template.usage_hours or 0
            updated_usage = current_usage + new_usage_hours
            
            product_template.with_context(skip_readonly=True).write({
                'usage_hours': updated_usage
            })
            
            # Log message vào session
            self.message_post(
                body=_("<b>Cập nhật giờ sử dụng máy</b><br/>"
                       "Máy: <b>%s</b><br/>"
                       "Giờ sử dụng phiên này: <b>%s giờ</b><br/>"
                       "Tổng giờ đã sử dụng: <b>%s → %s giờ</b>") % (
                    product_template.name,
                    new_usage_hours,
                    current_usage,
                    updated_usage
                )
            )
            
            # Log message vào product
            product_template.message_post(
                body=_("<b>Cập nhật giờ sử dụng</b><br/>"
                       "Session: <b>%s</b><br/>"
                       "Giờ sử dụng thêm: <b>+%s giờ</b><br/>"
                       "Tổng giờ: <b>%s giờ</b>") % (
                    self.name,
                    new_usage_hours,
                    updated_usage
                )
            )

    # ==========================
    # PHIẾU XUẤT KHO TỰ ĐỘNG
    # ==========================
    def _create_stock_picking_from_orders(self):
        """
        Tạo phiếu xuất kho từ các order hoàn thành trong phiên
        - Gom tất cả các order có order_state='done' thành 1 phiếu xuất
        - Tạo cyber stock.move cho mỗi order (sử dụng CyberStockMove)
        - Tự động confirm, gán quantity_done và validate phiếu xuất
        - Giảm số lượng tồn kho (stock.quant) theo số lượng order
        
        Returns:
            stock.picking: Phiếu xuất được tạo, hoặc None nếu không có order
        """
        self.ensure_one()

        # Lấy tất cả các order đã hoàn thành ('done')
        done_orders = self.order_ids.filtered(lambda o: o.order_state == 'done')
        
        if not done_orders:
            self.message_post(body=_("Không có order nào được hoàn thành để xuất kho."))
            return None
        
        # Kiểm tra tránh tạo phiếu xuất trùng lặp
        existing_picking = self.env['stock.picking'].search([
            ('origin', '=', f'cyber.session,{self.id}'),
            ('state', 'in', ['draft', 'confirmed', 'assigned', 'done'])
        ], limit=1)
        
        if existing_picking:
            self.message_post(
                body=_("Phiếu xuất kho đã tồn tại: <b>%s</b>") % existing_picking.name
            )
            return existing_picking

        try:
            # ==========================================
            # BƯỚC 1: LẤY CẤU HÌNH KHO VÀ PICKING TYPE
            # ==========================================
            warehouse = self.env['stock.warehouse'].search([], limit=1)
            if not warehouse:
                raise UserError(
                    _("Không tìm thấy kho. Vui lòng thiết lập kho trước.")
                )

            picking_type = warehouse.out_type_id
            if not picking_type:
                raise UserError(
                    _("Không tìm thấy kiểu phiếu xuất. Vui lòng thiết lập trong kho.")
                )

            # ==========================================
            # BƯỚC 2: TẠO PHIẾU XUẤT KHO (PICKING)
            # ==========================================
            picking_vals = {
                'picking_type_id': picking_type.id,
                'location_id': warehouse.lot_stock_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id or warehouse.lot_stock_id.id,
                'origin': f'cyber.session,{self.id}',
            }
            
            # Tạo picking với context để đánh dấu là cyber picking
            picking = self.env['stock.picking'].with_context(
                is_cyber_picking=True
            ).create(picking_vals)

            # ==========================================
            # BƯỚC 3: TẠO CYBER STOCK.MOVE CHO MỖI ORDER
            # ==========================================
            move_ids = []
            order_details = []

            for order in done_orders:
                # Kiểm tra product có phải là good không
                if not order.product_id or not order.product_id.is_good:
                    continue

                product = order.product_id
                product_template = product.product_tmpl_id

                # Tạo cyber stock move với cyber_product_id
                move_vals = {
                    'picking_id': picking.id,
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': order.quantity,
                    'product_uom': product.uom_id.id,
                    'location_id': warehouse.lot_stock_id.id,
                    'location_dest_id': picking_type.default_location_dest_id.id or warehouse.lot_stock_id.id,
                    'origin': f'cyber.sale_order_in_session,{order.id}',
                }
                
                # Thêm cyber_product_id để đánh dấu move này là cyber move
                if product_template:
                    move_vals['cyber_product_id'] = product_template.id
                
                move = self.env['stock.move'].create(move_vals)
                move_ids.append(move.id)
                order_details.append(f"{product.name} x {int(order.quantity)}")

            # Nếu không có move nào được tạo, xóa picking
            if not move_ids:
                picking.unlink()
                self.message_post(
                    body=_("Không có sản phẩm nào để xuất kho (kiểm tra domain is_good).")
                )
                return None

            # ==========================================
            # BƯỚC 4: CONFIRM & VALIDATE PHIẾU XUẤT
            # ==========================================
            picking.action_confirm()
            picking.button_validate()

            # ==========================================
            # BƯỚC 6: LOG MESSAGE VÀO CHATTER
            # ==========================================
            order_info = ', '.join(order_details)
            self.message_post(
                body=_("<b>Phiếu xuất kho tự động được tạo thành công</b><br/>"
                       "Picking: <b>%s</b><br/>"
                       "Sản phẩm: <b>%s</b><br/>"
                       "Trạng thái: <b>Đã validate</b>") % (
                    picking.name, order_info
                )
            )

            return picking

        except Exception as e:
            # Xóa picking nếu có lỗi trong quá trình tạo
            if 'picking' in locals() and picking.exists():
                picking.unlink()
            
            error_msg = str(e)
            raise UserError(
                _("Lỗi khi tạo phiếu xuất kho tự động:\n%s") % error_msg
            )

    def action_manual_create_picking(self):
        """
        Action button: Thủ công tạo phiếu xuất kho
        Chỉ có thể gọi khi phiên đã đóng
        """
        self.ensure_one()
        
        if self.session_state == 'running':
            raise UserError(
                _("Chỉ có thể tạo phiếu xuất kho khi phiên đã đóng.")
            )
        
        picking = self._create_stock_picking_from_orders()
        
        if picking:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Phiếu Xuất Kho'),
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': picking.id,
                'target': 'current',
            }
        else:
            raise UserError(
                _("Không thể tạo phiếu xuất kho. Kiểm tra các order đã hoàn thành.")
            )

    def action_view_pickings(self):
        """
        Action button: Xem tất cả phiếu xuất kho của phiên
        """
        self.ensure_one()
        
        pickings = self.env['stock.picking'].search([
            ('origin', '=', f'cyber.session,{self.id}')
        ])
        
        if not pickings:
            raise UserError(_("Không có phiếu xuất kho nào cho phiên này."))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Phiếu Xuất Kho - Phiên %s') % self.name,
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', pickings.ids)],
            'target': 'current',
        }
    
    def action_start_session(self):
        """Bắt đầu phiên từ draft với kiểm tra đầy đủ"""
        for rec in self:
            if rec.session_state != 'draft':
                raise UserError(_("Chỉ có thể bắt đầu phiên ở trạng thái Draft"))
            
            if not rec.account_id:
                raise ValidationError(_("Tài khoản là bắt buộc để bắt đầu phiên"))
            
            existing_session = self.search([
                ('account_id', '=', rec.account_id.id),
                ('session_state', '=', 'running'),
                ('id', '!=', rec.id)
            ], limit=1)
            if existing_session:
                raise ValidationError(_(
                    "Tài khoản %s đang có phiên %s đang chạy.\n"
                    "Vui lòng đóng phiên đó trước khi bắt đầu phiên mới."
                ) % (rec.account_id.username, existing_session.name))
            
            if not rec.product_machine_id:
                raise ValidationError(_("Máy là bắt buộc để bắt đầu phiên"))
            
            if rec.account_id.balance <= 0:
                raise ValidationError(_("Số dư tài khoản không đủ để bắt đầu phiên"))
            
            if rec.price_per_hour <= 0:
                raise ValidationError(_("Giá mỗi giờ của máy phải lớn hơn 0. Vui lòng kiểm tra cấu hình sản phẩm máy."))
            
            now = fields.Datetime.now()
            rec.write({
                'start_time': now,
                'session_state': 'running'
            })
            
            # ========================
            # CẬP NHẬT TRẠNG THÁI MÁY
            # ========================
            if rec.product_machine_id and hasattr(rec.product_machine_id, 'machine_using_status'):
                rec.product_machine_id.product_tmpl_id.with_context(skip_readonly=True).write({
                    'machine_using_status': 'in_use'
                })
                rec.message_post(body=_("Máy được đặt thành: <b>Đang sử dụng</b>"))
            
            time_str = now.strftime('%H:%M')
            rec.message_post(body=_("Session started at %s") % time_str)
        
        return True

    # ========================
    # ONCHANGE METHODS
    # ========================
    @api.onchange('product_machine_id')
    def _onchange_product_machine(self):
        """Validate machine selection and auto-fill price"""
        if self.product_machine_id:
            if not self.product_machine_id.is_machine:
                return {
                    'warning': {
                        'title': _("Invalid Product"),
                        'message': _("Selected product is not a machine. Please select a valid machine product.")
                    }
                }
            if self.product_machine_id.list_price <= 0:
                return {
                    'warning': {
                        'title': _("Invalid Price"),
                        'message': _("Machine price must be greater than 0. Please check the product configuration.")
                    }
                }

    # ========================
    # OVERRIDE METHODS
    # ========================
    @api.model
    def create(self, vals):
        """Tạo session ở trạng thái draft"""
        if vals.get('name', 'New') == 'New':
            timestamp = fields.Datetime.now().strftime('%Y%m%d%H%M%S')
            vals['name'] = f'SES{timestamp}'

        if vals.get('session_state') != 'running':
            vals.pop('start_time', None)

        session = super(CyberSession, self).create(vals)
        session.message_post(body=_("Session created in draft state."))
        return session

    # ========================
    # CRON AUTO-CLOSE
    # ========================
    @api.model
    def action_autoclose_sessions(self):
        """Tìm và đóng tất cả phiên hết hạn hoặc hết tiền (batch 50 records)"""
        now = fields.Datetime.now()
        
        domain_low_balance = [
            ('session_state', '=', 'running'),
            ('account_id.balance', '<=', 0)
        ]
        
        domain_time_expired = [
            ('session_state', '=', 'running'),
            ('end_time_expected', '!=', False),
            ('end_time_expected', '<=', now)
        ]
        
        sessions_low_balance = self.search(domain_low_balance, limit=50)
        sessions_time_expired = self.search(domain_time_expired, limit=50)
        
        all_sessions = (sessions_low_balance | sessions_time_expired)
        if len(all_sessions) > 50:
            all_sessions = all_sessions[:50]
        
        closed_count = 0
        failed_sessions = []
        
        for session in all_sessions:
            try:
                reason = None
                if session.account_id and session.account_id.balance <= 0:
                    reason = 'low_balance'
                elif session.end_time_expected and now >= session.end_time_expected:
                    reason = 'time_expired'
                
                session.action_close_session(auto=True, reason=reason)
                closed_count += 1
            except Exception as e:
                failed_sessions.append({
                    'session_id': session.id,
                    'session_name': session.name,
                    'error': str(e)
                })
                continue
        
        log_message = f"Auto-closed {closed_count} sessions at {now}"
        if failed_sessions:
            log_message += f". Failed to close {len(failed_sessions)} sessions: {failed_sessions}"
        
        self.env['ir.logging'].create({
            'name': 'Cyber Session Auto-Close',
            'type': 'server',
            'dbname': self.env.cr.dbname,
            'level': 'INFO',
            'message': log_message,
            'path': 'cyber.session',
            'line': '0',
            'func': 'action_autoclose_sessions',
        })
        
        return closed_count