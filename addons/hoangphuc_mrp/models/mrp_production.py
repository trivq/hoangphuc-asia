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

    quarry_picking_count = fields.Integer(
        string='Số Phiếu Chuyển Kho',
        compute='_compute_quarry_picking_count',
        help='Tổng số phiếu chuyển kho (cấp liệu, bổ sung hoặc trả hàng) liên quan đến lệnh sản xuất này.'
    )

    def _compute_quarry_picking_count(self):
        for mo in self:
            mo.quarry_picking_count = len(mo._get_related_component_pickings())

    def _get_quarry_raw_stone_move(self):
        """Xác định chính xác dòng nguyên liệu đá thô trong tab Thành phần (move_raw_ids)."""
        self.ensure_one()
        if not self.move_raw_ids:
            return self.env['stock.move']

        # 1. Ưu tiên sản phẩm có đánh dấu đá mỏ (is_quarry_stone)
        stone_moves = self.move_raw_ids.filtered(
            lambda m: getattr(m.product_id, 'is_quarry_stone', False)
        )
        if stone_moves:
            return stone_moves[0]

        # 2. Tìm theo từ khóa đặc trưng của đá thô / đá hộc khai thác
        raw_keywords = ['đá hộc', 'đá thô', 'nguyên khai', 'đá mỏ', 'boulder', 'raw']
        for kw in raw_keywords:
            matched = self.move_raw_ids.filtered(
                lambda m: kw in (m.product_id.name or '').lower() or
                          (m.product_id.categ_id and kw in (m.product_id.categ_id.name or '').lower())
            )
            if matched:
                return matched[0]

        # 3. Fallback: Dòng nguyên liệu đầu tiên
        return self.move_raw_ids[0]

    def _get_related_component_pickings(self, target_raw_move=None):
        """Tìm toàn bộ các phiếu chuyển kho (stock.picking) liên quan đến việc cấp liệu cho MO này."""
        self.ensure_one()
        pickings = self.env['stock.picking']

        # A. Lấy từ picking_ids có sẵn của MO (native Odoo 20)
        if hasattr(self, 'picking_ids') and self.picking_ids:
            pickings |= self.picking_ids

        # B. Tìm qua chuỗi cung ứng move_orig_ids của dòng nguyên liệu
        if target_raw_move and target_raw_move.move_orig_ids:
            pickings |= target_raw_move.move_orig_ids.picking_id
        elif self.move_raw_ids.move_orig_ids:
            pickings |= self.move_raw_ids.move_orig_ids.picking_id

        # C. Tìm qua picking_id trực tiếp trên move_raw_ids / move_finished_ids nếu có
        if hasattr(self.move_raw_ids, 'picking_id'):
            pickings |= self.move_raw_ids.picking_id
        if hasattr(self.move_finished_ids, 'picking_id'):
            pickings |= self.move_finished_ids.picking_id

        # D. Tìm qua trường origin gắn mã MO
        if self.name:
            pickings |= self.env['stock.picking'].search([
                ('origin', 'ilike', self.name)
            ])

        return pickings.filtered(lambda p: p.state != 'cancel')

    def _create_extra_component_picking(self, target_raw_move, qty, ref_picking):
        """Tự động tạo phiếu chuyển hàng BỔ SUNG khi thực tế nhiều hơn ban đầu (+ delta)."""
        self.ensure_one()
        prod = target_raw_move.product_id

        picking_vals = {
            'picking_type_id': ref_picking.picking_type_id.id,
            'location_id': ref_picking.location_id.id,
            'location_dest_id': ref_picking.location_dest_id.id,
            'origin': _('%s: Cấp bổ sung đá thô (+%s Tấn)') % (self.name, round(qty, 2)),
            'move_ids': [
                (0, 0, {
                    'description_picking': _('Cấp bổ sung %s cho %s') % (prod.display_name, self.name),
                    'product_id': prod.id,
                    'product_uom_qty': qty,
                    'quantity': qty,
                    'uom_id': prod.uom_id.id,
                    'location_id': ref_picking.location_id.id,
                    'location_dest_id': ref_picking.location_dest_id.id,
                    'origin': self.name,
                    'production_group_id': self.production_group_id.id if hasattr(self, 'production_group_id') and self.production_group_id else False,
                    'move_dest_ids': [(4, target_raw_move.id)],
                })
            ]
        }
        new_picking = self.env['stock.picking'].create(picking_vals)
        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking

    def _create_return_component_picking(self, target_raw_move, qty, ref_picking):
        """Tự động tạo phiếu TRẢ HÀNG THỪA về bãi kho khi thực tế ít hơn ban đầu (- delta)."""
        self.ensure_one()
        prod = target_raw_move.product_id
        wh = ref_picking.picking_type_id.warehouse_id
        # Sử dụng loại hoạt động điều chuyển nội bộ của kho nếu có
        picking_type = wh.int_type_id if wh and wh.int_type_id else ref_picking.picking_type_id

        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': ref_picking.location_dest_id.id,  # Từ trạm nghiền / pre-production
            'location_dest_id': ref_picking.location_id.id,    # Trả về bãi kho chính / stock
            'origin': _('%s: Trả đá thô thừa về bãi kho (-%s Tấn)') % (self.name, round(qty, 2)),
            'move_ids': [
                (0, 0, {
                    'description_picking': _('Hoàn trả đá thô thừa %s từ %s') % (prod.display_name, self.name),
                    'product_id': prod.id,
                    'product_uom_qty': qty,
                    'quantity': qty,
                    'uom_id': prod.uom_id.id,
                    'location_id': ref_picking.location_dest_id.id,
                    'location_dest_id': ref_picking.location_id.id,
                    'origin': self.name,
                    'production_group_id': self.production_group_id.id if hasattr(self, 'production_group_id') and self.production_group_id else False,
                })
            ]
        }
        return_picking = self.env['stock.picking'].create(picking_vals)
        return_picking.action_confirm()
        return_picking.action_assign()
        return return_picking

    def action_view_related_pickings(self):
        """Mở danh sách các lệnh chuyển hàng liên quan đến lệnh sản xuất này."""
        self.ensure_one()
        pickings = self._get_related_component_pickings()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        if len(pickings) == 1:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        else:
            action['domain'] = [('id', 'in', pickings.ids)]
        action['context'] = {'default_origin': self.name}
        return action

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
        """Tự động cập nhật khối lượng đá thô cấp liệu vào dòng nguyên liệu tiêu hao
        và đồng bộ Lệnh chuyển hàng (stock.picking) liên quan:
        1. Cập nhật số lượng tiêu hao trên đúng dòng nguyên liệu đá thô của MO.
        2. Nếu Lệnh chuyển hàng chưa Done -> cập nhật lại số lượng trên phiếu chuyển hàng.
        3. Nếu Lệnh chuyển hàng đã Done:
           - Thực tế nhiều hơn ban đầu -> Tự động sinh phiếu chuyển hàng bổ sung (+ chênh lệch).
           - Thực tế ít hơn ban đầu -> Tự động sinh phiếu trả hàng (- chênh lệch) về bãi kho.
        """
        self.ensure_one()
        if self.raw_stone_input_qty <= 0:
            raise UserError(_('Vui lòng nhập Khối lượng đá thô cấp liệu lớn hơn 0!'))

        target_move = self._get_quarry_raw_stone_move()
        if not target_move:
            raise UserError(_('Không tìm thấy dòng nguyên liệu đá thô phù hợp trong tab Thành phần để cập nhật!'))

        new_qty = self.raw_stone_input_qty
        prod = target_move.product_id

        # 1. Cập nhật đúng dòng nguyên liệu đá thô trên MO
        target_move.quantity = new_qty
        if 'product_uom_qty' in target_move._fields:
            target_move.product_uom_qty = new_qty

        # 2. Tìm các lệnh chuyển hàng (stock.picking) liên quan đến việc cấp liệu cho MO
        related_pickings = self._get_related_component_pickings(target_move)

        # Lọc các dòng move trong phiếu chuyển kho chuyển đúng sản phẩm này
        component_moves = self.env['stock.move']
        for p in related_pickings:
            component_moves |= p.move_ids.filtered(
                lambda m: m.product_id == prod and m.state != 'cancel'
            )

        messages = [
            _('1. Tab Thành Phần: Đã cập nhật %s thành %s Tấn.') % (prod.display_name, new_qty)
        ]
        notification_type = 'success'

        if not component_moves:
            messages.append(_('2. Lệnh Chuyển Hàng: Chưa phát sinh phiếu chuyển kho linh kiện nào cho lệnh này.'))
        else:
            done_moves = component_moves.filtered(lambda m: m.state == 'done')
            undone_moves = component_moves.filtered(lambda m: m.state != 'done')

            if undone_moves:
                # KỊCH BẢN 1: Còn lệnh chuyển hàng CHƯA DONE -> Cập nhật trực tiếp số lượng
                done_qty = sum(m.quantity or m.product_uom_qty for m in done_moves)
                needed_for_undone = max(0.0, new_qty - done_qty)

                primary_undone_move = undone_moves[0]
                primary_undone_move.product_uom_qty = needed_for_undone
                if primary_undone_move.quantity:
                    primary_undone_move.quantity = needed_for_undone

                for extra_undone in undone_moves[1:]:
                    extra_undone.product_uom_qty = 0.0
                    if extra_undone.quantity:
                        extra_undone.quantity = 0.0

                picking_names = ", ".join(undone_moves.mapped('picking_id.name'))
                messages.append(
                    _('2. Lệnh Chuyển Hàng [%s] (Chưa Done): Đã cập nhật lại số lượng cần chuyển thành %s Tấn.') % (
                        picking_names, round(needed_for_undone, 2)
                    )
                )
            else:
                # KỊCH BẢN 2: TẤT CẢ các lệnh chuyển hàng ĐÃ DONE
                total_done_qty = sum(m.quantity or m.product_uom_qty for m in done_moves)
                delta = new_qty - total_done_qty
                ref_picking = done_moves[0].picking_id

                if abs(delta) < 0.001:
                    messages.append(
                        _('2. Lệnh Chuyển Hàng: Khối lượng thực tế trùng khớp với khối lượng đã chuyển (%s Tấn).') % total_done_qty
                    )
                elif delta > 0:
                    # KỊCH BẢN 2A: Thực tế NHIỀU HƠN -> Tạo Phiếu Chuyển Bổ Sung (+delta)
                    new_picking = self._create_extra_component_picking(target_move, delta, ref_picking)
                    messages.append(
                        _('2. Lệnh Chuyển Hàng: Phiếu trước đã hoàn tất (%s Tấn). Đã tự động tạo thêm Phiếu Chuyển Bổ Sung [%s] cho phần chênh lệch +%s Tấn!') % (
                            round(total_done_qty, 2), new_picking.name, round(delta, 2)
                        )
                    )
                else:
                    # KỊCH BẢN 2B: Thực tế ÍT HƠN -> Tạo Phiếu Trả Hàng Thừa (-delta)
                    return_qty = abs(delta)
                    return_picking = self._create_return_component_picking(target_move, return_qty, ref_picking)
                    messages.append(
                        _('2. Lệnh Chuyển Hàng: Phiếu trước đã xuất %s Tấn (thực tế chỉ dùng %s Tấn). Đã tự động tạo Phiếu Trả Hàng [%s] hoàn trả %s Tấn về bãi kho!') % (
                            round(total_done_qty, 2), round(new_qty, 2), return_picking.name, round(return_qty, 2)
                        )
                    )
                    notification_type = 'warning'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đồng Bộ Cấp Liệu Thành Công'),
                'message': " \n".join(messages),
                'type': notification_type,
                'sticky': True if notification_type in ('warning', 'danger') else False,
            }
        }
