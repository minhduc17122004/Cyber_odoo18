from odoo import models, fields

class CyberExpenseType(models.Model):
    _name = 'cyber.expense.type'
    _description = 'Expense Type'

    name = fields.Char("Loại chi phí", required=True)
    amount_default = fields.Float("Số tiền mặc định", required=True)
    is_fixed = fields.Boolean("Chi phí cố định", default=False)
    description = fields.Text("Mô tả")
