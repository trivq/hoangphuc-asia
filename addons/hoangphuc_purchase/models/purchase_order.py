from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(
        selection_add=[
            ('waiting_gm', 'Chờ TGĐ Phê Duyệt'),
            ('waiting_chairman', 'Chờ Chủ Tịch HĐQT Phê Duyệt'),
            ('purchase',),
        ],
        ondelete={
            'waiting_gm': 'set default',
            'waiting_chairman': 'set default',
        }
    )

    user_is_gm = fields.Boolean(
        string='Người Dùng Là TGĐ',
        compute='_compute_user_approval_roles',
        help='Kiểm tra user đăng nhập có quyền Tổng Giám Đốc hay không'
    )
    user_is_chairman = fields.Boolean(
        string='Người Dùng Là Chủ Tịch HĐQT',
        compute='_compute_user_approval_roles',
        help='Kiểm tra user đăng nhập có quyền Chủ Tịch HĐQT hay không'
    )
    user_can_gm_approve = fields.Boolean(
        string='Có Quyền Duyệt TGĐ',
        compute='_compute_user_approval_roles',
    )
    user_can_chairman_approve = fields.Boolean(
        string='Có Quyền Duyệt Chủ Tịch',
        compute='_compute_user_approval_roles',
    )
    user_can_reject = fields.Boolean(
        string='Có Quyền Trả Lại Dự Thảo',
        compute='_compute_user_approval_roles',
    )

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Thiết Bị / Cơ Giới Chịu Chi Phí',
        tracking=True,
        help='Bắt buộc gắn đích danh xe ben, máy xúc hoặc trạm nghiền chịu chi phí (BR-10).'
    )
    is_single_source = fields.Boolean(
        string='Mua 1 Nguồn Duy Nhất (Chỉ Định Thầu)',
        default=False,
        tracking=True,
        help='Đánh dấu nếu không có 3 báo giá cạnh tranh (BR-02).'
    )
    single_source_reason = fields.Text(
        string='Giải Trình Mua 1 Nguồn Duy Nhất',
        tracking=True,
        help='Giải trình lý do kỹ thuật độc quyền hoặc khẩn cấp (BR-04).'
    )
    quote_source_1 = fields.Char(string='NCC Báo Giá 1')
    quote_price_1 = fields.Monetary(string='Giá Báo 1', currency_field='currency_id')
    quote_source_2 = fields.Char(string='NCC Báo Giá 2')
    quote_price_2 = fields.Monetary(string='Giá Báo 2', currency_field='currency_id')
    quote_source_3 = fields.Char(string='NCC Báo Giá 3')
    quote_price_3 = fields.Monetary(string='Giá Báo 3', currency_field='currency_id')

    approval_tier = fields.Selection([
        ('tier_1', 'Cấp 1: TGĐ Phê Duyệt (<= 20M)'),
        ('tier_2', 'Cấp 2: Chủ Tịch HĐQT Phê Duyệt (> 20M)')
    ], string='Phân Cấp Thẩm Quyền Tài Chính', compute='_compute_approval_tier', store=True)

    field_inspected = fields.Boolean(
        string='Đã Nghiệm Thu Hiện Trường',
        default=False,
        tracking=True,
        help='Nghiệm thu thực tế tại moong mỏ hoặc xưởng (BR-05).'
    )
    field_inspector_id = fields.Many2one(
        'res.users',
        string='Người Nghiệm Thu Thực Tế',
        tracking=True
    )
    field_inspection_photo = fields.Binary(
        string='Ảnh Bàn Giao Hiện Trường',
        attachment=True,
        help='Hình ảnh chụp thực tế phụ tùng/vật tư tại bãi mỏ.'
    )
    supplier_payment_term_type = fields.Selection([
        ('standard', 'Theo Đơn Hàng (Thanh toán theo tiến độ)'),
        ('special_1m', 'Nợ Gối Đầu 1 Tháng (Túy Hoài, Đức Soạn, Tiến Lốp)')
    ], string='Chính Sách Công Nợ NCC', default='standard', tracking=True)

    @api.depends_context('uid')
    @api.depends('state')
    def _compute_user_approval_roles(self):
        user = self.env.user
        is_su = self.env.is_superuser()
        is_gm = bool(user.is_general_manager or is_su)
        is_chairman = bool(user.is_board_chairman or is_su)
        for po in self:
            po.user_is_gm = is_gm
            po.user_is_chairman = is_chairman
            po.user_can_gm_approve = bool(is_gm and po.state == 'waiting_gm')
            po.user_can_chairman_approve = bool(is_chairman and po.state == 'waiting_chairman')
            po.user_can_reject = bool(
                (po.state == 'waiting_gm' and is_gm) or
                (po.state == 'waiting_chairman' and is_chairman)
            )

    def _approval_allowed(self):
        user = self.env.user
        if user.is_board_chairman or user.is_general_manager or self.env.is_superuser():
            return True
        return super()._approval_allowed()

    @api.model
    def _get_purchase_approval_limit(self):
        """Lấy hạn mức thẩm quyền phê duyệt TGĐ từ cấu hình hệ thống (mặc định 20.000.000 VNĐ)."""
        try:
            limit = self.env['ir.config_parameter'].sudo().get_float(
                'hoangphuc_purchase.purchase_approval_limit', 20_000_000.0
            )
        except Exception:
            val = self.env['ir.config_parameter'].sudo().get_param('hoangphuc_purchase.purchase_approval_limit', 20_000_000.0)
            limit = float(val or 20_000_000.0)
        return limit if limit > 0 else 20_000_000.0

    @api.depends('amount_total')
    def _compute_approval_tier(self):
        approval_limit = self._get_purchase_approval_limit()
        for order in self:
            if order.amount_total > approval_limit:
                order.approval_tier = 'tier_2'
            else:
                order.approval_tier = 'tier_1'

    def button_confirm(self):
        """Xác nhận đơn hàng hoặc trình cấp thẩm quyền phê duyệt tài chính BR-03."""
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue

            # Kiểm tra bắt buộc giải trình 1 nguồn duy nhất (BR-02, BR-04)
            if order.is_single_source and not (order.single_source_reason or '').strip():
                raise UserError(_('Bắt buộc nhập Giải trình lý do mua 1 nguồn duy nhất (BR-02, BR-04) trước khi xác nhận đơn hàng!'))

            approval_limit = order._get_purchase_approval_limit()
            user = self.env.user
            is_su = self.env.is_superuser()

            # Trường hợp 1: Chủ Tịch HĐQT trực tiếp xác nhận -> Phê duyệt thẳng
            if user.is_board_chairman or is_su:
                super(PurchaseOrder, order).button_confirm()
                order.message_post(body=_('Chủ Tịch HĐQT (%s) đã trực tiếp phê duyệt đơn hàng.') % user.name)
                continue

            # Trường hợp 2: TGĐ trực tiếp xác nhận và đơn hàng <= hạn mức 20M -> Phê duyệt thẳng
            if user.is_general_manager and order.amount_total <= approval_limit:
                super(PurchaseOrder, order).button_confirm()
                order.message_post(body=_('Tổng Giám Đốc (%s) đã trực tiếp phê duyệt đơn hàng (Tổng tiền: %s VNĐ <= Hạn mức %s VNĐ).') % (
                    user.name, f'{order.amount_total:,.0f}', f'{approval_limit:,.0f}'))
                continue

            # Trường hợp 3: Nhân viên mua sắm (hoặc TGĐ đối với đơn > 20M) -> Chuyển vào luồng duyệt
            order.write({'state': 'waiting_gm'})
            formatted_limit = f'{approval_limit:,.0f}'
            formatted_amount = f'{order.amount_total:,.0f}'
            if order.amount_total <= approval_limit:
                order.message_post(body=_('Đơn hàng [%s VNĐ <= Hạn mức %s VNĐ] đã được chuyển lên Tổng Giám Đốc phê duyệt.') % (formatted_amount, formatted_limit))
            else:
                order.message_post(body=_('Đơn hàng [%s VNĐ > Hạn mức %s VNĐ] vượt hạn mức, đã chuyển Tổng Giám Đốc xem xét để trình Chủ Tịch HĐQT phê duyệt tối cao.') % (formatted_amount, formatted_limit))
        return True

    def action_gm_approve(self):
        """TGĐ Phê duyệt: nếu <= hạn mức xong luôn (vào 'purchase'), nếu > hạn mức đẩy lên 'waiting_chairman'."""
        self.ensure_one()
        user = self.env.user
        if not (user.is_general_manager or self.env.is_superuser()):
            raise UserError(_('Chỉ người dùng có thẩm quyền Tổng Giám Đốc (TGĐ) mới được phê duyệt bước này!'))
        if self.state != 'waiting_gm':
            raise UserError(_('Đơn hàng không ở trạng thái Chờ TGĐ Phê Duyệt!'))

        approval_limit = self._get_purchase_approval_limit()
        formatted_limit = f'{approval_limit:,.0f}'
        formatted_amount = f'{self.amount_total:,.0f}'

        if self.amount_total <= approval_limit:
            # Thuộc thẩm quyền TGĐ -> Duyệt thẳng vào Đơn mua hàng (purchase)
            self.button_approve()
            self.message_post(body=_('Tổng Giám Đốc (%s) đã phê duyệt hoàn tất đơn hàng (Tổng tiền: %s VNĐ <= Hạn mức %s VNĐ). Đơn hàng chính thức có hiệu lực!') % (user.name, formatted_amount, formatted_limit))
        else:
            # Vượt thẩm quyền TGĐ -> Chuyển tiếp lên Chủ tịch HĐQT
            self.write({'state': 'waiting_chairman'})
            self.message_post(body=_('Tổng Giám Đốc (%s) đã xem xét và chuyển Chủ Tịch HĐQT phê duyệt tối cao (Tổng tiền: %s VNĐ > Hạn mức %s VNĐ).') % (user.name, formatted_amount, formatted_limit))
        return True

    def action_chairman_approve(self):
        """Chủ tịch HĐQT phê duyệt tối cao đơn hàng vượt hạn mức TGĐ -> Chuyển thẳng sang 'purchase'."""
        self.ensure_one()
        user = self.env.user
        if not (user.is_board_chairman or self.env.is_superuser()):
            raise UserError(_('Chỉ người dùng có thẩm quyền Chủ Tịch HĐQT mới được phê duyệt bước này!'))
        if self.state != 'waiting_chairman':
            raise UserError(_('Đơn hàng không ở trạng thái Chờ Chủ Tịch HĐQT Phê Duyệt!'))

        formatted_amount = f'{self.amount_total:,.0f}'
        self.button_approve()
        self.message_post(body=_('Chủ Tịch HĐQT (%s) đã phê duyệt tối cao cho đơn hàng (%s VNĐ). Đơn hàng chính thức có hiệu lực!') % (user.name, formatted_amount))
        return True

    def action_reject_to_draft(self):
        """Cấp thẩm quyền trả lại đơn hàng về Dự thảo để điều chỉnh giá / bổ sung báo giá."""
        self.ensure_one()
        user = self.env.user
        is_su = self.env.is_superuser()
        if self.state == 'waiting_gm' and not (user.is_general_manager or is_su):
            raise UserError(_('Chỉ Tổng Giám Đốc mới có quyền từ chối / trả lại đơn hàng ở bước này!'))
        if self.state == 'waiting_chairman' and not (user.is_board_chairman or is_su):
            raise UserError(_('Chỉ Chủ Tịch HĐQT mới có quyền từ chối / trả lại đơn hàng ở bước này!'))
        if self.state not in ['waiting_gm', 'waiting_chairman']:
            raise UserError(_('Chỉ có thể trả lại đơn hàng khi đang ở trạng thái chờ phê duyệt!'))

        self.write({'state': 'draft'})
        self.message_post(body=_('%s đã từ chối phê duyệt và trả lại đơn hàng về trạng thái Dự Thảo để điều chỉnh.') % user.name)
        return True
