from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
    is_deposit_insufficient = fields.Boolean(
        string='Số Dư Ký Quỹ Không Đủ',
        compute='_compute_credit_warning'
    )

    deposit_history_id = fields.Many2one(
        'customer.deposit.history',
        string='Giao Dịch Trừ Tiền Ký Quỹ',
        readonly=True,
        copy=False,
        help='Lịch sử trừ tiền ký quỹ khi đơn hàng được xác nhận.'
    )

    @api.depends('partner_id', 'partner_id.credit_status', 'partner_id.deposit_balance', 'partner_id.quarry_credit_limit', 'amount_total')
    def _compute_credit_warning(self):
        for order in self:
            msg = False
            insufficient = False
            partner = order.partner_id
            if partner:
                if partner.quarry_customer_type == 'prepaid':
                    if partner.deposit_balance <= 0:
                        insufficient = True
                        msg = _('CẢNH BÁO: Khách hàng chưa nộp tiền ký quỹ (Số dư: 0 VNĐ)! Không thể xác nhận đơn hàng.')
                    elif partner.deposit_balance < order.amount_total:
                        insufficient = True
                        shortage = order.amount_total - partner.deposit_balance
                        msg = _(
                            'CẢNH BÁO: Số dư ký quỹ hiện tại (%(balance)s VNĐ) THẤP HƠN tổng tiền đơn hàng (%(total)s VNĐ)! '
                            'Còn thiếu %(shortage)s VNĐ. Không thể xác nhận đơn hàng cho đến khi khách nạp thêm tiền.'
                        ) % {
                            'balance': f'{partner.deposit_balance:,.0f}',
                            'total': f'{order.amount_total:,.0f}',
                            'shortage': f'{shortage:,.0f}',
                        }
                    elif partner.deposit_balance < 10_000_000:
                        msg = _('LƯU Ý: Số dư ký quỹ sắp hết (Còn lại: %s VNĐ). Cần nhắc khách hàng nạp bổ sung.') % f'{partner.deposit_balance:,.0f}'
                else:
                    current_debt = partner.credit or 0.0
                    new_debt = current_debt + order.amount_total
                    if partner.quarry_credit_limit > 0 and new_debt > partner.quarry_credit_limit:
                        insufficient = True
                        msg = _('CẢNH BÁO: Đơn hàng này sẽ làm khách hàng vượt hạn mức nợ (Hạn mức: %s VNĐ, Nợ sau đơn: %s VNĐ)!') % (
                            f'{partner.quarry_credit_limit:,.0f}',
                            f'{new_debt:,.0f}',
                        )
            order.credit_warning_msg = msg
            order.is_deposit_insufficient = insufficient

    def action_quick_deposit(self):
        """Mở popup nạp tiền ký quỹ nhanh trực tiếp từ Đơn bán hàng."""
        self.ensure_one()
        shortage = max(0.0, self.amount_total - self.partner_id.deposit_balance)
        return {
            'name': _('Nạp Tiền Ký Quỹ Cho Khách Hàng - %s') % self.partner_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'customer.deposit.history',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_transaction_type': 'deposit',
                'default_amount': shortage if shortage > 0 else 0.0,
                'default_payment_method': 'bank',
                'default_notes': _('Nạp tiền ký quỹ để thanh toán đơn hàng %s (Dự án: %s)') % (self.name, self.project_name or 'N/A'),
            }
        }

    def action_confirm(self):
        """Xác nhận đơn hàng: Nếu khách trả trước, kiểm tra số dư và trừ tiền ký quỹ."""
        for order in self:
            partner = order.partner_id
            if partner.quarry_customer_type == 'prepaid' and order.amount_total > 0:
                if partner.deposit_balance < order.amount_total:
                    shortage = order.amount_total - partner.deposit_balance
                    raise UserError(_(
                        'CẢNH BÁO: KHÔNG THỂ XÁC NHẬN ĐƠN HÀNG!\n\n'
                        'Khách hàng [%(partner)s] thuộc diện Trả trước (Ký quỹ tiền cọc), '
                        'hiện tại số dư ký quỹ thấp hơn tổng giá trị đơn hàng:\n\n'
                        '• Tổng tiền đơn hàng: %(order_amount)s VNĐ\n'
                        '• Số dư ký quỹ hiện tại: %(deposit_balance)s VNĐ\n'
                        '• Số tiền còn thiếu: %(shortage)s VNĐ\n\n'
                        'Vui lòng nạp thêm tiền ký quỹ cho khách hàng (tối thiểu %(shortage)s VNĐ) trước khi xác nhận xuất hàng!',
                        partner=partner.name,
                        order_amount=f'{order.amount_total:,.0f}',
                        deposit_balance=f'{partner.deposit_balance:,.0f}',
                        shortage=f'{shortage:,.0f}',
                    ))

        res = super().action_confirm()

        deposit_history_obj = self.env['customer.deposit.history']
        for order in self:
            partner = order.partner_id
            if partner.quarry_customer_type == 'prepaid' and order.amount_total > 0 and not order.deposit_history_id:
                tx = deposit_history_obj.create({
                    'partner_id': partner.id,
                    'transaction_type': 'deduct',
                    'amount': order.amount_total,
                    'order_id': order.id,
                    'date': fields.Datetime.now(),
                    'state': 'posted',
                    'notes': _('Trừ tiền xuất đá cho đơn hàng %s (Dự án/Công trình: %s).') % (
                        order.name, order.project_name or 'N/A'
                    ),
                })
                order.deposit_history_id = tx.id
                order.message_post(body=_(
                    'Đã trừ thành công <b>%s VNĐ</b> từ Số dư ký quỹ của khách hàng (Mã GD: <a href="#" data-oe-model="customer.deposit.history" data-oe-id="%s">%s</a>). '
                    'Số dư ký quỹ còn lại: <b>%s VNĐ</b>.'
                ) % (
                    f'{order.amount_total:,.0f}',
                    tx.id,
                    tx.name,
                    f'{partner.deposit_balance:,.0f}',
                ))
        return res

    def action_cancel(self):
        """Hủy đơn hàng: Hoàn lại tiền ký quỹ nếu đã trừ tiền trước đó."""
        deposit_history_obj = self.env['customer.deposit.history']
        for order in self:
            if order.deposit_history_id and order.deposit_history_id.state == 'posted':
                refund_tx = deposit_history_obj.create({
                    'partner_id': order.partner_id.id,
                    'transaction_type': 'refund',
                    'amount': order.deposit_history_id.amount,
                    'order_id': order.id,
                    'date': fields.Datetime.now(),
                    'state': 'posted',
                    'notes': _('Hoàn trả tiền ký quỹ do hủy đơn hàng %s (Giao dịch trừ ban đầu: %s).') % (
                        order.name, order.deposit_history_id.name
                    ),
                })
                order.message_post(body=_(
                    'Đã hoàn trả <b>%s VNĐ</b> vào Số dư ký quỹ do đơn hàng bị hủy (Mã GD hoàn tiền: %s).'
                ) % (
                    f'{order.deposit_history_id.amount:,.0f}',
                    refund_tx.name,
                ))
        return super().action_cancel()

    def action_draft(self):
        for order in self:
            order.deposit_history_id = False
        return super().action_draft()
