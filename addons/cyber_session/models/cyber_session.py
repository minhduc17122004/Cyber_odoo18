from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CyberSession(models.Model):
    _name = 'cyber.session'
    _description = 'Cyber Game Session'
    _inherit = ['mail.thread']

    name = fields.Char(string='Session Name', default=lambda self: _('New'))
    account_id = fields.Many2one('cyber.account', string='Account', required=True, ondelete='cascade')
    product_machine_id = fields.Many2one('product.product', string='Machine', domain=[('is_machine', '=', True)])
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now)
    end_time = fields.Datetime(string='End Time')
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True)
    price_per_hour = fields.Float(string='Price per Hour')
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('running', 'Running'),
        ('closed', 'Closed')
    ], string='State', default='running', tracking=True)

    order_ids = fields.One2many('cyber.sale_order_in_session', 'session_id', string='Orders in Session')

    # ==========================
    # COMPUTE METHODS
    # ==========================
    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = round(delta.total_seconds() / 3600, 2)
            else:
                rec.duration = 0.0

    @api.depends('order_ids.line_total', 'duration', 'price_per_hour', 'state')
    def _compute_total_cost(self):
        for rec in self:
            order_total = sum(rec.order_ids.mapped('line_total'))
            service_cost = rec.duration * rec.price_per_hour if rec.state == 'closed' else 0.0
            rec.total_cost = order_total + service_cost
            rec._auto_close_if_out_of_balance()  # ⬅ Gọi auto check tại đây

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

            # Kiểm tra nếu tổng chi phí = số dư hiện tại
            if round(rec.total_cost, 2) >= round(account.balance, 2) and account.balance > 0:
                rec._close_session_auto(reason="Balance reached 0")

    def _close_session_auto(self, reason=""):
        """Đóng phiên khi hết tiền hoặc theo trigger tự động"""
        for rec in self:
            rec.end_time = fields.Datetime.now()
            rec._compute_duration()
            rec.state = 'closed'
            rec._compute_total_cost()

            account = rec.account_id
            customer = account.customer_id

            # Ghi transaction spend
            self.env['cyber.transaction'].create({
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

            # Có thể ghi log nếu cần
            rec.message_post(body=f"Session closed automatically ({reason}).")

    # ==========================
    # MANUAL CLOSE BUTTON
    # ==========================
    def action_close(self):
        """Đóng phiên thủ công"""
        for rec in self:
            if rec.state == 'closed':
                continue
            rec._close_session_auto(reason="Manual close")