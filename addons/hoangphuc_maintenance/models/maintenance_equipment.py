from odoo import models, fields, _
from odoo.exceptions import UserError

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    vehicle_plate = fields.Char(
        string='Biển Số / Số Hiệu Máy Mỏ',
        tracking=True,
        help='Biển số xe ben hoặc số hiệu máy xúc (VD: EX-01, 36C-999.88).'
    )
    equipment_quarry_type = fields.Selection([
        ('excavator', 'Máy Xúc Đào Thủy Lực'),
        ('truck', 'Xe Ben Vận Tải Mỏ'),
        ('crusher', 'Trạm Nghiền Sàng Đá'),
        ('drill', 'Máy Khoan Đá'),
        ('loader', 'Máy Xúc Lật'),
        ('other', 'Thiết Bị Khác')
    ], string='Phân Loại Cơ Giới Mỏ', default='excavator', tracking=True)

    standard_fuel_rate = fields.Float(
        string='Định Mức Nhiên Liệu Chuẩn (L/h)',
        digits=(10, 2),
        default=15.0,
        tracking=True,
        help='Định mức tiêu hao nhiên liệu chuẩn theo giờ máy làm việc.'
    )
    pre_shift_safety_status = fields.Selection([
        ('safe', 'An Toàn Vận Hành'),
        ('warning', 'Cảnh Báo Cần Lưu Ý'),
        ('locked', 'Khóa Thiết Bị (Không Đạt An Toàn - BR-02)')
    ], string='An Toàn Đầu Ca', default='safe', tracking=True)

    safety_lock_reason = fields.Char(
        string='Lý Do Khóa Thiết Bị',
        tracking=True,
        help='Mô tả lỗi nguy hiểm phát hiện đầu ca (chảy dầu phanh, mất áp thủy lực...).'
    )

    fuel_log_count = fields.Integer(
        string='Số Phiếu Cấp Dầu',
        compute='_compute_fuel_log_count'
    )

    def _compute_fuel_log_count(self):
        for eq in self:
            eq.fuel_log_count = self.env['hoangphuc.fuel.log'].search_count([('equipment_id', '=', eq.id)])

    def action_lock_equipment(self):
        """Khóa máy khẩn cấp nếu không an toàn."""
        self.ensure_one()
        self.pre_shift_safety_status = 'locked'
        self.message_post(body=_('Thiết bị đã bị KHÓA VẬN HÀNH do không đảm bảo an toàn đầu ca (BR-02). Lý do: %s') % (self.safety_lock_reason or 'Chưa rõ'))

    def action_unlock_equipment(self):
        """Mở khóa máy sau khi kiểm tra đạt."""
        self.ensure_one()
        self.pre_shift_safety_status = 'safe'
        self.safety_lock_reason = False
        self.message_post(body=_('Thiết bị đã được Quản đốc xác nhận AN TOÀN và mở khóa đưa vào vận hành.'))

    def action_view_fuel_logs(self):
        """Xem nhật ký cấp dầu của thiết bị này."""
        self.ensure_one()
        return {
            'name': _('Nhật Ký Cấp Dầu - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hoangphuc.fuel.log',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }
