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
    start_time = fields.Datetime(string='Start Time', default=lambda self: fields.Datetime.now())
    end_time = fields.Datetime(string='End Time')
    end_time_expected = fields.Datetime(string='Expected End Time', compute='_compute_end_time_expected', store=True)
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True, digits=(12, 6))
    price_per_hour = fields.Float(string='Price per Hour (VND)', required=True, digits=(16, 2))
    total_cost = fields.Float(string='Total Cost (VND)', compute='_compute_total_cost', store=True, digits=(16, 2))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='Status', default='running', tracking=True)

    order_ids = fields.One2many('cyber.sale_order_in_session', 'session_id', string='Orders in Session')
    transaction_id = fields.Many2one(
    'cyber.transaction',
    string='Giao dịch liên quan',
    ondelete='set null'
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

            order_total = sum(rec.order_ids.mapped('line_total'))
            service_cost = rec.duration * rec.price_per_hour if rec.state == 'closed' else 0.0
            rec.total_cost = order_total + service_cost
            rec._auto_close_if_out_of_balance()  # ⬅ Auto-check balance

    # ==========================
    # AUTO CLOSE WHEN OUT OF BALANCE
    # ==========================
    def _auto_close_if_out_of_balance(self):
        """Đóng phiên tự động khi chi phí đạt đến số dư tài khoản."""
        for rec in self:
            if rec.state != 'running':
                continue
            account = rec.account_id
            if not account:
                continue

            if round(rec.total_cost, 2) >= round(account.balance, 2) and account.balance > 0:
                rec._close_session_auto(reason="Balance reached 0")

    # ==========================
    # CLOSE SESSION + AUTO INVOICE
    # ==========================
    def _close_session_auto(self, reason=""):
        """Đóng phiên và tự tạo hóa đơn"""

            session_cost = rec.duration * rec.price_per_hour
            orders_cost = sum(rec.order_ids.mapped('line_total'))
            rec.total_cost = round(session_cost + orders_cost)

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

            # Tính lại thời lượng & chi phí cho đúng
            rec._compute_duration()
            rec._compute_total_cost()

            # ❌ Không trừ tiền nữa (đã trừ khi tạo)
            acc.play_time_total += rec.duration
            acc.last_session_end = rec.end_time


            # Ghi transaction spend
            transaction = self.env['cyber.transaction'].create({
                'account_id': account.id,
                'type': 'spend',
                'amount': rec.total_cost,
                'payment_method': 'cash',
            })

            # Cập nhật account
            account.total_spent += rec.total_cost
            account.play_time_total += rec.duration
            account.last_session_end = rec.end_time
            account._compute_balance()

            # Cập nhật customer
            if customer:
                customer._calculate_totals()
                if hasattr(customer, '_compute_segment'):
                    customer._compute_segment()

            # ✅ TỰ ĐỘNG TẠO HÓA ĐƠN
            invoice_vals = {
                'customer_id': customer.id if customer else False,
                'session_id': rec.id,
                'transaction_id': transaction.id,
                'total_cost': rec.total_cost,
                'invoice_date': fields.Datetime.now(),
                'start_time': rec.start_time,
                'end_time': rec.end_time,
            }
            self.env['cyber.invoice'].create(invoice_vals)

            rec.message_post(body=f"Session closed automatically ({reason}). Invoice created.")

    # ==========================
    # MANUAL CLOSE BUTTON
    # ==========================
    def action_close(self):
        """Đóng phiên thủ công"""
        for rec in self:
            if rec.state == 'closed':
                continue
            rec._close_session_auto(reason="Manual close")

            acc.sudo().write({
                'play_time_total': acc.play_time_total,
                'last_session_end': acc.last_session_end,
            })

            # Cập nhật customer tổng hợp
            if acc.customer_id:
                acc.customer_id._calculate_totals()

            # ✅ Chuyển trạng thái và log
            rec.state = 'closed'
            rec.message_post(body=_("Session closed automatically at %s.") % rec.end_time)

        return True

    def _close_if_expired(self):
        """Tự động đóng khi hết giờ"""
        now = fields.Datetime.now()
        for rec in self:
            if rec.state == 'running' and rec.end_time_expected and now >= rec.end_time_expected:
                rec.with_context(skip_check=True).sudo().write({
                    'end_time': rec.end_time_expected or now,
                    'state': 'closed'
                })
                rec._finalize_close()

    def _auto_close_if_out_of_balance(self):
        """Tự đóng nếu hết tiền"""
        for rec in self:
            if rec.state == 'running' and rec.account_id and rec.account_id.balance <= 0:
                rec.end_time = fields.Datetime.now()
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
    @api.model
    def create(self, vals):
        """Tạo session và trừ tiền ngay"""
        if vals.get('name', 'New') == 'New':
            timestamp = fields.Datetime.now().strftime('%Y%m%d%H%M%S')
            vals['name'] = f'SES{timestamp}'

        session = super(CyberSession, self).create(vals)
        acc = session.account_id

        # ✅ Khi tạo session, trừ tiền ngay 1 giờ (hoặc thời lượng dự kiến)
        if acc and session.price_per_hour > 0:
            cost = session.price_per_hour  # tạm tính 1h; có thể sửa thành duration cố định nếu cần
            if acc.balance < cost:
                raise UserError(_("Số dư không đủ để bắt đầu session."))

            # Cập nhật account
            acc.sudo().write({
                'balance': acc.balance - cost,
                'total_spent': acc.total_spent + cost,
            })

            # Tạo transaction spend (1 lần duy nhất)
            self.env['cyber.transaction'].with_context(from_session=True).create({
                'account_id': acc.id,
                'session_id': session.id,
                'amount': cost,
                'type': 'spend',
                'payment_method': 'cash',
            })

            # Cập nhật play_time_remaining (vì đã trừ tiền)
            acc._compute_play_time_remaining()

        return session

    def read(self, fields=None, load='_classic_read'):
        """Mỗi lần mở view, kiểm tra và đóng nếu quá hạn"""
        self._close_if_expired()
        return super().read(fields, load)

    def write(self, vals):
        """Mỗi lần ghi dữ liệu, kiểm tra lại"""
        res = super().write(vals)
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

