from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class CyberMaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    cyber_machine_id = fields.Many2one(
        'product.product',
        string='Máy',
        domain=[('is_machine', '=', True)],
        help='Máy/Thiết bị liên quan trong cyber cafe'
    )

    expense_ids = fields.One2many(
        'cyber.expense',
        'maintenance_id',
        string="Chi phí liên quan"
    )
    
    # Thêm field state nếu chưa có trong maintenance.request
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('unscheduled', 'Unscheduled'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # ========================
    # LIFECYCLE METHODS
    # ========================
    @api.model
    def create(self, vals):
        """Override create - khi tạo maintenance request mới, update product"""
        request = super(CyberMaintenanceRequest, self).create(vals)
        
        # Nếu có cyber_machine_id -> set thành maintenance
        if request.cyber_machine_id:
            request._update_product_maintenance_status()
        
        return request

    def write(self, vals):
        """Override write - khi cập nhật, nếu state thay đổi -> update product"""
        result = super(CyberMaintenanceRequest, self).write(vals)
        
        # Nếu có thay đổi state hoặc cyber_machine_id
        if 'state' in vals or 'cyber_machine_id' in vals or 'stage_id' in vals:
            for request in self:
                if request.cyber_machine_id:
                    request._update_product_maintenance_status()
        
        return result

    def unlink(self):
        """Override unlink - khi xóa maintenance request, reset product status"""
        for request in self:
            if request.cyber_machine_id:
                # Nếu xóa bản ghi bảo trì, reset product.machine_status = 'active'
                request.cyber_machine_id.product_tmpl_id.with_context(skip_readonly=True).write({
                    'machine_status': 'active'
                })
                request.message_post(body=_("✅ Máy được reset thành: <b>Hoạt động</b>"))
        
        return super(CyberMaintenanceRequest, self).unlink()

    # ========================
    # MAINTENANCE STATUS METHODS
    # ========================
    def _update_product_maintenance_status(self):
        """
        Cập nhật trạng thái máy dựa trên state của maintenance request
        - draft/sent/unscheduled/in_progress -> machine_status = 'maintenance'
        - done -> machine_status = 'active', update last_maintenance & next_maintenance
        """
        for request in self:
            if not request.cyber_machine_id:
                continue
            
            product = request.cyber_machine_id.product_tmpl_id
            
            # Lấy state hiện tại (có thể từ field state hoặc stage_id)
            current_state = request.state if hasattr(request, 'state') and request.state else None
            
            # Nếu không có state, check stage_id
            if not current_state and hasattr(request, 'stage_id') and request.stage_id:
                # Kiểm tra stage name để xác định trạng thái
                stage_name = request.stage_id.name.lower()
                if 'done' in stage_name or 'complete' in stage_name:
                    current_state = 'done'
                elif 'cancel' in stage_name:
                    current_state = 'cancel'
                else:
                    current_state = 'in_progress'
            
            # Trạng thái bảo trì đang thực hiện (chưa hoàn thành)
            if current_state in ['draft', 'sent', 'unscheduled', 'in_progress']:
                product.with_context(skip_readonly=True).write({
                    'machine_status': 'maintenance'
                })
                request.message_post(
                    body=_("🔧 Máy được đặt thành: <b>Bảo trì</b>")
                )
            
            # Trạng thái bảo trì hoàn thành
            elif current_state == 'done':
                today = fields.Date.today()
                next_maintenance = today + timedelta(days=30)  # Mặc định bảo trì sau 30 ngày
                
                product.with_context(skip_readonly=True).write({
                    'machine_status': 'active',
                    'last_maintenance': today,
                    'next_maintenance': next_maintenance,
                })
                
                request.message_post(
                    body=_("✅ <b>Bảo trì hoàn thành</b><br/>"
                           "Cập nhật máy:<br/>"
                           "- Trạng thái: <b>Hoạt động</b><br/>"
                           "- Ngày bảo trì gần nhất: <b>%s</b><br/>"
                           "- Ngày bảo trì tiếp theo: <b>%s</b>") % (today, next_maintenance)
                )
            
            # Trạng thái máy hỏng (nếu maintenance request ở trạng thái cancel)
            elif current_state == 'cancel':
                product.with_context(skip_readonly=True).write({
                    'machine_status': 'broken'
                })
                request.message_post(
                    body=_("⚠️ Máy được đặt thành: <b>Hỏng</b>")
                )

    # ========================
    # ACTION BUTTONS
    # ========================
    def action_confirm(self):
        """
        Khi confirm maintenance request -> update product thành maintenance
        """
        for request in self:
            if request.cyber_machine_id:
                request.state = 'in_progress'
                request._update_product_maintenance_status()
        return True

    def action_done(self):
        """
        Khi mark done -> update product thành active + ngày bảo trì
        """
        for request in self:
            request.state = 'done'
            if request.cyber_machine_id:
                request._update_product_maintenance_status()
        return True

    def action_cancel(self):
        """
        Khi cancel -> update product thành broken
        """
        for request in self:
            request.state = 'cancel'
            if request.cyber_machine_id:
                request._update_product_maintenance_status()
        return True

    # ========================
    # COMPUTE METHODS
    # ========================
    @api.onchange('cyber_machine_id')
    def _onchange_cyber_machine_id(self):
        """
        Khi chọn máy, tự động điền thông tin
        """
        if self.cyber_machine_id:
            self.name = f"Bảo trì {self.cyber_machine_id.name}"