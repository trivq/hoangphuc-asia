from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    quarry_customer_type = fields.Selection([
        ('prepaid', 'Trả Trước (Ký Quỹ Tiền Cọc)'),
        ('credit', 'Công Nợ (Có Hạn Mức Tín Dụng)')
    ], string='Chính Sách Bán Hàng Mỏ Đá', default='prepaid', tracking=True)

    deposit_balance = fields.Monetary(
        string='Số Dư Ký Quỹ (VNĐ)',
        currency_field='currency_id',
        compute='_compute_deposit_balance',
        store=True,
        tracking=True,
        help='Số tiền khách hàng nộp trước vào tài khoản để trừ dần khi xe ra trạm cân.'
    )
    deposit_history_ids = fields.One2many(
        'customer.deposit.history',
        'partner_id',
        string='Lịch Sử Ký Quỹ'
    )
    deposit_history_count = fields.Integer(
        string='Số Lượt Giao Dịch',
        compute='_compute_deposit_history_count'
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

    @api.depends('deposit_history_ids.amount', 'deposit_history_ids.transaction_type', 'deposit_history_ids.state')
    def _compute_deposit_balance(self):
        for partner in self:
            balance = 0.0
            for tx in partner.deposit_history_ids:
                if tx.state == 'posted':
                    if tx.transaction_type in ('deposit', 'refund'):
                        balance += tx.amount
                    elif tx.transaction_type == 'deduct':
                        balance -= tx.amount
            partner.deposit_balance = balance

    @api.depends('deposit_history_ids')
    def _compute_deposit_history_count(self):
        for partner in self:
            partner.deposit_history_count = len(partner.deposit_history_ids)

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
                current_debt = partner.credit or 0.0
                if partner.quarry_credit_limit > 0 and current_debt >= partner.quarry_credit_limit:
                    partner.credit_status = 'blocked'
                elif partner.quarry_credit_limit > 0 and current_debt >= (partner.quarry_credit_limit * 0.85):
                    partner.credit_status = 'warning'
                else:
                    partner.credit_status = 'good'

    def action_view_deposit_history(self):
        """Mở toàn bộ danh sách lịch sử nạp/trừ tiền ký quỹ của khách hàng."""
        self.ensure_one()
        return {
            'name': _('Lịch Sử Ký Quỹ - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'customer.deposit.history',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'default_transaction_type': 'deposit',
            }
        }

    def action_add_deposit(self):
        """Mở popup nạp tiền ký quỹ nhanh cho khách hàng."""
        self.ensure_one()
        return {
            'name': _('Nạp Tiền Ký Quỹ - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'customer.deposit.history',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_transaction_type': 'deposit',
                'default_payment_method': 'bank',
            }
        }
