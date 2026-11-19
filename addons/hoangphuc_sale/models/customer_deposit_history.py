from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CustomerDepositHistory(models.Model):
    _name = 'customer.deposit.history'
    _description = 'Lịch Sử Giao Dịch Ký Quỹ Mỏ Đá'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Mã Giao Dịch',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Mới'),
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Khách Hàng Ký Quỹ',
        required=True,
        index=True,
        tracking=True,
        domain="[('quarry_customer_type', '=', 'prepaid')]"
    )
    date = fields.Datetime(
        string='Thời Gian',
        required=True,
        default=fields.Datetime.now,
        index=True,
        tracking=True
    )
    transaction_type = fields.Selection([
        ('deposit', 'Nạp Tiền Ký Quỹ'),
        ('deduct', 'Trừ Tiền Xuất Đá (Đơn Hàng)'),
        ('refund', 'Hoàn Trả Tiền Cọc'),
    ], string='Loại Giao Dịch', required=True, default='deposit', index=True, tracking=True)

    amount = fields.Monetary(
        string='Số Tiền (VNĐ)',
        currency_field='currency_id',
        required=True,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền Tệ',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Công Ty',
        default=lambda self: self.env.company,
        required=True
    )
    balance_after = fields.Monetary(
        string='Số Dư Sau GD',
        currency_field='currency_id',
        readonly=True,
        help='Số dư ký quỹ của khách hàng sau khi giao dịch này được ghi nhận'
    )

    # Nạp tiền ký quỹ (Chứng từ sao kê / Phiếu thu)
    payment_method = fields.Selection([
        ('bank', 'Chuyển Khoản Ngân Hàng'),
        ('cash', 'Tiền Mặt Tại Quầy/Trạm Cân'),
    ], string='Hình Thức Nộp Tiền', default='bank', tracking=True)
    bank_ref = fields.Char(
        string='Mã Giao Dịch / Số Bút Toán NH',
        tracking=True,
        help='Mã giao dịch ngân hàng, số UNC hoặc số phiếu thu kế toán'
    )
    proof_image = fields.Binary(
        string='Ảnh Sao Kê / Phiếu Thu',
        attachment=True,
        help='Hình ảnh chụp sao kê chuyển khoản hoặc phiếu thu tiền mặt'
    )
    proof_attachment_ids = fields.Many2many(
        'ir.attachment',
        'customer_deposit_attachment_rel',
        'deposit_id',
        'attachment_id',
        string='File Đính Kèm Sao Kê / UNC',
        help='Tải lên sao kê ngân hàng, giấy báo có hoặc phiếu thu tiền mặt'
    )

    # Trừ tiền đơn hàng (Liên kết Sale Order)
    order_id = fields.Many2one(
        'sale.order',
        string='Đơn Hàng Liên Kết (Sale Order)',
        ondelete='set null',
        index=True,
        tracking=True
    )

    user_id = fields.Many2one(
        'res.users',
        string='Người Lập',
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True
    )
    notes = fields.Text(string='Ghi Chú / Nội Dung Giao Dịch')
    state = fields.Selection([
        ('draft', 'Dự Thảo'),
        ('posted', 'Đã Xác Nhận'),
        ('cancel', 'Đã Hủy'),
    ], string='Trạng Thái', default='posted', tracking=True, index=True)

    @api.constrains('amount')
    def _check_amount(self):
        for tx in self:
            if tx.amount <= 0:
                raise ValidationError(_('Số tiền giao dịch phải lớn hơn 0!'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                tx_type = vals.get('transaction_type', 'deposit')
                prefix = 'NAP' if tx_type == 'deposit' else ('TRU' if tx_type == 'deduct' else 'HOAN')
                seq = self.env['ir.sequence'].next_by_code('customer.deposit.history')
                if not seq:
                    count = self.search_count([]) + 1
                    year = fields.Date.today().year
                    seq = f'{prefix}/{year}/{count:05d}'
                vals['name'] = seq
        records = super().create(vals_list)
        for record in records:
            if not record.balance_after:
                record.balance_after = record.partner_id.deposit_balance
        return records

    def action_post(self):
        """Xác nhận giao dịch nếu ở trạng thái dự thảo."""
        for tx in self:
            if tx.state != 'draft':
                continue
            tx.write({'state': 'posted', 'balance_after': tx.partner_id.deposit_balance})
        return True

    def action_cancel(self):
        """Hủy giao dịch."""
        for tx in self:
            if tx.order_id and tx.order_id.state == 'sale':
                raise UserError(_('Không thể hủy giao dịch trừ tiền khi đơn hàng %s vẫn đang có hiệu lực!') % tx.order_id.name)
            tx.write({'state': 'cancel'})
        return True
