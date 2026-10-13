from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    crushing_plant = fields.Selection([
        ('plant_1', 'Trạm Nghiền Sàng 1 (Công suất 250 Tấn/h)'),
        ('plant_2', 'Trạm Nghiền Sàng 2 (Công suất 150 Tấn/h)'),
    ], string='Trạm Nghiền Sàng', default='plant_1', tracking=True)

    production_shift = fields.Selection([
        ('shift_1', 'Ca 1 (06:00 - 14:00)'),
        ('shift_2', 'Ca 2 (14:00 - 22:00)'),
        ('shift_3', 'Ca 3 (22:00 - 06:00)'),
    ], string='Ca Sản Xuất', default='shift_1', tracking=True)

    operator_name = fields.Char(
        string='Trưởng Ca / Người Vận Hành',
        default='Lê Hoàng Long',
        tracking=True
    )

    safety_checked = fields.Boolean(
        string='Đã Kiểm Tra An Toàn Đầu Ca (BR-02)',
        default=True,
        tracking=True,
        help='Bắt buộc kiểm tra điều kiện an toàn mỏ, che chắn và phễu trạm nghiền trước khi chạy máy.'
    )

    safety_inspector = fields.Char(
        string='Cán Bộ An Toàn Hiện Trường',
        default='Cán bộ An toàn Mỏ Núi Dài'
    )

    raw_stone_input_qty = fields.Float(
        string='Đá Thô Cấp Liệu Thực Tế (Tấn)',
        digits=(12, 2),
        default=0.0,
        tracking=True,
        help='Khối lượng đá nguyên khai moong mỏ xúc cấp vào phễu nghiền (Luồng 4B).'
    )

    vehicle_trips_count = fields.Integer(
        string='Số Chuyến Xe Cấp Liệu',
        default=0,
        help='Số lượt chuyến xe ben Howo chở đá từ moong mỏ lên phễu cấp liệu trạm.'
    )

    quarry_pit_location = fields.Char(
        string='Vị Trí Khai Trường / Moong Cấp Liệu',
        default='Moong Khai Thác Mỏ Núi Dài - Tầng Mức +45m'
    )

    operating_hours = fields.Float(
        string='Thời Gian Chạy Máy Thực Tế (Giờ)',
        digits=(12, 1),
        default=8.0,
        help='Tổng số giờ chạy máy có tải trong ca.'
    )

    downtime_minutes = fields.Integer(
        string='Thời Gian Dừng Máy (Phút)',
        default=0,
        tracking=True,
        help='Tổng thời gian dừng máy phát sinh trong ca.'
    )

    downtime_cause = fields.Selection([
        ('none', 'Không Dừng Máy (Bình Thường)'),
        ('jam', 'Tắc Phễu / Kẹt Đá Quá Cỡ'),
        ('electrical', 'Sự Cố Điện / Mất Điện Lưới'),
        ('mechanical', 'Sự Cố Cơ Khí / Rách Băng Tải / Kẹt Sàng'),
        ('weather', 'Mưa Lớn / Thời Tiết Mất An Toàn'),
        ('maintenance', 'Bảo Dưỡng Định Kỳ Đầu Ca'),
    ], string='Nguyên Nhân Dừng Máy (BR-04)', default='none', tracking=True)

    downtime_explanation = fields.Text(
        string='Giải Trình Sự Cố Dừng Máy',
        help='Bắt buộc nhập giải trình kỹ thuật nếu thời gian dừng máy >= 10 phút (BR-04).'
    )

    quarry_stock_yard = fields.Char(
        string='Vị Trí Bãi Tập Kết Thành Phẩm',
        default='Bãi Thành Phẩm Đá 1x2 - Cạnh Trạm Cân Số 1',
        help='Bãi tập kết thành phẩm đá sau khi qua hệ thống băng tải sàng phân loại (Luồng 4.5).'
    )

    def action_confirm(self):
        """Kiểm tra quy tắc an toàn BR-02 trước khi xác nhận phát lệnh sản xuất."""
        for mo in self:
            if not mo.safety_checked:
                raise UserError(_('CẢNH BÁO BR-02: Điều kiện an toàn đầu ca chưa được xác nhận! Nghiêm cấm phát lệnh vận hành trạm nghiền.'))
        return super().action_confirm()

    def button_mark_done(self):
        """Kiểm tra giải trình dừng máy BR-04 trước khi hoàn tất lệnh sản xuất."""
        for mo in self:
            if mo.downtime_minutes >= 10 and not (mo.downtime_explanation or '').strip():
                raise UserError(_('CẢNH BÁO BR-04: Thời gian dừng máy >= 10 phút (%s phút). Bắt buộc nhập Giải trình sự cố dừng máy trước khi chốt sản xuất!') % mo.downtime_minutes)
        return super().button_mark_done()

    def action_quick_fill_scale_input(self):
        """Tự động cập nhật khối lượng đá thô cấp liệu vào dòng nguyên liệu tiêu hao."""
        self.ensure_one()
        if self.raw_stone_input_qty <= 0:
            raise UserError(_('Vui lòng nhập Khối lượng đá thô cấp liệu lớn hơn 0!'))
        for move in self.move_raw_ids:
            move.quantity = self.raw_stone_input_qty
            if 'product_uom_qty' in move._fields and not move.product_uom_qty:
                move.product_uom_qty = self.raw_stone_input_qty
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành Công'),
                'message': _('Đã cập nhật khối lượng đá thô cấp liệu (%s Tấn) vào nguyên liệu tiêu hao!') % self.raw_stone_input_qty,
                'type': 'success',
                'sticky': False,
            }
        }
