from odoo import api, fields, models
from odoo.exceptions import ValidationError

class CyberProduct(models.Model):
    _inherit = 'product.template'

    is_machine = fields.Boolean(string="Máy tính")
    is_service = fields.Boolean(string="Dịch vụ")
    serial_number = fields.Char(string="IP định vị")
    status = fields.Selection([
        ('available', 'Có sẵn'),
        ('playing', 'Đang chơi'),
        ('error', 'Lỗi'),
        ('almost_gone', 'Gần hết'),
        ('sold_out', 'Hết')
    ], string="Status")
    last_maintenance = fields.Date(string="Ngày bảo trì cuối")
    
    categ_id = fields.Many2one('product.category', string="Loại", required=True)
    uom_id = fields.Many2one('uom.uom', string="Đơn vị tính", required=True)

    @api.constrains('is_machine', 'is_service')
    def _check_machine_service_flags(self):
        for rec in self:
            if not rec.is_machine and not rec.is_service:
                raise ValidationError("Một sản phẩm phải là Machine hoặc Service.")
            if rec.is_machine and rec.is_service:
                raise ValidationError("Một sản phẩm không thể vừa là Machine vừa là Service.")

    @api.constrains('is_service', 'serial_number')
    def _check_serial_number_for_service(self):
        for rec in self:
            if rec.is_service and rec.serial_number:
                raise ValidationError("Dịch vụ không được có Serial Number.")

    @api.onchange('is_machine', 'is_service')
    def _onchange_status(self):
        """Giới hạn giá trị status theo loại sản phẩm."""
        for rec in self:
            if rec.is_machine:
                rec.status = 'available' if rec.status not in ['available', 'playing', 'error'] else rec.status
            elif rec.is_service:
                rec.status = 'available' if rec.status not in ['available', 'almost_gone', 'sold_out'] else rec.status
            else:
                rec.status = False

    @api.onchange('is_service')
    def _onchange_disable_machine_field(self):
        """Vô hiệu hóa serial_number và last_maintenance nếu là service."""
        for rec in self:
            if rec.is_service:
                rec.serial_number = False
                rec.last_maintenance = False
