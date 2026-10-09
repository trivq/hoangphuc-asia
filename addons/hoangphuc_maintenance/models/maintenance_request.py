from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    request_category = fields.Selection([
        ('preventive', 'Bảo Dưỡng Định Kỳ (Theo Giờ/Km)'),
        ('corrective', 'Sửa Chữa Đột Xuất (Sự Cố/Hỏng Hóc)')
    ], string='Phân Loại Bảo Trì (BR-10)', default='corrective', required=True, tracking=True)

    downtime_minutes = fields.Integer(
        string='Thời Gian Dừng Máy (Phút)',
        default=0,
        tracking=True,
        help='Tổng thời gian máy móc phải ngừng hoạt động để sửa chữa (BR-04).'
    )
    downtime_cause = fields.Selection([
        ('electrical', 'Sự Cố Điện / Hệ Thống Điều Khiển'),
        ('hydraulic', 'Hỏng Hệ Thống Thủy Lực / Ty Bơm'),
        ('engine', 'Sự Cố Động Cơ / Kim Phun / Quá Nhiệt'),
        ('tyre_track', 'Hỏng Lốp / Rách Xích Cơ Giới'),
        ('jaw_crusher', 'Kẹt / Mòn Má Nghiền / Rách Lưới Sàng'),
        ('operator', 'Lỗi Thao Tác Của Lái Máy'),
        ('other', 'Nguyên Nhân Khác')
    ], string='Nguyên Nhân Dừng Máy (BR-04)', tracking=True)

    downtime_explanation = fields.Text(
        string='Giải Trình Kỹ Thuật (Dừng Máy >= 10 Phút)',
        tracking=True,
        help='Bắt buộc ghi rõ lý do sự cố nếu thời gian dừng máy từ 10 phút trở lên (BR-04).'
    )

    # Biên bản nghiệm thu 3 bên (BR-07)
    driver_confirmed = fields.Boolean(
        string='1. Lái Xe Vận Hành Thử (OK)',
        default=False,
        tracking=True,
        help='Lái máy/lái xe xác nhận máy móc đã chạy bình thường sau khi sửa.'
    )
    driver_notes = fields.Char(string='Ghi Chú Của Lái Xe')

    mechanic_confirmed = fields.Boolean(
        string='2. Thợ Sửa Chữa Hoàn Thành (OK)',
        default=False,
        tracking=True,
        help='Thợ cơ khí/điện xác nhận đã thay thế phụ tùng và xử lý xong sự cố.'
    )

    manager_confirmed = fields.Boolean(
        string='3. Quản Đốc Mỏ Phê Duyệt Mở Máy (OK)',
        default=False,
        tracking=True,
        help='Quản đốc ký duyệt bàn giao máy đưa trở lại sản xuất mỏ.'
    )

    is_three_party_approved = fields.Boolean(
        string='Đã Nghiệm Thu Đủ 3 Bên (BR-07)',
        compute='_compute_three_party_approved',
        store=True,
        help='Bắt buộc phải có đủ 3 bên xác nhận mới được phép đóng phiếu bảo trì.'
    )

    @api.depends('driver_confirmed', 'mechanic_confirmed', 'manager_confirmed')
    def _compute_three_party_approved(self):
        for req in self:
            req.is_three_party_approved = req.driver_confirmed and req.mechanic_confirmed and req.manager_confirmed

    def action_verify_three_party_signoff(self):
        """Kiểm tra điều kiện nghiệm thu trước khi mở khóa máy."""
        self.ensure_one()
        if self.downtime_minutes >= 10 and not (self.downtime_explanation or '').strip():
            raise UserError(_('Thời gian dừng máy %s phút (>= 10 phút). Bắt buộc phải có giải trình nguyên nhân kỹ thuật (BR-04)!') % self.downtime_minutes)
        if not self.is_three_party_approved:
            raise UserError(_('Chưa đủ biên bản nghiệm thu 3 bên (Lái xe, Thợ sửa chữa, Quản đốc mỏ)! Không được phép mở máy (BR-07).'))

        # Tự động mở khóa thiết bị nếu thiết bị đang bị khóa
        if self.equipment_id and self.equipment_id.pre_shift_safety_status == 'locked':
            self.equipment_id.action_unlock_equipment()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Nghiệm Thu Thành Công'),
                'message': _('Đã xác nhận nghiệm thu 3 bên (BR-07). Thiết bị %s đủ điều kiện vận hành an toàn!') % self.equipment_id.name,
                'type': 'success',
                'sticky': False,
            }
        }
