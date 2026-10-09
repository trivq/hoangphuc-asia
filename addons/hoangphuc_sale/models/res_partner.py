from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    quarry_customer_type = fields.Selection([
        ('prepaid', 'Trả Trước (Ký Quỹ Tiền Cọc)'),
        ('credit', 'Công Nợ (Có Hạn Mức Tín Dụng)')
    ], string='Chính Sách Bán Hàng Mỏ Đá', default='prepaid', tracking=True)

    deposit_balance = fields.Monetary(
        string='Số Dư Ký Quỹ (VNĐ)',
        currency_field='currency_id',
        default=0.0,
        tracking=True,
        help='Số tiền khách hàng nộp trước vào tài khoản để trừ dần khi xe ra trạm cân.'
    )
    quarry_credit_limit = fields.Monetary(
        string='Hạn Mức Nợ Tối Đa (VNĐ)',
        currency_field='currency_id',
        default=0.0,
        tracking=True,
        help='Hạn mức tín dụng tối đa cho phép khách hàng nợ tiền lấy đá.'
    )
    quarry_payment_term_days = fields.Integer(
        string='Thời Hạn Nợ (Ngày)',
        default=30,
        help='Số ngày được phép chậm thanh toán (thường 15 hoặc 30 ngày).'
    )
    credit_status = fields.Selection([
        ('good', 'Tốt / Đủ Điều Kiện Xuất Đá'),
        ('warning', 'Cảnh Báo (Số Dư Thấp)'),
        ('blocked', 'Khóa Xuất Hàng (Hết Tiền / Vượt Hạn Mức)')
    ], string='Trạng Thái Tín Dụng Mỏ', compute='_compute_quarry_credit_status', store=False)

    @api.depends('quarry_customer_type', 'deposit_balance', 'quarry_credit_limit', 'credit')
    def _compute_quarry_credit_status(self):
        for partner in self:
            if partner.quarry_customer_type == 'prepaid':
                if partner.deposit_balance <= 0:
                    partner.credit_status = 'blocked'
                elif partner.deposit_balance < 10_000_000:
                    partner.credit_status = 'warning'
                else:
                    partner.credit_status = 'good'
            else:
                # credit limit
                current_debt = partner.credit or 0.0
                if partner.quarry_credit_limit > 0 and current_debt >= partner.quarry_credit_limit:
                    partner.credit_status = 'blocked'
                elif partner.quarry_credit_limit > 0 and current_debt >= (partner.quarry_credit_limit * 0.85):
                    partner.credit_status = 'warning'
                else:
                    partner.credit_status = 'good'
