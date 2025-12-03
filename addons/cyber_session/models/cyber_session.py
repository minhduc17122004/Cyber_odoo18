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

    # ==========================
    # CLOSE SESSION ACTION
    # ==========================
    def action_close_session(self):
        """Đóng phiên thủ công"""
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
            
            # Đóng phiên với end_time = now
            rec.write({
                'end_time': fields.Datetime.now(),
                'session_state': 'closed'
            })
            
            # Tính lại các field computed cho session
            rec._compute_duration()
            rec._compute_total_service()
            rec._compute_total_sale()
        
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
            # Price will be auto-filled via related field
            # But we can add additional validations here
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
        # Tự động sinh session ID nếu là 'New'
        if vals.get('name', 'New') == 'New':
            timestamp = fields.Datetime.now().strftime('%Y%m%d%H%M%S')
            vals['name'] = f'SES{timestamp}'

        # Chỉ set start_time khi session_state = 'running'
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
                # Đóng phiên với end_time = end_time_expected (không kiểm tra order)
                session.write({
                    'end_time': session.end_time_expected,
                    'session_state': 'closed'
                })
                
                # Tính lại các field computed
                session._compute_duration()
                session._compute_total_service()
                session._compute_total_sale()
                
                closed_count += 1
            except Exception:
                continue
        
        return closed_count
