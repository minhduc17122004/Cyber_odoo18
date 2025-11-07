# -*- coding: utf-8 -*-
from datetime import timedelta
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
    product_machine_id = fields.Many2one('product.product', string='Machine', domain=[('is_machine', '=', True)])
    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    price_per_hour = fields.Float(string='Price per Hour (VND)', required=True, digits=(16, 2))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)

    order_ids = fields.One2many('cyber.sale_order_in_session', 'session_id', string='Orders in Session')

    # Hiển thị/ghi sổ
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True, digits=(12, 6))
    total_service = fields.Float(string='Tổng tiền dịch vụ (VND)', compute='_compute_total_service', store=True, digits=(16, 2))
    total_order = fields.Float(string='Tổng tiền order (VND)', compute='_compute_total_order', store=True, digits=(16, 2))
    total_cost = fields.Float(string='Total Cost (VND)', compute='_compute_total_cost', store=True, digits=(16, 2))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # Dự kiến đóng phiên
    end_time_expected = fields.Datetime(
        string='Thời gian đóng phiên dự kiến',
        compute='_compute_end_time_expected',
        store=True,
        help="Dựa trên số tiền còn lại trong phiên (balance_in_session). Tự cập nhật khi balance hoặc order thay đổi."
    )

    # Realtime (không lưu DB)
    time_played = fields.Float(
        string='Thời gian đã chơi (giờ)',
        compute='_compute_time_played',
        store=False,
        digits=(12, 6),
        help="Nếu đang chạy: now - start_time; nếu đã đóng: end_time - start_time."
    )
    play_time_remaining_virtual = fields.Float(
        string='Thời gian còn lại (giờ)',
        compute='_compute_play_time_remaining_virtual',
        store=False,
        digits=(12, 6),
        help="Dựa trên balance_in_session realtime."
    )
    balance_in_session = fields.Float(
        string='Số tiền còn lại trong phiên (VND)',
        compute='_compute_balance_in_session',
        store=False,
        digits=(16, 2),
        help="= account.balance - service_cost_so_far - total_order"
    )

    # ========================
    # HELPERS
    # ========================
    def _service_cost_so_far(self):
        """
        Chi phí dịch vụ đến thời điểm hiện tại:
        - Nếu running: (now - start_time) * price_per_hour
        - Nếu closed: duration * price_per_hour
        """
        self.ensure_one()
        if not self.start_time or self.price_per_hour <= 0:
            return 0.0

        if self.state == 'running':
            now = fields.Datetime.now()
            played_hours = max(0.0, (now - self.start_time).total_seconds() / 3600.0)
        else:
            played_hours = self.duration or 0.0
        return round(played_hours * self.price_per_hour, 2)

    def _current_total_order(self):
        self.ensure_one()
        return round(sum(self.order_ids.mapped('line_total')), 2)

    def _balance_in_session_now(self):
        """Realtime: account.balance - service_cost_so_far - total_order"""
        self.ensure_one()
        acc = self.account_id
        if not acc:
            return 0.0
        return round((acc.balance or 0.0) - self._service_cost_so_far() - self._current_total_order(), 2)

    # ========================
    # COMPUTE METHODS
    # ========================
    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = delta.total_seconds() / 3600.0
            else:
                rec.duration = 0.0

    @api.depends('start_time', 'end_time', 'price_per_hour', 'duration')
    def _compute_total_service(self):
        for rec in self:
            # Nếu đã đóng thì tính theo duration, nếu đang chạy thì = 0 (ghi sổ chỉ khi đóng)
            if rec.state == 'closed':
                rec.total_service = round((rec.duration or 0.0) * (rec.price_per_hour or 0.0), 2)
            else:
                rec.total_service = 0.0

    @api.depends('order_ids.line_total')
    def _compute_total_order(self):
        for rec in self:
            rec.total_order = round(sum(rec.order_ids.mapped('line_total')), 2)

    @api.depends('total_service', 'total_order')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = round((rec.total_service or 0.0) + (rec.total_order or 0.0), 2)

    @api.depends('account_id.balance', 'order_ids.line_total', 'price_per_hour', 'start_time', 'state')
    def _compute_end_time_expected(self):
        """
        Dùng balance_in_session realtime để suy ra thời gian còn chơi được cho dịch vụ.
        - Nếu balance_in_session <= 0: end_time_expected = now
        - Ngược lại: end_time_expected = now + hours_remaining * 1h
        """
        now = fields.Datetime.now()
        for rec in self:
            if rec.state == 'closed' or not rec.start_time or rec.price_per_hour <= 0:
                rec.end_time_expected = False
                continue
            bis = rec._balance_in_session_now()
            if bis <= 0:
                rec.end_time_expected = now
            else:
                remaining_hours = bis / rec.price_per_hour
                rec.end_time_expected = now + timedelta(hours=max(0.0, remaining_hours))

    def _compute_time_played(self):
        for rec in self:
            if not rec.start_time:
                rec.time_played = 0.0
                continue
            if rec.state == 'running':
                now = fields.Datetime.now()
                rec.time_played = max(0.0, (now - rec.start_time).total_seconds() / 3600.0)
            elif rec.end_time:
                rec.time_played = rec.duration
            else:
                rec.time_played = 0.0

    def _compute_play_time_remaining_virtual(self):
        for rec in self:
            if rec.state != 'running' or not rec.start_time or rec.price_per_hour <= 0:
                rec.play_time_remaining_virtual = 0.0
                continue
            bis = rec._balance_in_session_now()
            rec.play_time_remaining_virtual = max(0.0, bis / rec.price_per_hour) if bis > 0 else 0.0

    def _compute_balance_in_session(self):
        for rec in self:
            rec.balance_in_session = rec._balance_in_session_now()

    # ========================
    # CLOSING LOGIC
    # ========================
    def _create_service_transaction_if_needed(self, amount, when_label):
        """
        Tạo transaction cho tiền dịch vụ nếu chưa có
        - when_label: 'auto' hoặc 'manual'
        - note: 'service:auto' hoặc 'service:manual'
        """
        self.ensure_one()
        
        # ✅ Kiểm tra account_id trước
        if not self.account_id:
            return False
        
        # ✅ Check duplicate dựa trên note
        existed = self.env['cyber.transaction'].search([
            ('session_id', '=', self.id),
            ('type', '=', 'spend'),
            ('note', '=', f'service:{when_label}'),  # ← Kiểm tra note
        ], limit=1)
        
        if existed:
            return False  # Đã có transaction với note này rồi
        
        # ✅ Kiểm tra amount > 0
        if amount <= 0:
            return False
        
        # ✅ Tạo transaction với note
        self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
            'account_id': self.account_id.id,
            'session_id': self.id,
            'amount': amount,
            'type': 'spend',
            'payment_method': 'balance',
            'note': f'service:{when_label}',  # ← Set note
        })
        return True

    def _finalize_close(self, when_label='manual'):
        """
        Khi session kết thúc:
        - Tính duration, chốt end_time nếu thiếu.
        - Tạo transaction cho tiền dịch vụ còn lại (nếu chưa tạo).
        - Cập nhật thống kê account và gọi tổng hợp khách hàng (nếu có).
        """
        for rec in self:
            if not rec.end_time:
                rec.end_time = fields.Datetime.now()

            # Chốt duration và service ở thời điểm đóng
            duration_hours = max(0.0, (rec.end_time - rec.start_time).total_seconds() / 3600.0) if rec.start_time else 0.0
            session_service_cost = round(duration_hours * (rec.price_per_hour or 0.0), 2)

            # Tạo transaction cho dịch vụ lúc đóng (ghi note để tránh double)
            rec._create_service_transaction_if_needed(session_service_cost, when_label)

            # Cập nhật trạng thái và tổng hợp
            rec.sudo().write({'state': 'closed'})
            
            # ✅ Chỉ log nếu record đã được lưu (có ID thật)
            if rec.id and not isinstance(rec.id, models.NewId):
                rec.message_post(body=_("Session closed at %s. Duration: %.2f hours") % (rec.end_time, duration_hours))

            acc = rec.account_id
            if acc:
                acc.sudo().write({
                    'play_time_total': (acc.play_time_total or 0.0) + duration_hours,
                    'last_session_end': rec.end_time,
                })
                if acc.customer_id:
                    acc.customer_id._calculate_totals()
        return True

    def _close_if_expired(self):
        """
        Đóng nếu:
        - end_time_expected <= now
        - hoặc balance_in_session_now <= 0
        """
        now = fields.Datetime.now()
        for rec in self:
            # ✅ Bỏ qua record chưa được lưu (NewId)
            if not rec.id or isinstance(rec.id, models.NewId):
                continue
            
            if rec.state != 'running':
                continue
            
            # ✅ Bỏ qua record chưa có account hoặc start_time
            if not rec.account_id or not rec.start_time:
                continue
            
            must_close = False
            if rec.end_time_expected and now >= rec.end_time_expected:
                must_close = True
            if rec._balance_in_session_now() <= 0:
                must_close = True
            if must_close:
                rec.with_context(skip_check=True).sudo().write({
                    'end_time': rec.end_time_expected or now,
                    'state': 'closed'
                })
                rec._finalize_close(when_label='auto')
                
                # ✅ Chỉ log nếu record đã được lưu
                if rec.id and not isinstance(rec.id, models.NewId):
                    rec.message_post(body=_("⏰ Session auto-closed at %s") % now)
    
    def action_start_session(self):
        """Start session from draft"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError('Only draft sessions can be started!')
        if not self.account_id:
            raise ValidationError('Account is required to start session!')
        if not self.price_per_hour or self.price_per_hour <= 0:
            raise ValidationError('Price per hour must be greater than 0!')
        
        self.write({
            'state': 'running',
            'start_time': fields.Datetime.now()
        })
        
        # Message post only on saved records
        if self.id and not isinstance(self.id, models.NewId):
            self.message_post(body=f"Session started at {self.start_time}")
        return True
    
    def action_close_manual(self):
        """Đóng phiên thủ công"""
        for rec in self:
            if rec.state != 'running':
                continue
            rec.with_context(skip_check=True).sudo().write({
                'end_time': fields.Datetime.now(),
                'state': 'closed'
            })
            rec._finalize_close(when_label='manual')
            
            # ✅ Chỉ log nếu record đã được lưu
            if rec.id and not isinstance(rec.id, models.NewId):
                rec.message_post(body=_("👤 Session manually closed by user"))
        return True

    # ========================
    # OVERRIDES
    # ========================
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            timestamp = fields.Datetime.now().strftime('%Y%m%d%H%M%S')
            vals['name'] = f'SES{timestamp}'
        
        # Only set start_time if state is running
        if vals.get('state') == 'running' and not vals.get('start_time'):
            vals['start_time'] = fields.Datetime.now()
        
        session = super().create(vals)
        
        # Log only for running sessions
        if session.state == 'running' and session.id and not isinstance(session.id, models.NewId):
            session.message_post(body=_("🎮 Session started at %s.") % session.start_time)
        
        return session

    def read(self, fields=None, load='_classic_read'):
        if not self.env.context.get('skip_check'):
            self.filtered(lambda s: s.state == 'running')._close_if_expired()
        return super().read(fields, load)

    def write(self, vals):
        if not self.env.context.get('skip_check'):
            self.filtered(lambda s: s.state == 'running')._close_if_expired()
        res = super().write(vals)
        if not self.env.context.get('skip_check'):
            self.filtered(lambda s: s.state == 'running')._close_if_expired()
        return res

    # ========================
    # CRON DỰ PHÒNG
    # ========================
    @api.model
    def cron_close_expired_sessions(self):
        now = fields.Datetime.now()
        expired_sessions = self.search([
            ('state', '=', 'running'),
            ('end_time_expected', '!=', False),
            ('end_time_expected', '<=', now)
        ])
        for s in expired_sessions:
            try:
                s.with_context(skip_check=True)._close_if_expired()
            except Exception as e:
                self.env['ir.logging'].sudo().create({
                    'name': 'Cyber Session Auto-Close Error',
                    'type': 'server',
                    'dbname': self.env.cr.dbname,
                    'level': 'ERROR',
                    'message': f"Failed to close session {s.name}: {str(e)}",
                    'path': 'cyber.session',
                    'line': '0',
                    'func': 'cron_close_expired_sessions',
                })
        return True
