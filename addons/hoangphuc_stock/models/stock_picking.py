from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    scale_equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Xe Cơ Giới Mỏ (BKS)',
        tracking=True,
        help='Chọn xe ben / thiết bị mỏ nếu là phương tiện nội bộ để tự động điền biển số, tài xế và khối lượng bì.'
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
    weigh_time = fields.Datetime(
        string='Thời Gian Cân Xe',
        default=fields.Datetime.now,
        tracking=True,
        help='Thời điểm phương tiện thực hiện cân tại trạm cân mỏ đá.'
    )
    crushing_plant = fields.Selection([
        ('plant_1', 'Trạm Nghiền Sàng 1'),
        ('plant_2', 'Trạm Nghiền Sàng 2'),
        ('quarry_pit', 'Moong Khai Thác Mỏ')
    ], string='Trạm Nghiền / Vị Trí Cấp Liệu', tracking=True)

    # Trường dùng cho Xuất kho Vật tư phụ tùng
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Thiết Bị / Xe Cơ Giới Chịu Chi Phí',
        help='Đích danh máy xúc, xe ben hoặc trạm nghiền nhận phụ tùng (BR-10).'
    )

    # Trường dùng cho Xuất kho Vật liệu nổ
    blasting_passport_code = fields.Char(
        string='Mã Hộ Chiếu Nổ Mìn',
        help='Mã phương án / hộ chiếu khoan nổ mìn được phê duyệt.'
    )
    blasting_commander = fields.Char(
        string='Chỉ Huy Nổ Mìn',
        help='Người có chứng chỉ chỉ huy nổ mìn chịu trách nhiệm hiện trường.'
    )

    # Phân loại nghiệp vụ và kiểm soát hiển thị các tab tương ứng với loại hoạt động
    picking_category = fields.Selection(
        related='picking_type_id.picking_category',
        string='Phân Loại Nghiệp Vụ Kho',
        readonly=True,
        store=True,
    )
    show_scale_tab = fields.Boolean(
        string='Hiển Thị Tab Trạm Cân',
        compute='_compute_tab_visibility',
        store=True,
        readonly=False,
        help='Cho phép hiển thị thông tin trạm cân mỏ đá.'
    )
    show_spare_parts_tab = fields.Boolean(
        string='Hiển Thị Tab Phụ Tùng',
        compute='_compute_tab_visibility',
        store=True,
        readonly=False,
        help='Cho phép hiển thị thông tin cấp phát phụ tùng thiết bị cơ giới mỏ.'
    )
    show_explosive_tab = fields.Boolean(
        string='Hiển Thị Tab Vật Liệu Nổ',
        compute='_compute_tab_visibility',
        store=True,
        readonly=False,
        help='Cho phép hiển thị thông tin hộ chiếu nổ mìn VLNCN.'
    )

    @api.depends('picking_type_id', 'picking_type_id.picking_category', 'scale_equipment_id', 'vehicle_plate', 'equipment_id', 'blasting_passport_code')
    def _compute_tab_visibility(self):
        for picking in self:
            category = picking.picking_type_id.picking_category or 'stone'
            # Tab Trạm Cân: Hiển thị nếu là kho đá/thành phẩm HOẶC phiếu có chọn xe mỏ / có biển số xe
            picking.show_scale_tab = (category == 'stone') or bool(picking.scale_equipment_id) or bool(picking.vehicle_plate)
            # Tab Phụ Tùng: Hiển thị nếu loại hoạt động là phụ tùng/vật tư HOẶC phiếu đã chọn thiết bị nhận
            picking.show_spare_parts_tab = (category == 'spare_parts') or bool(picking.equipment_id)
            # Tab Vật Liệu Nổ: Hiển thị nếu loại hoạt động là VLNCN HOẶC phiếu đã có mã hộ chiếu nổ mìn
            picking.show_explosive_tab = (category == 'explosives') or bool(picking.blasting_passport_code)

    @api.onchange('scale_equipment_id')
    def _onchange_scale_equipment_id(self):
        """Khi chọn xe cơ giới mỏ, tự động điền biển số, khối lượng bì chuẩn và tài xế phụ trách."""
        if self.scale_equipment_id:
            eq = self.scale_equipment_id
            if eq.vehicle_plate:
                self.vehicle_plate = eq.vehicle_plate
            elif not self.vehicle_plate:
                self.vehicle_plate = eq.name
            if eq.tare_weight > 0:
                self.tare_weight = eq.tare_weight
            if eq.driver_name:
                self.driver_name = eq.driver_name

    @api.onchange('vehicle_plate')
    def _onchange_vehicle_plate(self):
        """Khi nhập hoặc quét biển số xe, tự động tìm kiếm hồ sơ thiết bị cơ giới mỏ tương ứng."""
        if not self.vehicle_plate:
            return
        plate = self.vehicle_plate.strip()
        equipment = self.env['maintenance.equipment'].search([
            '|',
            ('vehicle_plate', '=ilike', plate),
            ('name', '=ilike', plate)
        ], limit=1)
        if not equipment and any(c in plate for c in ['-', '.', ' ']):
            clean_plate = plate.replace('-', '').replace('.', '').replace(' ', '').lower()
            all_eqs = self.env['maintenance.equipment'].search([('vehicle_plate', '!=', False)])
            for eq in all_eqs:
                eq_clean = eq.vehicle_plate.replace('-', '').replace('.', '').replace(' ', '').lower()
                if eq_clean == clean_plate:
                    equipment = eq
                    break
        if equipment:
            self.scale_equipment_id = equipment
            if equipment.vehicle_plate and self.vehicle_plate != equipment.vehicle_plate:
                self.vehicle_plate = equipment.vehicle_plate
            if equipment.tare_weight > 0:
                self.tare_weight = equipment.tare_weight
            if equipment.driver_name and not self.driver_name:
                self.driver_name = equipment.driver_name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sync_scale_equipment_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._sync_scale_equipment_vals(vals)
        return super().write(vals)

    def _sync_scale_equipment_vals(self, vals):
        """Hỗ trợ tự động điền bì và tài xế khi tạo/sửa phiếu kho qua API/trạm cân tự động."""
        eq = False
        if vals.get('scale_equipment_id'):
            eq = self.env['maintenance.equipment'].browse(vals['scale_equipment_id'])
        elif vals.get('vehicle_plate') and not vals.get('scale_equipment_id'):
            plate = str(vals['vehicle_plate']).strip()
            eq = self.env['maintenance.equipment'].search([
                '|',
                ('vehicle_plate', '=ilike', plate),
                ('name', '=ilike', plate)
            ], limit=1)
            if not eq and any(c in plate for c in ['-', '.', ' ']):
                clean_plate = plate.replace('-', '').replace('.', '').replace(' ', '').lower()
                all_eqs = self.env['maintenance.equipment'].search([('vehicle_plate', '!=', False)])
                for item in all_eqs:
                    eq_clean = item.vehicle_plate.replace('-', '').replace('.', '').replace(' ', '').lower()
                    if eq_clean == clean_plate:
                        eq = item
                        break
            if eq:
                vals['scale_equipment_id'] = eq.id

        if eq and eq.exists():
            if not vals.get('vehicle_plate') and eq.vehicle_plate:
                vals['vehicle_plate'] = eq.vehicle_plate
            if 'tare_weight' not in vals and eq.tare_weight > 0:
                vals['tare_weight'] = eq.tare_weight
            if not vals.get('driver_name') and eq.driver_name:
                vals['driver_name'] = eq.driver_name

    def action_update_equipment_tare(self):
        """Cập nhật khối lượng bì hiện tại của phiếu cân vào hồ sơ thiết bị cơ giới mỏ."""
        self.ensure_one()
        if not self.scale_equipment_id:
            raise UserError(_('Vui lòng chọn hoặc liên kết thiết bị cơ giới mỏ trước khi lưu bì!'))
        if self.tare_weight <= 0:
            raise UserError(_('Khối lượng bì phải lớn hơn 0 để lưu vào hồ sơ xe!'))
        vals = {'tare_weight': self.tare_weight}
        if self.driver_name and not self.scale_equipment_id.driver_name:
            vals['driver_name'] = self.driver_name
        self.scale_equipment_id.write(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đã Cập Nhật Hồ Sơ Xe'),
                'message': _('Đã cập nhật khối lượng bì chuẩn (%s Kg) vào hồ sơ xe [%s] %s!') % (
                    self.tare_weight,
                    self.scale_equipment_id.vehicle_plate or '',
                    self.scale_equipment_id.name
                ),
                'type': 'success',
                'sticky': False,
            }
        }


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

    def _apply_scale_to_moves(self):
        """Logic cốt lõi áp khối lượng từ trạm cân vào các dòng stock move."""
        self.ensure_one()
        if self.net_weight <= 0:
            return False

        for move in self.move_ids:
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
                # Mặc định quy đổi ra tấn cho đá mỏ
                qty = round(self.net_weight / 1000.0, 3)

            move.quantity = qty
            if 'product_uom_qty' in move._fields:
                move.product_uom_qty = qty
        return True

    def action_apply_scale_to_moves(self):
        """Hành động nút bấm thủ công trên giao diện."""
        self.ensure_one()
        if self.net_weight <= 0:
            raise UserError(_('Khối lượng tịnh phải lớn hơn 0 trước khi cập nhật!'))

        self._apply_scale_to_moves()
        if self.state == 'draft':
            self.with_context(skip_zero_demand_check=True).action_confirm()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành Công'),
                'message': _('Đã cập nhật khối lượng tịnh (%s Kg / %s m³) vào phiếu kho!') % (self.net_weight, self.volume_m3),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    def button_validate(self):
        """Tự động đồng bộ số lượng từ trạm cân trước khi hoàn tất phiếu kho."""
        for picking in self:
            if (picking.show_scale_tab or picking.show_explosive_tab) and picking.net_weight > 0:
                picking._apply_scale_to_moves()
        pickings_scale = self.filtered(lambda p: p.show_scale_tab or p.show_explosive_tab)
        if pickings_scale:
            return super(StockPicking, self.with_context(skip_zero_demand_check=True)).button_validate()
        return super().button_validate()

    def action_confirm(self):
        """Tự động đồng bộ số lượng từ trạm cân trước khi xác nhận phiếu kho."""
        for picking in self:
            if (picking.show_scale_tab or picking.show_explosive_tab) and picking.net_weight > 0:
                picking._apply_scale_to_moves()
        pickings_scale = self.filtered(lambda p: p.show_scale_tab or p.show_explosive_tab)
        if pickings_scale:
            return super(StockPicking, self.with_context(skip_zero_demand_check=True)).action_confirm()
        return super().action_confirm()

    def action_print_scale_ticket(self):
        """In phiếu cân điện tử chuẩn mỏ đá."""
        self.ensure_one()
        return self.env.ref('hoangphuc_stock.action_report_scale_ticket').report_action(self)
