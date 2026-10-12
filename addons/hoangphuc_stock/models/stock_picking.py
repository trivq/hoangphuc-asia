from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_scale_picking = fields.Boolean(
        string='Phiếu Cân Trạm Cân',
        default=False,
        copy=False,
        help='Bật tính năng cân xe tự động cho phiếu nhập/xuất này.'
    )
    vehicle_plate = fields.Char(
        string='Biển Số Xe (BKS)',
        tracking=True,
        help='Biển kiểm soát xe vận chuyển (VD: 36C-123.45).'
    )
    driver_name = fields.Char(
        string='Họ Tên Lái Xe',
        tracking=True,
        help='Tên tài xế điều khiển phương tiện.'
    )
    tare_weight = fields.Float(
        string='Khối Lượng Bì (Kg)',
        digits=(12, 2),
        default=0.0,
        tracking=True,
        help='Khối lượng xe không tải.'
    )
    gross_weight = fields.Float(
        string='Khối Lượng Tổng (Kg)',
        digits=(12, 2),
        default=0.0,
        tracking=True,
        help='Khối lượng xe có tải.'
    )
    net_weight = fields.Float(
        string='Khối Lượng Tịnh (Kg)',
        digits=(12, 2),
        compute='_compute_scale_weights',
        store=True,
        tracking=True,
        help='Khối lượng hàng hóa thực tế = Tổng - Bì.'
    )
    density = fields.Float(
        string='Tỷ Trọng Đá (Tấn/m³)',
        digits=(12, 3),
        default=1.600,
        help='Tỷ trọng quy đổi khối lượng sang thể tích m3.'
    )
    volume_m3 = fields.Float(
        string='Thể Tích Quy Đổi (m³)',
        digits=(12, 2),
        compute='_compute_scale_weights',
        store=True,
        tracking=True,
        help='Thể tích quy đổi tương đương = (Khối lượng tịnh / 1000) / Tỷ trọng.'
    )
    weigh_scale_number = fields.Char(
        string='Trạm Cân Số',
        default='Trạm Cân Số 1',
        help='Tên hoặc số hiệu trạm cân thực hiện.'
    )
    weigh_time_first = fields.Datetime(
        string='Thời Gian Cân Lần 1',
        help='Thời điểm cân xe lần 1 (cân bì hoặc cân tổng).'
    )
    weigh_time_second = fields.Datetime(
        string='Thời Gian Cân Lần 2',
        help='Thời điểm cân xe lần 2.'
    )
    crushing_plant = fields.Selection([
        ('plant_1', 'Trạm Nghiền Sàng 1'),
        ('plant_2', 'Trạm Nghiền Sàng 2'),
        ('quarry_pit', 'Moong Khai Thác Mỏ')
    ], string='Trạm Nghiền / Vị Trí Cấp Liệu', tracking=True)

    # Trường dùng cho Xuất kho Vật tư phụ tùng (Sóng 1 & Sóng 2)
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Thiết Bị / Xe Cơ Giới Chịu Chi Phí',
        help='Đích danh máy xúc, xe ben hoặc trạm nghiền nhận phụ tùng (BR-10).'
    )

    # Trường dùng cho Xuất kho Vật liệu nổ (Sóng 1)
    blasting_passport_code = fields.Char(
        string='Mã Hộ Chiếu Nổ Mìn',
        help='Mã phương án / hộ chiếu khoan nổ mìn được phê duyệt.'
    )
    blasting_commander = fields.Char(
        string='Chỉ Huy Nổ Mìn',
        help='Người có chứng chỉ chỉ huy nổ mìn chịu trách nhiệm hiện trường.'
    )

    @api.depends('gross_weight', 'tare_weight', 'density')
    def _compute_scale_weights(self):
        for picking in self:
            net = 0.0
            if picking.gross_weight > picking.tare_weight:
                net = picking.gross_weight - picking.tare_weight
            picking.net_weight = net

            d = picking.density or 1.600
            if d > 0 and net > 0:
                # net is in kg, net / 1000 is in tons, (tons / density) = m3
                picking.volume_m3 = round((net / 1000.0) / d, 2)
            else:
                picking.volume_m3 = 0.0

    @api.onchange('move_ids')
    def _onchange_moves_density(self):
        """Tự động cập nhật tỷ trọng mặc định từ sản phẩm đầu tiên."""
        for picking in self:
            if picking.move_ids:
                first_product = picking.move_ids[0].product_id
                if first_product and first_product.density > 0:
                    picking.density = first_product.density

    def action_apply_scale_to_moves(self):
        """Tự động áp số lượng từ trạm cân vào các dòng move."""
        self.ensure_one()
        if self.net_weight <= 0:
            raise UserError(_('Khối lượng tịnh phải lớn hơn 0 trước khi cập nhật!'))

        for move in self.move_ids:
            # Tương thích đa phiên bản Odoo (Odoo 20: uom_id, Odoo 19/18: product_uom, fallback: product_id.uom_id)
            uom = (
                move.uom_id if 'uom_id' in move._fields
                else move.product_uom if 'product_uom' in move._fields
                else (move.product_id.uom_id if move.product_id else False)
            )
            uom_name = (uom.name or '').lower() if uom else ''
            qty = 0.0
            if 'm3' in uom_name or 'm³' in uom_name or 'khối' in uom_name:
                qty = self.volume_m3
            elif 'tấn' in uom_name or 'tan' in uom_name:
                qty = round(self.net_weight / 1000.0, 3)
            elif 'kg' in uom_name:
                qty = self.net_weight
            else:
                # Default to tons if stone
                qty = round(self.net_weight / 1000.0, 3)

            move.quantity = qty
            if 'product_uom_qty' in move._fields and not move.product_uom_qty:
                move.product_uom_qty = qty
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành Công'),
                'message': _('Đã cập nhật khối lượng tịnh (%s Kg / %s m³) vào phiếu kho!') % (self.net_weight, self.volume_m3),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_print_scale_ticket(self):
        """In phiếu cân điện tử chuẩn mỏ đá."""
        self.ensure_one()
        return self.env.ref('hoangphuc_stock.action_report_scale_ticket').report_action(self)
