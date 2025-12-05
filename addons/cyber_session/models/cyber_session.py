from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CyberSession(models.Model):
    _name = 'cyber.session'
    _description = 'Cyber Game Session'
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
    ], string='Session Status', default='draft')

    order_ids = fields.One2many('cyber.sale_order_in_session', 'session_id', string='Orders in Session')
    picking_ids = fields.One2many(
        'stock.picking',
        compute='_compute_picking_ids',
        string='Stock Pickings'
    )

    # ========================
    # NEW COMPUTED FIELDS
    # ========================
    time_remaining = fields.Float(
        string='Time Remaining (hours)',
        compute='_compute_time_remaining',
        store=True,
        digits=(12, 6)
    )
    
    total_service = fields.Float(
        string='Total Service Cost (VND)',
        compute='_compute_total_service',
        store=True,
        digits=(16, 0)
    )
    
    total_order = fields.Float(
        string='Total Order Cost (VND)',
        compute='_compute_total_order',
        store=True,
        digits=(16, 0)
    )
    
    has_incomplete_orders = fields.Boolean(
        string='Has Incomplete Orders',
        compute='_compute_has_incomplete_orders',
        store=True
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
            # Lọc chỉ lấy các order có order_state = 'done'
            done_orders = rec.order_ids.filtered(lambda o: o.order_state == 'done')
            rec.total_order = round(sum(done_orders.mapped('line_total')), 0)

    @api.depends('order_ids.order_state', 'session_state')
    def _compute_has_incomplete_orders(self):
        """Kiểm tra xem phiên có order chưa hoàn thành không"""
        for rec in self:
            if rec.session_state == 'closed':
                # Chỉ check khi phiên đã đóng
                in_progress_orders = rec.order_ids.filtered(lambda o: o.order_state == 'in_progress')
                rec.has_incomplete_orders = len(in_progress_orders) > 0
            else:
                rec.has_incomplete_orders = False
                
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


    def action_close_session(self):
        """Đóng phiên thủ công"""
        for rec in self:
            #Kiểm tra phiên phải đang running
            # if rec.session_state != 'running':
                # raise UserError(_("Chỉ có thể đóng phiên đang chạy"))
            
            # Kiểm tra không có order nào đang in_progress
            in_progress_orders = rec.order_ids.filtered(lambda o: o.order_state == 'in_progress')
            if in_progress_orders:
                order_names = ', '.join(in_progress_orders.mapped('product_id.name'))
                raise UserError(_(
                    "Không thể đóng phiên khi còn đơn hàng đang thực hiện.\n"
                    "Các sản phẩm: %s\n"
                    "Vui lòng hoàn thành hoặc hủy các đơn hàng này trước."
                ) % order_names)
            
            # Lưu duration trước khi update end_time
            old_duration = rec.duration
            
            # Đóng phiên với end_time = now
            rec.write({
                'end_time': fields.Datetime.now(),
                'session_state': 'closed'
            })
            
            # Tính lại các field computed cho session
            rec._compute_duration()
            rec._compute_total_service()
            rec._compute_total_sale()
            
            # ========================
            # CẬP NHẬT TRẠNG THÁI MÁY
            # ========================
            if rec.product_machine_id and hasattr(rec.product_machine_id, 'machine_using_status'):
                rec.product_machine_id.product_tmpl_id.with_context(skip_readonly=True).write({
                    'machine_using_status': 'offline'
                })
            
            # ========================
            # CẬP NHẬT USAGE HOURS CHO MÁY
            # ========================
            rec._update_machine_usage_hours(old_duration)
            
            # ========================
            # TỰ ĐỘNG TẠO PHIẾU XUẤT KHO
            # ========================
            rec._create_stock_picking_from_orders()

        return True
    
    def action_start_session(self):
        """Bắt đầu phiên từ draft với kiểm tra đầy đủ"""
        for rec in self:
            # Kiểm tra 1: Phiên phải ở trạng thái draft
            if rec.session_state != 'draft':
                raise UserError(_("Chỉ có thể bắt đầu phiên ở trạng thái Draft"))
            
            # Kiểm tra 2: Account phải tồn tại
            if not rec.account_id:
                raise ValidationError(_("Tài khoản là bắt buộc để bắt đầu phiên"))
            
            # Kiểm tra 3: Account không có phiên nào đang chạy
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
            
            # Kiểm tra 4: Machine phải tồn tại
            if not rec.product_machine_id:
                raise ValidationError(_("Máy là bắt buộc để bắt đầu phiên"))
            
            # Kiểm tra 5: Balance phải > 0
            if rec.account_id.balance <= 0:
                raise ValidationError(_("Số dư tài khoản không đủ để bắt đầu phiên"))
            
            # Kiểm tra 6: Price per hour phải > 0
            if rec.price_per_hour <= 0:
                raise ValidationError(_("Giá mỗi giờ của máy phải lớn hơn 0. Vui lòng kiểm tra cấu hình sản phẩm máy."))
            
            # Set session_state='running' và start_time=now()
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
        
        # Làm tròn thành số thập phân
        new_usage_hours = round(new_usage, 2)
        
        if new_usage_hours > 0:
            # Cập nhật usage_hours của máy với context skip_readonly
            current_usage = product_template.usage_hours or 0.0
            updated_usage = current_usage + new_usage_hours
            
            try:
                product_template.with_context(skip_readonly=True).write({
                    'usage_hours': updated_usage
                })
            except Exception as e:
                # Log lỗi nhưng không dừng quá trình đóng phiên
                pass

    # ==========================
    # PHIẾU XUẤT KHO TỰ ĐỘNG
    # ==========================
    def _create_stock_picking_from_orders(self):
        """
        Returns:
            stock.picking: Phiếu xuất được tạo, hoặc None nếu không có order
        """
        self.ensure_one()

        # Lấy tất cả các order đã hoàn thành ('done')
        done_orders = self.order_ids.filtered(lambda o: o.order_state == 'done')
        
        if not done_orders:
            return None
        
        # Kiểm tra tránh tạo phiếu xuất trùng lặp
        existing_picking = self.env['stock.picking'].search([
            ('origin', '=', f'cyber.session,{self.id}'),
            ('state', 'in', ['draft', 'confirmed', 'assigned', 'done'])
        ], limit=1)
        
        if existing_picking:
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
                return None

            # ==========================================
            # BƯỚC 4: CONFIRM & VALIDATE PHIẾU XUẤT
            # ==========================================
            picking.action_confirm()
            picking.button_validate()

            return picking

        except Exception as e:
            # Xóa picking nếu có lỗi trong quá trình tạo
            if 'picking' in locals() and picking.exists():
                picking.unlink()
            
            error_msg = str(e)
            raise UserError(
                _("Lỗi khi tạo phiếu xuất kho tự động:\n%s") % error_msg
            )

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
        return session

    # ========================
    # CRON AUTO-CLOSE-SESSIONS
    # ========================
    @api.model
    def action_autoclose_sessions(self):
        """Tự động đóng các phiên đã hết thời gian dự kiến"""
        now = fields.Datetime.now()
        
        # Tìm các phiên running có end_time_expected <= now
        sessions = self.search([
            ('session_state', '=', 'running'),
            ('end_time_expected', '!=', False),
            ('end_time_expected', '<=', now)
        ], limit=50)
        
        closed_count = 0
        
        for session in sessions:
            try:
                # Lưu duration trước khi update
                old_duration = session.duration
                
                # Đóng phiên với end_time = end_time_expected (không kiểm tra order)
                session.write({
                    'end_time': session.end_time_expected,
                    'session_state': 'closed'
                })
                
                # Tính lại các field computed
                session._compute_duration()
                session._compute_total_service()
                session._compute_total_sale()
                
                # Cập nhật usage hours
                session._update_machine_usage_hours(old_duration)
                
                # Cập nhật trạng thái máy
                if session.product_machine_id and hasattr(session.product_machine_id, 'machine_using_status'):
                    session.product_machine_id.product_tmpl_id.with_context(skip_readonly=True).write({
                        'machine_using_status': 'offline'
                    })
                
                # Tạo phiếu xuất kho
                session._create_stock_picking_from_orders()
                
                closed_count += 1
            except Exception:
                continue
        
        return closed_count
