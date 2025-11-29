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
    total_cost = fields.Float(string='Total Cost (VND)', compute='_compute_total_cost', store=True, digits=(16, 0))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)

    order_ids = fields.One2many('cyber.sale_order_in_session', 'session_id', string='Orders in Session')
    transaction_id = fields.Many2one(
    'cyber.transaction',
    string='Giao dịch liên quan',
    ondelete='set null'
)

    # ========================
    # NEW COMPUTED FIELDS
    # ========================
    available_balance = fields.Float(
        string='Available Balance (VND)',
        compute='_compute_available_balance',
        store=True,
        tracking=True,
        digits=(16, 0)
    )
    
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

    @api.depends('account_id.balance', 'total_cost')
    def _compute_available_balance(self):
        """Tính số dư khả dụng = account.balance - total_cost"""
        for rec in self:
            if rec.account_id:
                rec.available_balance = round(rec.account_id.balance - rec.total_cost, 0)
            else:
                rec.available_balance = 0.0

    @api.depends('start_time', 'state')
    def _compute_time_played(self):
        """Tính thời gian đã chơi (giờ)"""
        for rec in self:
            if rec.state == 'running' and rec.start_time:
                delta = fields.Datetime.now() - rec.start_time
                rec.time_played = delta.total_seconds() / 3600
            else:
                rec.time_played = 0.0

    @api.depends('available_balance', 'price_per_hour')
    def _compute_time_remaining(self):
        """Tính thời gian còn lại (giờ)"""
        for rec in self:
            if rec.available_balance > 0 and rec.price_per_hour > 0:
                rec.time_remaining = rec.available_balance / rec.price_per_hour
            else:
                rec.time_remaining = 0.0

    @api.depends('duration', 'price_per_hour', 'state')
    def _compute_total_service(self):
        """Tính chi phí dịch vụ (giờ chơi)"""
        for rec in self:
            if rec.state == 'closed':
                rec.total_service = round(rec.duration * rec.price_per_hour, 0)
            else:
                rec.total_service = 0.0

    @api.depends('order_ids.line_total')
    def _compute_total_order(self):
        """Tính tổng chi phí đơn hàng"""
        for rec in self:
            rec.total_order = round(sum(rec.order_ids.mapped('line_total')), 0)

    @api.depends('total_service', 'total_order')
    def _compute_total_cost(self):
        """Tổng chi phí = total_service + total_order"""
        for rec in self:
            rec.total_cost = round(rec.total_service + rec.total_order, 0)

    # ==========================
    # AUTO CLOSE WHEN OUT OF BALANCE
    # ==========================
    def _auto_close_if_out_of_balance(self):
        """Đóng phiên tự động khi chi phí đạt đến số dư tài khoản."""
        # Thay thế logic cũ bằng gọi _check_auto_close()
        self._check_auto_close()
    
    def _check_auto_close(self):
        """
        Kiểm tra và tự động đóng phiên nếu cần.
        
        Conditions:
        - state = 'running'
        - available_balance <= 0 OR now >= expected_end_time
        
        Actions:
        - Call action_close_session(auto=True)
        - Determine reason: 'low_balance' or 'time_expired'
        """
        for rec in self:
            # Kiểm tra state = 'running'
            if rec.state != 'running':
                continue
            
            # Kiểm tra điều kiện auto-close
            now = fields.Datetime.now()
            should_close = False
            reason = None
            
            # Kiểm tra available_balance <= 0
            if rec.available_balance <= 0:
                should_close = True
                reason = 'low_balance'
            # Kiểm tra now >= expected_end_time
            elif rec.end_time_expected and now >= rec.end_time_expected:
                should_close = True
                reason = 'time_expired'
            
            # Gọi action_close_session(auto=True) với reason phù hợp
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

    # ========================
    # MAIN LOGIC
    # ========================
    def _finalize_close(self):
        """
        Xử lý khi session kết thúc.
        
        Logic:
        - Compute duration, total_service, total_cost
        - Create transaction for service
        - Update account play_time_total and last_session_end
        - Update customer totals and segment
        - Log warning if balance < 0
        
        Note: Logic cắt duration đã được xử lý trong action_close_session()
        """
        for rec in self:
            acc = rec.account_id
            if not acc:
                continue

            # Tính lại thời lượng & chi phí cho đúng
            rec._compute_duration()
            rec._compute_total_service()
            rec._compute_total_cost()

            # Sử dụng total_service đã được tính
            service_cost = rec.total_service

            # Tạo transaction cho dịch vụ (nếu có)
            if service_cost > 0:
                self.env['cyber.transaction'].create({
                    'account_id': acc.id,
                    'session_id': rec.id,
                    'type': 'spend',
                    'amount': service_cost,
                    'payment_method': 'cash',
                })

            # Cập nhật thông tin account
            # play_time_total và last_session_end sẽ trigger customer._compute_totals() tự động
            acc.write({
                'play_time_total': acc.play_time_total + rec.duration,
                'last_session_end': rec.end_time
            })

            # Đảm bảo account.balance >= 0 sau khi đóng
            if acc.balance < 0:
                # Log warning nếu balance bị âm
                self.env['ir.logging'].create({
                    'name': 'Cyber Session Warning',
                    'type': 'server',
                    'dbname': self.env.cr.dbname,
                    'level': 'WARNING',
                    'message': f'Account {acc.name} has negative balance {acc.balance} after closing session {rec.name}',
                    'path': 'cyber.session',
                    'line': '0',
                    'func': '_finalize_close',
                })

    # ==========================
    # CLOSE SESSION ACTION
    # ==========================
    def action_close_session(self, auto=False, reason=None):
        """
        Đóng phiên thủ công hoặc tự động.
        
        Parameters:
        - auto (bool): True nếu được gọi từ auto-close mechanism
        - reason (str): Lý do đóng tự động (e.g., 'low_balance', 'time_expired')
        
        Preconditions:
        - state = 'running'
        
        Actions:
        - Set end_time = now()
        - Set state = 'closed'
        - Call _finalize_close()
        - Post message to chatter (khác nhau giữa manual và auto)
        
        Note: Nếu auto=True và balance không đủ, cắt duration để balance = 0
        """
        for rec in self:
            # Kiểm tra state = 'running'
            if rec.state != 'running':
                raise UserError(_("Chỉ có thể đóng phiên đang chạy"))
            
            # Xử lý trường hợp auto=True và balance không đủ
            # Cắt duration để balance = 0
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
                                'state': 'closed'
                            })
                        else:
                            # Duration bình thường
                            rec.write({
                                'end_time': fields.Datetime.now(),
                                'state': 'closed'
                            })
                    else:
                        rec.write({
                            'end_time': fields.Datetime.now(),
                            'state': 'closed'
                        })
                else:
                    rec.write({
                        'end_time': fields.Datetime.now(),
                        'state': 'closed'
                    })
            else:
                # Manual close hoặc balance đủ - set end_time = now()
                rec.write({
                    'end_time': fields.Datetime.now(),
                    'state': 'closed'
                })
            
            # Gọi _finalize_close() để xử lý chi phí cuối cùng
            rec._finalize_close()
            
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
            # Kiểm tra state = 'draft'
            if rec.state != 'draft':
                raise UserError(_("Chỉ có thể bắt đầu phiên ở trạng thái Draft"))
            
            # Kiểm tra account_id exists
            if not rec.account_id:
                raise ValidationError(_("Tài khoản là bắt buộc để bắt đầu phiên"))
            
            # Kiểm tra machine exists
            if not rec.product_machine_id:
                raise ValidationError(_("Máy là bắt buộc để bắt đầu phiên"))
            
            # Kiểm tra balance > 0
            if rec.account_id.balance <= 0:
                raise ValidationError(_("Số dư tài khoản không đủ để bắt đầu phiên"))
            
            # Kiểm tra price_per_hour > 0 (from machine)
            if rec.price_per_hour <= 0:
                raise ValidationError(_("Giá mỗi giờ của máy phải lớn hơn 0. Vui lòng kiểm tra cấu hình sản phẩm máy."))
            
            # Set state='running', start_time=now()
            now = fields.Datetime.now()
            rec.write({
                'start_time': now,
                'state': 'running'
            })
            
            # Trigger compute expected_end_time (tự động qua @api.depends)
            # Post message vào chatter với format "Session started at HH:MM"
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
        if vals.get('name', 'New') == 'New':
            timestamp = fields.Datetime.now().strftime('%Y%m%d%H%M%S')
            vals['name'] = f'SES{timestamp}'

        # Chỉ set start_time khi state = 'running'
        if vals.get('state') != 'running':
            vals.pop('start_time', None)

        session = super(CyberSession, self).create(vals)
        session.message_post(body=_("Session created in draft state."))
        return session




    # ========================
    # CRON AUTO-CLOSE
    # ========================
    @api.model
    def action_autoclose_sessions(self):
        """
        Tìm và đóng tất cả phiên hết hạn hoặc hết tiền.
        
        Search Domain:
        - state = 'running'
        - available_balance <= 0 OR expected_end_time <= now()
        
        Actions:
        - Process in batches of 50
        - Call action_close_session(auto=True) for each
        - Log to ir.logging
        
        Returns:
        - Number of sessions closed
        """
        # Subtask 7.1: Viết search domain tìm phiên hết hạn
        # state='running' AND (available_balance <= 0 OR expected_end_time <= now)
        now = fields.Datetime.now()
        
        # Tìm phiên với available_balance <= 0
        domain_low_balance = [
            ('state', '=', 'running'),
            ('available_balance', '<=', 0)
        ]
        
        # Tìm phiên với expected_end_time <= now
        domain_time_expired = [
            ('state', '=', 'running'),
            ('end_time_expected', '!=', False),
            ('end_time_expected', '<=', now)
        ]
        
        # Subtask 7.2: Xử lý batch 50 records mỗi lần
        # Sử dụng limit=50 trong search
        sessions_low_balance = self.search(domain_low_balance, limit=50)
        sessions_time_expired = self.search(domain_time_expired, limit=50)
        
        # Kết hợp và loại bỏ trùng lặp
        all_sessions = (sessions_low_balance | sessions_time_expired)
        
        # Giới hạn tổng số phiên xử lý là 50
        if len(all_sessions) > 50:
            all_sessions = all_sessions[:50]
        
        closed_count = 0
        failed_sessions = []
        
        # Subtask 7.3: Gọi action_close_session(auto=True) cho mỗi session
        # Xử lý exception để không block toàn bộ batch
        for session in all_sessions:
            try:
                # Xác định reason
                reason = None
                if session.available_balance <= 0:
                    reason = 'low_balance'
                elif session.end_time_expected and now >= session.end_time_expected:
                    reason = 'time_expired'
                
                # Gọi action_close_session(auto=True)
                session.action_close_session(auto=True, reason=reason)
                closed_count += 1
            except Exception as e:
                # Xử lý exception để không block toàn bộ batch
                failed_sessions.append({
                    'session_id': session.id,
                    'session_name': session.name,
                    'error': str(e)
                })
                continue
        
        # Subtask 7.4: Ghi log vào ir.logging
        # Log số lượng phiên đã đóng, timestamp
        # Level: INFO
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
        
        # Subtask 7.5: Return số lượng sessions đã đóng
        return closed_count
