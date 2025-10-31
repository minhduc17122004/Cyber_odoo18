from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CyberSession(models.Model):
    _name = 'cyber.session'
    _description = 'Cyber Game Session'
    _inherit = ['mail.thread']

    # ========================
    # FIELDS
    # ========================
    name = fields.Char(string='Session Name', required=True, default=lambda self: _('New'))
    account_id = fields.Many2one('cyber.account', string='Account', required=True, ondelete='cascade')
    product_machine_id = fields.Many2one('product.product', string='Machine', domain=[('is_machine', '=', True)])
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now)
    end_time = fields.Datetime(string='End Time')
    end_time_expected = fields.Datetime(string='Expected End Time', compute='_compute_end_time_expected', store=True)
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True)
    price_per_hour = fields.Float(string='Price per Hour', required=True)
    total_cost = fields.Monetary(string='Total Cost', currency_field='currency_id', compute='_compute_total_cost', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='Status', default='running', tracking=True)

    order_ids = fields.One2many('cyber.sale_order_in_session', 'session_id', string='Orders in Session')

    # ========================
    # COMPUTE METHODS
    # ========================
    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Tính thời lượng phiên chơi"""
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = round(delta.total_seconds() / 3600, 2)
            else:
                rec.duration = 0.0

    @api.depends('duration', 'price_per_hour')
    def _compute_total_cost(self):
        """Tính tổng chi phí"""
        for rec in self:
            rec.total_cost = round(rec.duration * rec.price_per_hour, 2)

    @api.depends('account_id.play_time_remaining_seconds', 'start_time')
    def _compute_end_time_expected(self):
        """Tính thời gian kết thúc dự kiến dựa trên play_time_remaining_seconds"""
        for rec in self:
            acc = rec.account_id
            if acc and rec.start_time and acc.play_time_remaining_seconds > 0:
                rec.end_time_expected = rec.start_time + timedelta(seconds=acc.play_time_remaining_seconds)
            else:
                rec.end_time_expected = False

    # ========================
    # MAIN LOGIC
    # ========================
    def _finalize_close(self):
        """Xử lý khi session kết thúc"""
        for rec in self:
            acc = rec.account_id
            if not acc:
                continue

            # Cập nhật thời lượng & chi phí
            rec._compute_duration()
            rec._compute_total_cost()

            # Cập nhật account
            acc.total_spent += rec.total_cost
            acc.play_time_total += rec.duration
            acc.last_session_end = rec.end_time
            acc._compute_balance()

            # Cập nhật customer
            if acc.customer_id:
                acc.customer_id._calculate_totals()

            rec.state = 'closed'
            rec.message_post(body=_("Session closed automatically at %s.") % rec.end_time)
        return True

    def _close_if_expired(self):
        """Kiểm tra nếu hết giờ thì đóng ngay"""
        now = fields.Datetime.now()
        for rec in self:
            if rec.state == 'running' and rec.end_time_expected and now >= rec.end_time_expected:
                # Ghi trực tiếp vào DB mà không tái gọi _close_if_expired
                rec.with_context(skip_check=True).sudo().write({
                    'end_time': rec.end_time_expected,
                    'state': 'closed'
                })
                rec._finalize_close()

    def action_close_manual(self):
        """Đóng thủ công"""
        for rec in self:
            if rec.state == 'closed':
                continue
            rec.end_time = fields.Datetime.now()
            rec._finalize_close()
        return True

    # ========================
    # OVERRIDE METHODS
    # ========================
    def read(self, fields=None, load='_classic_read'):
        """Mỗi lần mở view, kiểm tra và đóng nếu quá hạn"""
        self._close_if_expired()
        return super().read(fields, load)

    def write(self, vals):
        """Mỗi lần ghi dữ liệu, kiểm tra lại"""
        res = super().write(vals)
        # Nếu context có flag thì bỏ qua kiểm tra
        if not self.env.context.get('skip_check'):
            self._close_if_expired()
        return res

    # ========================
    # CRON DỰ PHÒNG
    # ========================
    @api.model
    def cron_close_expired_sessions(self):
        """Cron mỗi phút để đóng các phiên quá hạn"""
        now = fields.Datetime.now()
        sessions = self.search([
            ('state', '=', 'running'),
            ('end_time_expected', '<=', now)
        ])
        if sessions:
            sessions._close_if_expired()
            _logger = self.env['ir.logging']
            _logger.create({
                'name': 'Cyber Session Auto-Close',
                'type': 'server',
                'dbname': self.env.cr.dbname,
                'level': 'INFO',
                'message': f"Closed {len(sessions)} expired sessions at {now}",
                'path': 'cyber.session',
                'line': '0',
                'func': 'cron_close_expired_sessions',
            })
        return True