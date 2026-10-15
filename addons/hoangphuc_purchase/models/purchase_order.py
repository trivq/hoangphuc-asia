from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

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
        ('tier_1', 'Cấp 1: TGĐ Phê Duyệt'),
        ('tier_2', 'Cấp 2: Chủ Tịch HĐQT Phê Duyệt')
    ], string='Phân Cấp Thẩm Quyền Tài Chính', compute='_compute_approval_tier', store=True)

    approval_state = fields.Selection([
        ('draft', 'Mới Lập'),
        ('waiting_gm', 'Chờ TGĐ Phê Duyệt'),
        ('waiting_chairman', 'Chờ Chủ Tịch HĐQT Phê Duyệt'),
        ('approved', 'Đã Phê Duyệt Thẩm Quyền'),
        ('rejected', 'Từ Chối')
    ], string='Trạng Thái Duyệt Tài Chính', default='draft', tracking=True)

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

    def action_submit_for_approval(self):
        """Trình ký duyệt tài chính."""
        self.ensure_one()
        if self.is_single_source and not (self.single_source_reason or '').strip():
            raise UserError(_('Bắt buộc nhập Giải trình lý do mua 1 nguồn duy nhất (BR-02, BR-04)!'))
        self.approval_state = 'waiting_gm'

    def action_gm_approve(self):
        """TGĐ Phê duyệt: nếu <= hạn mức xong luôn, nếu > hạn mức đẩy lên CT HĐQT."""
        self.ensure_one()
        approval_limit = self._get_purchase_approval_limit()
        formatted_limit = f'{approval_limit:,.0f}'
        if self.approval_tier == 'tier_1':
            self.approval_state = 'approved'
            self.message_post(body=_('Tổng Giám Đốc đã phê duyệt đơn hàng (Thẩm quyền <= %s VNĐ).') % formatted_limit)
        else:
            self.approval_state = 'waiting_chairman'
            self.message_post(body=_('Tổng Giám Đốc đã xem xét và chuyển Chủ Tịch HĐQT phê duyệt (Đơn hàng > %s VNĐ).') % formatted_limit)

    def action_chairman_approve(self):
        """Chủ tịch HĐQT phê duyệt đơn hàng vượt hạn mức TGĐ."""
        self.ensure_one()
        self.approval_state = 'approved'
        self.message_post(body=_('Chủ Tịch HĐQT đã phê duyệt tối cao cho đơn hàng.'))

    def action_reject(self):
        """Từ chối đơn hàng."""
        self.ensure_one()
        self.approval_state = 'rejected'
        self.message_post(body=_('Đơn mua sắm đã bị từ chối phê duyệt.'))

    def action_reset_draft(self):
        """Làm lại."""
        self.ensure_one()
        self.approval_state = 'draft'

    def button_confirm(self):
        """Chặn xác nhận đơn hàng nếu chưa được phê duyệt thẩm quyền tài chính."""
        for order in self:
            if order.approval_state != 'approved':
                raise UserError(_('Đơn hàng "%s" chưa được phê duyệt thẩm quyền tài chính (BR-03)! Vui lòng trình phê duyệt trước khi Xác nhận.') % order.name)
        return super().button_confirm()
