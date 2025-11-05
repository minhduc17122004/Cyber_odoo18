# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CyberSession(models.Model):
    _name = 'cyber.session'
    _description = 'Cyber Game Session'
    _inherit = ['mail.thread']
    _order = 'name desc'

    # ========================
    # FIELDS
    # ========================
    name = fields.Char(string='Mã phiên', required=True, readonly=True, copy=False, default='New')
    account_id = fields.Many2one('cyber.account', string='Tài khoản', required=True, ondelete='cascade')
    cyber_product_machine_id = fields.Many2one(
        'cyber.product',
        string='Máy',
        domain=[('is_machine', '=', True)],
        required=True,
        ondelete='restrict'
    )
    start_time = fields.Datetime(string='Thời gian bắt đầu')
    end_time = fields.Datetime(string='Thời gian kết thúc')
    end_time_expected = fields.Datetime(string='Thời gian kết thúc dự kiến', compute='_compute_end_time_expected', store=True)
    duration = fields.Float(string='Thời lượng (giờ)', compute='_compute_duration', store=True, digits=(12, 6))
    
    # Virtual field - Real-time countdown (chỉ hiển thị, không dùng cho logic nghiệp vụ)
    play_time_remaining_virtual = fields.Float(
        string='Thời gian còn lại (giờ) - Real-time',
        compute='_compute_play_time_remaining_virtual',
        store=False,  # Không lưu DB
        digits=(12, 6)
    )
    play_time_remaining_virtual_seconds = fields.Float(
        string='Thời gian còn lại (giây) - Real-time',
        compute='_compute_play_time_remaining_virtual',
        store=False
    )
    
    price_per_hour = fields.Float(
        string='Giá theo giờ (VND)',
        compute='_compute_price_per_hour',
        store=True,
        digits=(16, 2),
        readonly=True
    )
    total_cost = fields.Float(string='Tổng chi phí (VND)', compute='_compute_total_cost', store=True, digits=(16, 2))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='Trạng thái', default='running', tracking=True)

    order_ids = fields.One2many('cyber.sale_order_in_session', 'session_id', string='Đơn hàng trong phiên')

    # ========================
    # COMPUTE
    # ========================
    @api.depends('cyber_product_machine_id', 'cyber_product_machine_id.price_per_hour')
    def _compute_price_per_hour(self):
        """Tự động lấy giá giờ từ máy được chọn"""
        for rec in self:
            if rec.cyber_product_machine_id and rec.cyber_product_machine_id.price_per_hour > 0:
                rec.price_per_hour = rec.cyber_product_machine_id.price_per_hour
            else:
                rec.price_per_hour = 0.0

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
        """Tổng chi phí = (giờ chơi * giá/giờ) + tổng đơn hàng"""
        for rec in self:
            session_cost = rec.duration * rec.price_per_hour
            orders_cost = sum(rec.order_ids.mapped('line_total'))
            rec.total_cost = round(session_cost + orders_cost, 2)

    @api.depends('account_id.play_time_remaining_seconds', 'start_time')
    def _compute_end_time_expected(self):
        """Tính thời gian kết thúc dự kiến dựa vào số giờ còn lại"""
        for rec in self:
            acc = rec.account_id
            if acc and rec.start_time and acc.play_time_remaining_seconds > 0:
                rec.end_time_expected = rec.start_time + timedelta(seconds=acc.play_time_remaining_seconds)
            else:
                rec.end_time_expected = False

    def _compute_play_time_remaining_virtual(self):
        """
        Tính thời gian chơi còn lại REAL-TIME cho phiên hiện tại.
        Field này CHỈ để hiển thị, KHÔNG dùng cho logic nghiệp vụ.
        Logic nghiệp vụ (transaction, _finalize_close) vẫn dùng account.play_time_remaining_seconds
        """
        for rec in self:
            acc = rec.account_id
            
            # Chỉ tính cho session đang running
            if rec.state != 'running' or not rec.start_time or not acc:
                rec.play_time_remaining_virtual = 0.0
                rec.play_time_remaining_virtual_seconds = 0.0
                continue
            
            if rec.price_per_hour > 0:
                # ===== REAL-TIME CALCULATION =====
                # Tính thời gian đã chơi
                now = fields.Datetime.now()
                time_played_seconds = (now - rec.start_time).total_seconds()
                time_played_hours = time_played_seconds / 3600.0
                
                # Tính chi phí đã phát sinh (chưa được trừ vào balance thật)
                cost_so_far = time_played_hours * rec.price_per_hour
                
                # Tính "virtual balance" = balance hiện tại - chi phí đã chơi
                virtual_balance = acc.balance - cost_so_far
                
                if virtual_balance > 0:
                    # Tính thời gian còn lại CÓ THỂ chơi với virtual balance
                    hours_remaining = virtual_balance / rec.price_per_hour
                    rec.play_time_remaining_virtual = hours_remaining
                    rec.play_time_remaining_virtual_seconds = hours_remaining * 3600
                else:
                    # Hết tiền (virtual balance <= 0)
                    rec.play_time_remaining_virtual = 0.0
                    rec.play_time_remaining_virtual_seconds = 0.0
            else:
                rec.play_time_remaining_virtual = 0.0
                rec.play_time_remaining_virtual_seconds = 0.0

    # ========================
    # MAIN LOGIC
    # ========================
    def action_start(self):
        """Bắt đầu session"""
        for rec in self:
            acc = rec.account_id
            if not acc:
                raise UserError(_("Không tìm thấy tài khoản."))
            if acc.balance <= 0:
                raise UserError(_("Số dư không đủ để bắt đầu session."))
            if not rec.cyber_product_machine_id:
                raise UserError(_("Vui lòng chọn máy để bắt đầu session."))
            if rec.price_per_hour <= 0:
                raise UserError(_("Giá giờ của máy không hợp lệ. Vui lòng kiểm tra cấu hình máy."))
            rec.start_time = fields.Datetime.now()
            rec.state = 'running'
            rec.message_post(body=_("🔵 Phiên chơi bắt đầu trên máy %s lúc %s.") % (rec.cyber_product_machine_id.name, rec.start_time))

    def _finalize_close(self, auto=False):
        for rec in self:
            acc = rec.account_id
            if not acc or rec.state == 'closed':
                continue

            # 1. Xác định thời điểm kết thúc
            end_time_now = rec.end_time_expected if auto and rec.end_time_expected else fields.Datetime.now()
            rec.with_context(skip_check=True).write({'end_time': end_time_now})

            if rec.total_cost <= 0:
                raise UserError(_("Chi phí phiên chơi không hợp lệ."))

            # 2. Tính số tiền thực tế
            actual_amount = min(rec.total_cost, acc.balance)

            # 3. Ghi transaction nếu có tiền
            if actual_amount > 0:
                self.env['cyber.transaction'].with_context(from_session=True).create({
                    'account_id': acc.id,
                    'session_id': rec.id,
                    'amount': actual_amount,
                    'type': 'spend',
                    'payment_method': 'balance',
                })
            else:
                rec.message_post(body=_("⚠️ Phiên chơi hết tiền trước khi kết thúc, không thể trừ thêm."))

            # 4. Cập nhật account
            acc.sudo().write({
                'play_time_total': acc.play_time_total + rec.duration,
                'last_session_end': end_time_now,
            })

            if acc.customer_id:
                acc.customer_id._calculate_totals()

            # 5. Đóng phiên
            rec.with_context(skip_check=True).write({'state': 'closed'})
            msg_type = "🟠" if auto else "🟢"
            rec.message_post(body=_("%s Phiên chơi đóng lúc %s.") % (msg_type, end_time_now))


    def action_close_manual(self):
        """Đóng thủ công (do nhân viên thao tác)"""
        for rec in self:
            if rec.state == 'closed':
                continue
            rec._finalize_close(auto=False)
        return True

    def _action_close_auto(self):
        """Đóng session auto khi hết giờ dự kiến"""
        now = fields.Datetime.now()
        for rec in self.sudo():
            if rec.state == 'running' and rec.end_time_expected and now >= rec.end_time_expected:
                rec._finalize_close(auto=True)

    # ========================
    # OVERRIDE
    # ========================
    @api.model
    def create(self, vals):
        # Tạo mã phiên tự động
        if vals.get('name', 'New') == 'New':
            timestamp = fields.Datetime.now().strftime('%Y%m%d%H%M%S')
            vals['name'] = f'SES{timestamp}'
        
        # Set thời gian bắt đầu khi tạo record
        if not vals.get('start_time'):
            vals['start_time'] = fields.Datetime.now()
        
        session = super(CyberSession, self).create(vals)

        acc = session.account_id
        if acc.balance <= 0:
            raise UserError(_("Số dư không đủ để bắt đầu session."))

        return session

    def read(self, fields=None, load='_classic_read'):
        """Mỗi lần mở view, kiểm tra session hết giờ"""
        self._action_close_auto()
        return super().read(fields, load)

    def write(self, vals):
        """Mỗi lần ghi dữ liệu, kiểm tra session hết giờ"""
        res = super().write(vals)
        if not self.env.context.get('skip_auto_close'):
            self._action_close_auto()
        return res

    # ========================
    # CRON
    # ========================
    @api.model
    def cron_close_expired_sessions(self):
        """Cron mỗi phút để tự động đóng session hết hạn"""
        now = fields.Datetime.now()
        sessions = self.search([
            ('state', '=', 'running'),
            ('end_time_expected', '<=', now)
        ])
        if sessions.sudo():
            sessions._action_close_auto()