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
            # Lọc chỉ lấy các order có order_state = 'done'
            done_orders = rec.order_ids.filtered(lambda o: o.order_state == 'done')
            rec.total_order = round(sum(done_orders.mapped('line_total')), 0)

    @api.depends('total_service', 'total_order')
    def _compute_total_sale(self):
        """Tổng chi phí = total_service + total_order"""
        for rec in self:
            rec.total_sale = round(rec.total_service + rec.total_order, 0)

    # ==========================
    # AUTO CLOSE MECHANISM
    # ==========================
    def _auto_close_if_out_of_balance(self):
        """Kiểm tra và tự động đóng phiên nếu hết tiền hoặc hết thời gian"""
        for rec in self:
            # Chỉ xử lý phiên đang running
            if rec.session_state != 'running':
                continue
            
            now = fields.Datetime.now()
            should_close = False
            reason = None
            
            # Kiểm tra điều kiện 1: Số dư account <= 0
            if rec.account_id and rec.account_id.balance <= 0:
                should_close = True
                reason = 'low_balance'
            # Kiểm tra điều kiện 2: Đã quá thời gian dự kiến kết thúc
            elif rec.end_time_expected and now >= rec.end_time_expected:
                should_close = True
                reason = 'time_expired'
            
            # Gọi action_close_session với auto=True
            if should_close and reason:
                rec.action_close_session(auto=True, reason=reason)

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
            if auto and rec.account_id:
                # Tính toán thời gian tối đa có thể chơi với số dư hiện tại
                # available_balance = account.balance - total_order
                # max_duration = available_balance / price_per_hour
                available_for_service = rec.account_id.balance - rec.total_order
                
                if available_for_service < 0:
                    available_for_service = 0
                
                if rec.price_per_hour > 0:
                    max_duration_hours = available_for_service / rec.price_per_hour
                    
                    # Tính duration hiện tại
                    if rec.start_time:
                        current_duration = (fields.Datetime.now() - rec.start_time).total_seconds() / 3600
                        
                        # Nếu duration hiện tại vượt quá max_duration, cắt end_time
                        if current_duration > max_duration_hours:
                            # Cắt end_time để duration = max_duration_hours
                            adjusted_end_time = rec.start_time + timedelta(hours=max_duration_hours)
                            rec.write({
                                'end_time': adjusted_end_time,
                                'session_state': 'closed'
                            })
                        else:
                            # Duration bình thường
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
                # Manual close hoặc balance đủ - set end_time = now()
                rec.write({
                    'end_time': fields.Datetime.now(),
                    'session_state': 'closed'
                })
            
            # Tính lại các field computed cho session
            rec._compute_duration()
            rec._compute_total_service()
            rec._compute_total_sale()

            # Tính last_session_end
            rec.account_id.update_last_dates()
            
            # Post message vào chatter khác nhau cho manual vs auto
            if auto:
                # Auto close - include reason
                if reason:
                    message = _("Session auto-closed due to %s") % reason
                else:
                    message = _("Session auto-closed")
                rec.message_post(body=message)
            else:
                # Manual close
                rec.message_post(body=_("Session closed manually"))
        
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
            
            # Post message vào chatter
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
        session.message_post(body=_("Session created in draft state."))
        return session

    # ========================
    # CRON AUTO-CLOSE
    # ========================
    @api.model
    def action_autoclose_sessions(self):
        """Tìm và đóng tất cả phiên hết hạn hoặc hết tiền (batch 50 records)"""
        now = fields.Datetime.now()
        
        # Tìm phiên có account.balance <= 0
        domain_low_balance = [
            ('session_state', '=', 'running'),
            ('account_id.balance', '<=', 0)
        ]
        
        # Tìm phiên có expected_end_time <= now
        domain_time_expired = [
            ('session_state', '=', 'running'),
            ('end_time_expected', '!=', False),
            ('end_time_expected', '<=', now)
        ]
        
        # Search với limit 50 cho mỗi domain
        sessions_low_balance = self.search(domain_low_balance, limit=50)
        sessions_time_expired = self.search(domain_time_expired, limit=50)
        
        # Kết hợp và giới hạn tổng là 50 sessions
        all_sessions = (sessions_low_balance | sessions_time_expired)
        if len(all_sessions) > 50:
            all_sessions = all_sessions[:50]
        
        closed_count = 0
        failed_sessions = []
        
        # Đóng từng session với exception handling
        for session in all_sessions:
            try:
                # Xác định reason để log
                reason = None
                if session.account_id and session.account_id.balance <= 0:
                    reason = 'low_balance'
                elif session.end_time_expected and now >= session.end_time_expected:
                    reason = 'time_expired'
                
                session.action_close_session(auto=True, reason=reason)
                closed_count += 1
            except Exception as e:
                # Lưu lại failed sessions để log
                failed_sessions.append({
                    'session_id': session.id,
                    'session_name': session.name,
                    'error': str(e)
                })
                continue
        
        # Log kết quả vào ir.logging
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
