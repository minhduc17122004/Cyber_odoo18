from odoo import models, fields, api

class CyberExpense(models.Model):
    _name = 'cyber.expense'
    _description = 'Cyber Expense'

    name = fields.Char("Tên chi phí", required=True)
    amount = fields.Float("Số tiền", required=True)
    date = fields.Date("Ngày tạo", default=fields.Date.today)
    description = fields.Text("Mô tả")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancelled', 'Cancelled'),
        ('paid', 'Paid')], 
        string="Trạng thái", default='draft')
    
    expense_type_id = fields.Many2one(
        'cyber.expense.type', 
        string="Loại chi phí",
        )

    maintenance_id = fields.Many2one(
        'maintenance.request',
        string="Yêu cầu bảo trì",
        ondelete="set null"
    )

    @api.onchange('expense_type_id')
    def _onchange_expense_type(self):
        if self.expense_type_id and self.expense_type_id.is_fixed:
            self.amount = self.expense_type_id.amount_default
        else:
            self.amount = 0.0 

    