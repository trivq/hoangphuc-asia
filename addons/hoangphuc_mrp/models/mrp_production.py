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

    downtime_ids = fields.One2many(
        'mrp.production.downtime',
        'production_id',
        string='Nhật Ký Dừng Máy'
    )

    downtime_minutes = fields.Integer(
        string='Tổng Thời Gian Dừng Máy (Phút)',
        compute='_compute_downtime_minutes',
        store=True,
        tracking=True,
        help='Tổng thời gian dừng máy phát sinh trong ca từ các lượt dừng máy.'
    )

    @api.depends('downtime_ids.duration_minutes')
    def _compute_downtime_minutes(self):
        for mo in self:
            mo.downtime_minutes = sum(mo.downtime_ids.mapped('duration_minutes'))

    quarry_stock_yard = fields.Char(
        string='Vị Trí Bãi Tập Kết Thành Phẩm',
        default='Bãi Thành Phẩm Đá 1x2 - Cạnh Trạm Cân Số 1',
        help='Bãi tập kết thành phẩm đá sau khi qua hệ thống băng tải sàng phân loại (Luồng 4.5).'
    )

    @api.depends('state', 'move_finished_ids.picking_id')
    def _compute_picking_ids(self):
        super()._compute_picking_ids()
        for order in self:
            extra_pickings = self.env['stock.picking'].search([
                '|',
                ('origin', '=', order.name),
                ('id', 'in', (order.move_finished_ids.picking_id | order.move_raw_ids.picking_id).ids),
            ])
            all_pickings = (order.picking_ids or self.env['stock.picking']) | extra_pickings
            order.picking_ids = all_pickings
            order.delivery_count = len(all_pickings)

    def _create_or_update_finished_picking(self):
        """Tự động tạo hoặc liên kết Phiếu Nhập Kho Bãi Thành Phẩm (Receipt) cho MO."""
        Picking = self.env['stock.picking']
        for mo in self:
            if not mo.move_finished_ids:
                continue
            # Tìm phiếu kho thành phẩm đã liên kết
            picking = mo.picking_ids.filtered(
                lambda p: p.location_dest_id == mo.location_dest_id or p.picking_type_id.code in ('incoming', 'internal')
            )
            qty_val = mo.qty_producing or mo.product_qty or 0.0
            net_kg = qty_val * 1000.0
            density_val = mo.product_id.density if hasattr(mo.product_id, 'density') and mo.product_id.density else 1.6
            vol = round((net_kg / 1000.0) / density_val, 2) if density_val > 0 else 0.0

            if not picking:
                warehouse = mo.picking_type_id.warehouse_id or self.env['stock.warehouse'].search([('company_id', '=', mo.company_id.id)], limit=1)
                picking_type = warehouse.in_type_id or mo.picking_type_id
                vals = {
                    'picking_type_id': picking_type.id,
                    'origin': mo.name,
                    'location_id': mo.production_location_id.id,
                    'location_dest_id': mo.location_dest_id.id,
                    'company_id': mo.company_id.id,
                    'crushing_plant': mo.crushing_plant,
                    'driver_name': mo.operator_name,
                    'is_scale_picking': True,
                    'net_weight': net_kg,
                    'density': density_val,
                    'volume_m3': vol,
                }
                picking = Picking.create(vals)
            else:
                picking.write({
                    'net_weight': net_kg,
                    'volume_m3': vol,
                })

            # Gắn các moves finished và move_lines vào picking
            moves_to_link = mo.move_finished_ids.filtered(lambda m: not m.picking_id)
            if moves_to_link:
                moves_to_link.write({'picking_id': picking.id})
                if moves_to_link.move_line_ids:
                    moves_to_link.move_line_ids.filtered(lambda ml: not ml.picking_id).write({'picking_id': picking.id})

    def action_view_mo_delivery(self):
        """Mở danh sách phiếu nhập kho của MO, tự động khởi tạo nếu chưa có."""
        self.ensure_one()
        if not self.picking_ids and self.move_finished_ids:
            self._create_or_update_finished_picking()
        return super().action_view_mo_delivery()

    def action_confirm(self):
        """Kiểm tra quy tắc an toàn BR-02 trước khi xác nhận phát lệnh sản xuất."""
        for mo in self:
            if not mo.safety_checked:
                raise UserError(_('CẢNH BÁO BR-02: Điều kiện an toàn đầu ca chưa được xác nhận! Nghiêm cấm phát lệnh vận hành trạm nghiền.'))
        res = super().action_confirm()
        for mo in self:
            mo._create_or_update_finished_picking()
        return res

    def button_mark_done(self):
        """Kiểm tra giải trình dừng máy BR-04 trước khi hoàn tất lệnh sản xuất."""
        for mo in self:
            missing_explanation = mo.downtime_ids.filtered(
                lambda d: d.duration_minutes >= 10 and not (d.explanation or '').strip()
            )
            if missing_explanation:
                raise UserError(_(
                    'CẢNH BÁO BR-04: Có %s lượt dừng máy từ 10 phút trở lên chưa có giải trình kỹ thuật! '
                    'Bắt buộc nhập đầy đủ giải trình sự cố dừng máy trước khi chốt sản xuất!'
                ) % len(missing_explanation))
            if mo.downtime_minutes >= 10 and not (mo.downtime_explanation or '').strip():
                raise UserError(_('CẢNH BÁO BR-04: Thời gian dừng máy >= 10 phút (%s phút). Bắt buộc nhập Giải trình sự cố dừng máy trước khi chốt sản xuất!') % mo.downtime_minutes)
        for mo in self:
            mo._create_or_update_finished_picking()
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
