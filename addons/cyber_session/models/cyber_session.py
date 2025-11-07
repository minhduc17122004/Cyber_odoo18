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
    end_time_expected = fields.Datetime(string='Thời gian đóng phiên dự kiến', compute='_compute_end_time_expected', store=True, help="Thời gian dự kiến phiên sẽ tự động đóng dựa trên balance và giá máy. Tự động cập nhật khi nạp tiền hoặc mua order.")
    duration = fields.Float(string='Duration', compute='_compute_duration', store=True, digits=(12, 6))
    price_per_hour = fields.Float(string='Price per Hour (VND)', required=True, digits=(16, 2))
    total_cost = fields.Float(string='Total Cost (VND)', compute='_compute_total_cost', store=True, digits=(16, 2))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='Status', default='running', tracking=True)

    order_ids = fields.One2many('cyber.sale_order_in_session', 'session_id', string='Orders in Session')
    
    time_played = fields.Float(
        string='Thời gian đã chơi (giờ)',
        compute='_compute_time_played',
        store=False,
        digits=(12, 6),
        help="Thời gian đã chơi tính từ lúc bắt đầu session đến hiện tại (nếu đang chơi) hoặc đến lúc kết thúc (nếu đã đóng)."
    )
    
    play_time_remaining_virtual = fields.Float(
        string='Thời gian còn lại',
        compute='_compute_play_time_remaining_virtual',
        store=False,
        digits=(12, 6),
        help="Thời gian còn lại có thể chơi dựa trên balance hiện tại và chi phí đã phát sinh. Cập nhật real-time."
    )
    
    virtual_balance = fields.Float(
        string='Virtual Balance',
        compute='_compute_virtual_balance',
        store=False,
        digits=(16, 2),
        help="Số dư khả dụng trong phiên = balance - chi phí đã phát sinh (chưa charge)"
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

    @api.depends('duration', 'price_per_hour', 'order_ids.line_total')
    def _compute_total_cost(self):
        """Tổng chi phí = (duration * price_per_hour) + tổng orders"""
        for rec in self:
            session_cost = rec.duration * rec.price_per_hour
            orders_cost = sum(rec.order_ids.mapped('line_total'))
            rec.total_cost = round(session_cost + orders_cost, 6)

    @api.depends('account_id.balance', 'account_id.total_spent', 'start_time', 'price_per_hour', 'state')
    def _compute_end_time_expected(self):
        """
        ✅ ENHANCED: Tính thời gian kết thúc dự kiến và TẠO TRANSACTION khi hết giờ
        - Tự động cập nhật khi balance thay đổi (nạp tiền, mua order)
        - Tính virtual balance = balance - chi phí đã phát sinh
        - Khi end_time_expected <= now → TẠO TRANSACTION NGAY
        """
        for rec in self:
            # Nếu session đã đóng, giữ nguyên end_time_expected
            if rec.state == 'closed':
                continue
            
            acc = rec.account_id
            if not acc or not rec.start_time or rec.price_per_hour <= 0:
                rec.end_time_expected = False
                continue
            
            # Tính thời gian đã chơi
            now = fields.Datetime.now()
            time_played_seconds = (now - rec.start_time).total_seconds()
            time_played_hours = time_played_seconds / 3600.0
            
            # Tính chi phí đã phát sinh (chưa được charge vào transaction)
            cost_so_far = time_played_hours * rec.price_per_hour
            
            # Tính virtual balance (balance thực tế - chi phí đã phát sinh)
            virtual_balance = acc.balance - cost_so_far
            
            # ✅ Nếu virtual balance <= 0 → Tạo transaction NGAY
            if virtual_balance <= 0:
                rec.end_time_expected = now
                
                # ✅ TẠO TRANSACTION cho tiền đã chơi (nếu chưa có transaction cho session này)
                if cost_so_far > 0:
                    # Check xem đã tạo transaction chưa (tránh duplicate)
                    existing_transaction = self.env['cyber.transaction'].search([
                        ('session_id', '=', rec.id),
                        ('type', '=', 'spend'),
                    ], limit=1)
                    
                    if not existing_transaction:
                        # Tạo transaction mới
                        self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
                            'account_id': acc.id,
                            'session_id': rec.id,
                            'amount': cost_so_far,
                            'type': 'spend',
                            'payment_method': 'balance',
                        })
                        rec.message_post(body=_("⚠️ Balance depleted! Transaction created for %.2f hours (Cost: %s VND)") % (time_played_hours, cost_so_far))
            else:
                # Tính thời gian còn lại có thể chơi (giây)
                remaining_hours = virtual_balance / rec.price_per_hour
                remaining_seconds = remaining_hours * 3600
                
                # end_time_expected = now + remaining_seconds
                rec.end_time_expected = now + timedelta(seconds=remaining_seconds)

    def _compute_time_played(self):
        """
        ✅ Tính thời gian đã chơi (CHỈ để hiển thị)
        - Nếu session đang running: time_played = now - start_time
        - Nếu session đã closed: time_played = end_time - start_time (= duration)
        """
        for rec in self:
            if not rec.start_time:
                rec.time_played = 0.0
                continue
            
            if rec.state == 'running':
                # Session đang chạy → Tính từ start_time đến hiện tại
                now = fields.Datetime.now()
                time_played_seconds = (now - rec.start_time).total_seconds()
                rec.time_played = time_played_seconds / 3600.0
            elif rec.end_time:
                # Session đã đóng → Lấy duration (end_time - start_time)
                rec.time_played = rec.duration
            else:
                rec.time_played = 0.0

    def _compute_play_time_remaining_virtual(self):
        """
        ✅ Tính thời gian còn lại real-time (CHỈ để hiển thị)
        - Không lưu vào DB (store=False)
        - Dựa trên virtual balance (balance - chi phí đã phát sinh)
        """
        for rec in self:
            if rec.state != 'running' or not rec.start_time or not rec.price_per_hour:
                rec.play_time_remaining_virtual = 0.0
                continue

            acc = rec.account_id
            if not acc or acc.balance <= 0:
                rec.play_time_remaining_virtual = 0.0
                continue

            # Tính thời gian đã chơi
            now = fields.Datetime.now()
            time_played_hours = (now - rec.start_time).total_seconds() / 3600.0
            
            # Tính chi phí đã phát sinh (chưa được charge)
            cost_so_far = time_played_hours * rec.price_per_hour
            
            # Tính virtual balance
            virtual_balance = acc.balance - cost_so_far
            
            # Tính thời gian còn lại
            if virtual_balance > 0 and rec.price_per_hour > 0:
                hours_remaining = virtual_balance / rec.price_per_hour
                rec.play_time_remaining_virtual = max(0, hours_remaining)
            else:
                rec.play_time_remaining_virtual = 0.0

    @api.depends('account_id.balance', 'start_time', 'price_per_hour', 'state')
    def _compute_virtual_balance(self):
        """
        ✅ Tính virtual balance = balance - chi phí đã phát sinh
        - Đây là số dư thực tế có thể dùng để mua order
        """
        for rec in self:
            if rec.state != 'running' or not rec.start_time:
                rec.virtual_balance = rec.account_id.balance if rec.account_id else 0.0
                continue
            
            acc = rec.account_id
            if not acc:
                rec.virtual_balance = 0.0
                continue
            
            # Tính chi phí đã phát sinh
            now = fields.Datetime.now()
            time_played_hours = (now - rec.start_time).total_seconds() / 3600.0
            cost_so_far = time_played_hours * rec.price_per_hour
            
            # Virtual balance = balance thực - chi phí đã phát sinh
            rec.virtual_balance = max(0, acc.balance - cost_so_far)
    
    # ========================
    # MAIN LOGIC
    # ========================
    def _finalize_close(self):
        """Xử lý khi session kết thúc - Tạo transaction nếu chưa có (đóng thủ công)"""
        for rec in self:
            acc = rec.account_id
            if not acc:
                continue
            
            # ✅ Tính duration local
            if rec.start_time and rec.end_time:
                duration_hours = (rec.end_time - rec.start_time).total_seconds() / 3600
            else:
                duration_hours = 0.0
            
            session_cost = duration_hours * rec.price_per_hour

            # ✅ Check xem đã có transaction cho session này chưa
            existing_transaction = self.env['cyber.transaction'].search([
                ('session_id', '=', rec.id),
                ('type', '=', 'spend'),
            ], limit=1)
            
            # ✅ Nếu có transaction → Tạo mới (trường hợp đóng thủ công)
            if existing_transaction and session_cost > 0:
                if acc.balance < session_cost:
                    # Không đủ tiền trả phí chơi
                    rec.message_post(body=_("⚠️ Session closed but insufficient balance to pay session fee. Cost: %s VND, Balance: %s VND") % (session_cost, acc.balance))
                else:
                    # Tạo transaction
                    self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
                        'account_id': acc.id,
                        'session_id': rec.id,
                        'amount': session_cost,
                        'type': 'spend',
                        'payment_method': 'balance',
                    })
                    rec.message_post(body=_("✅ Transaction created for manual close: %.2f hours (Cost: %s VND)") % (duration_hours, session_cost))

            # ✅ Cập nhật thống kê (play_time_total)
            acc.sudo().write({
                'play_time_total': acc.play_time_total + duration_hours,
                'last_session_end': rec.end_time,
            })

            # Cập nhật customer tổng hợp
            if acc.customer_id:
                acc.customer_id._calculate_totals()

            # ✅ Log thông tin
            if existing_transaction:
                rec.message_post(body=_("Session closed at %s. Duration: %.2f hours (Transaction already exists)") % (rec.end_time, duration_hours))
            else:
                rec.message_post(body=_("Session closed at %s. Duration: %.2f hours") % (rec.end_time, duration_hours))

        return True

    def _close_if_expired(self):
        """
        ✅ SIMPLIFIED: Chỉ cần 1 hàm auto-close dựa trên end_time_expected
        - end_time_expected tự động update khi balance thay đổi
        - Không cần check virtual balance ở đây nữa
        """
        now = fields.Datetime.now()
        for rec in self:
            if rec.state == 'running' and rec.end_time_expected and now >= rec.end_time_expected:
                rec.with_context(skip_check=True).sudo().write({
                    'end_time': rec.end_time_expected or now,
                    'state': 'closed'
                })
                rec._finalize_close()
                rec.message_post(body=_("⏰ Session auto-closed at %s") % now)

    def action_close_manual(self):
        """Đóng thủ công"""
        for rec in self:
            if rec.state == 'closed':
                continue
            rec.with_context(skip_check=True).sudo().write({
                'end_time': fields.Datetime.now(),
                'state': 'closed'
            })
            rec._finalize_close()
            rec.message_post(body=_("👤 Session manually closed by user"))
        return True

    # ========================
    # OVERRIDE METHODS
    # ========================
    @api.model
    def create(self, vals):
        """Tạo session - Validate và set defaults"""
        if vals.get('name', 'New') == 'New':
            timestamp = fields.Datetime.now().strftime('%Y%m%d%H%M%S')
            vals['name'] = f'SES{timestamp}'

        # ✅ Set start_time nếu chưa có
        if not vals.get('start_time'):
            vals['start_time'] = fields.Datetime.now()

        session = super(CyberSession, self).create(vals)
        
        # ✅ Log session started
        session.message_post(body=_("🎮 Session started at %s. No charges applied yet.") % session.start_time)
        
        return session

    def read(self, fields=None, load='_classic_read'):
        """
        ✅ Override read() để trigger auto-close mỗi khi view được load
        - Được gọi khi: Mở form view, list view, refresh page
        - Check và đóng sessions hết hạn TRƯỚC KHI trả data về client
        """
        # ✅ Check và đóng sessions hết hạn (chỉ cho sessions đang running)
        if not self.env.context.get('skip_check'):
            self.filtered(lambda s: s.state == 'running')._close_if_expired()
        
        # ✅ Gọi super() để lấy data
        return super().read(fields, load)

    def write(self, vals):
        """
        ✅ Override write() để trigger auto-close mỗi khi có update
        - Được gọi khi: User save form, cron update, computed field update
        - Check TRƯỚC khi write để đảm bảo state mới nhất
        """
        # ✅ Check expired TRƯỚC khi write (tránh ghi đè state không đúng)
        if not self.env.context.get('skip_check'):
            self.filtered(lambda s: s.state == 'running')._close_if_expired()
        
        # ✅ Gọi super() để update data
        res = super().write(vals)
        
        # ✅ Check lại SAU khi write (nếu có update balance hoặc các field liên quan)
        if not self.env.context.get('skip_check'):
            self.filtered(lambda s: s.state == 'running')._close_if_expired()
        
        return res

    # ========================
    # CRON JOB - DỰ PHÒNG
    # ========================
    @api.model
    def cron_close_expired_sessions(self):
        """
        ✅ SIMPLIFIED: Cron job chạy mỗi 1 phút để đóng các phiên quá hạn.
        Đây là cơ chế dự phòng nếu read()/write()/search() bỏ lỡ.
        """
        now = fields.Datetime.now()
        total_closed = 0
        
        # ✅ Đóng phiên hết giờ (end_time_expected đã bao gồm cả logic hết tiền)
        expired_sessions = self.search([
            ('state', '=', 'running'),
            ('end_time_expected', '!=', False),
            ('end_time_expected', '<=', now)
        ])
        
        if expired_sessions:
            for session in expired_sessions:
                try:
                    session.with_context(skip_check=True)._close_if_expired()
                    total_closed += 1
                except Exception as e:
                    self.env['ir.logging'].sudo().create({
                        'name': 'Cyber Session Auto-Close Error',
                        'type': 'server',
                        'dbname': self.env.cr.dbname,
                        'level': 'ERROR',
                        'message': f"Failed to close session {session.name}: {str(e)}",
                        'path': 'cyber.session',
                        'line': '0',
                        'func': 'cron_close_expired_sessions',
                    })
        
        # ✅ Log kết quả
        if total_closed > 0:
            self.env['ir.logging'].sudo().create({
                'name': 'Cyber Session Auto-Close Cron',
                'type': 'server',
                'dbname': self.env.cr.dbname,
                'level': 'INFO',
                'message': f"✅ Successfully closed {total_closed} sessions at {now}",
                'path': 'cyber.session',
                'line': '0',
                'func': 'cron_close_expired_sessions',
            })
        
        return True


class CyberSaleOrderInSession(models.Model):
    _name = 'cyber.sale_order_in_session'
    _description = 'Cyber Sale Order in Session'
    _order = 'id desc'

    # ========================
    # FIELDS
    # ========================
    session_id = fields.Many2one('cyber.session', string='Session', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    price_unit = fields.Float(string='Unit Price (VND)', required=True, digits=(16, 2))
    line_total = fields.Float(string='Line Total (VND)', compute='_compute_line_total', store=True, digits=(16, 2))

    # ========================
    # COMPUTE METHODS
    # ========================
    @api.depends('quantity', 'price_unit')
    def _compute_line_total(self):
        """Tính tổng cộng của dòng đơn hàng"""
        for rec in self:
            rec.line_total = rec.quantity * rec.price_unit

    # ========================
    # OVERRIDE METHODS
    # ========================
    @api.model
    def create(self, vals):
        """Khi tạo order mới trong session:
        - ✅ KIỂM TRA virtual_balance (balance trong phiên) TRƯỚC KHI tạo order
        - ✅ Tạo transaction chi tiêu
        - ✅ Trừ tiền qua transaction (transaction.create sẽ tự động update balance)
        - ✅ Tự động đóng phiên nếu hết tiền
        """
        # ✅ Tính line_total trước khi tạo record
        product = self.env['product.product'].browse(vals.get('product_id'))
        quantity = vals.get('quantity', 1.0)
        price_unit = vals.get('price_unit', product.list_price if product else 0.0)
        line_total = quantity * price_unit
        
        # ✅ Lấy session và account
        session = self.env['cyber.session'].browse(vals.get('session_id'))
        account = session.account_id

        if session.state != 'running':
            raise UserError(_("Không thể thêm order khi phiên đã đóng."))

        # ✅ KIỂM TRA virtual_balance (balance trong phiên) TRƯỚC
        if session.virtual_balance < line_total:
            raise ValidationError(
                _("⚠️ Số dư trong phiên không đủ để mua sản phẩm này!\n\n"
                  "Cần: %s VND\n"
                  "Số dư khả dụng trong phiên: %s VND\n"
                  "Thiếu: %s VND\n\n"
                  "💡 Lưu ý: Số dư này đã trừ đi chi phí chơi game chưa được tính (%s VND)")
                % (
                    line_total,
                    session.virtual_balance,
                    line_total - session.virtual_balance,
                    account.balance - session.virtual_balance
                )
            )

        # ✅ Tạo order (AFTER validation)
        order = super(CyberSaleOrderInSession, self).create(vals)

        # ✅ Tạo transaction (transaction.create sẽ tự động update balance & total_spent)
        self.env['cyber.transaction'].sudo().with_context(from_session=True).create({
            'account_id': account.id,
            'session_id': session.id,
            'amount': order.line_total,
            'type': 'spend',
            'payment_method': 'balance',
        })

        # ✅ Odoo sẽ tự động trigger:
        #    - _compute_balance() vì total_spent changed
        #    - _compute_end_time_expected() vì balance changed
        #    - _compute_total_cost() vì order_line_ids changed
        # ✅ end_time_expected sẽ được recalc → nếu <= now → _close_if_expired() sẽ đóng

        return order
