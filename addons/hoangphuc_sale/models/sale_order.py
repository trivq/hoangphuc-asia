from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_name = fields.Char(
        string='Công Trình / Dự Án Nhận Đá',
        tracking=True,
        help='Tên công trình nhận đá (VD: Dự án Cao tốc Bắc - Nam, Tuyến đường Nghi Sơn - Sao Vàng...)'
    )
    contract_ref = fields.Char(
        string='Số Hợp Đồng Mỏ Đá',
        tracking=True,
        help='Số hiệu hợp đồng nguyên tắc hoặc hợp đồng kinh tế đã ký kết.'
    )
    quarry_uom_type = fields.Selection([
        ('ton', 'Bán Theo Tấn (Trọng Lượng Cân)'),
        ('m3', 'Bán Theo Mét Khối (Thể Tích m³)')
    ], string='Quy Cách Tính Giá Hợp Đồng', default='ton', tracking=True)

    partner_quarry_type = fields.Selection(
        related='partner_id.quarry_customer_type',
        string='Loại Khách Hàng',
        readonly=True
    )
    partner_credit_status = fields.Selection(
        related='partner_id.credit_status',
        string='Trạng Thái Tín Dụng Khách Hàng',
        readonly=True
    )
    partner_deposit_balance = fields.Monetary(
        related='partner_id.deposit_balance',
        currency_field='currency_id',
        string='Số Dư Ký Quỹ Còn Lại',
        readonly=True
    )
    credit_warning_msg = fields.Char(
        string='Thông Báo Tín Dụng',
        compute='_compute_credit_warning'
    )

    @api.depends('partner_id', 'partner_id.credit_status', 'partner_id.deposit_balance', 'partner_id.quarry_credit_limit')
    def _compute_credit_warning(self):
        for order in self:
            msg = False
            partner = order.partner_id
            if partner:
                if partner.quarry_customer_type == 'prepaid':
                    if partner.deposit_balance <= 0:
                        msg = _('CẢNH BÁO: Khách hàng chưa nộp tiền ký quỹ (Số dư: 0 VNĐ)! Không cho phép xuất đá.')
                    elif partner.deposit_balance < 10_000_000:
                        msg = _('LƯU Ý: Số dư ký quỹ sắp hết (Còn lại: %s VNĐ). Cần nhắc khách nộp bổ sung.') % '{:,.0f}'.format(partner.deposit_balance)
                else:
                    if partner.credit_status == 'blocked':
                        msg = _('CẢNH BÁO: Khách hàng đã chạm/vượt hạn mức nợ (%s VNĐ)! Không cho phép xuất đá.') % '{:,.0f}'.format(partner.quarry_credit_limit)
            order.credit_warning_msg = msg
