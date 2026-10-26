from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        related='company_id.currency_id',
        readonly=True
    )
    is_deposit_deducted = fields.Boolean(
        string='Đã Trừ Tiền Ký Quỹ',
        default=False,
        copy=False,
        tracking=True,
        help='Đánh dấu phiếu xuất kho này đã trừ tiền vào số dư ký quỹ của khách hàng.'
    )
    deducted_deposit_amount = fields.Monetary(
        string='Số Tiền Cọc Đã Trừ (VNĐ)',
        currency_field='currency_id',
        default=0.0,
        copy=False,
        tracking=True,
        help='Giá trị thực tế đã trừ vào số dư tiền cọc của khách hàng khi xe qua trạm cân.'
    )
    partner_quarry_type = fields.Selection(
        related='partner_id.quarry_customer_type',
        string='Chính Sách Bán Hàng Mỏ',
        readonly=True
    )
    partner_deposit_balance = fields.Monetary(
        related='partner_id.deposit_balance',
        currency_field='currency_id',
        string='Số Dư Ký Quỹ Của Khách (VNĐ)',
        readonly=True
    )

    def _calculate_picking_total_amount(self):
        """Tính tổng giá trị tiền hàng của phiếu xuất đá qua trạm cân."""
        self.ensure_one()
        total = 0.0
        for move in self.move_ids.filtered(lambda m: m.state != 'cancel'):
            qty = move.quantity if move.state == 'done' else (move.quantity or move.product_uom_qty or 0.0)
            if qty <= 0:
                continue

            sale_line = move.sale_line_id if 'sale_line_id' in move._fields else False
            if sale_line:
                price_unit = sale_line.price_unit
                taxes = getattr(sale_line, 'tax_ids', False) or getattr(sale_line, 'tax_id', False)
                if taxes:
                    tax_res = taxes.compute_all(
                        price_unit,
                        currency=sale_line.currency_id or self.company_id.currency_id,
                        quantity=qty,
                        product=move.product_id,
                        partner=self.partner_id
                    )
                    total += tax_res['total_included']
                else:
                    discount_factor = 1.0 - (sale_line.discount or 0.0) / 100.0
                    total += qty * price_unit * discount_factor
            else:
                price_unit = move.product_id.list_price or 0.0
                total += qty * price_unit
        return total

    def button_validate(self):
        """Kiểm tra số dư ký quỹ trước khi cho phép trạm cân xuất bến (BR-01 / BR-02)."""
        for picking in self:
            if picking.picking_type_id.code == 'outgoing' and picking.partner_id.quarry_customer_type == 'prepaid' and not picking.is_deposit_deducted:
                total_amount = picking._calculate_picking_total_amount()
                if total_amount > 0 and picking.partner_id.deposit_balance < total_amount:
                    raise UserError(_(
                        'CẢNH BÁO TÍN DỤNG (BR-01): Số dư tiền ký quỹ của khách hàng "%s" không đủ để xuất xe đá này!\n\n'
                        '• Tổng giá trị xe hàng: %s VNĐ\n'
                        '• Số dư ký quỹ hiện tại: %s VNĐ\n'
                        '• Số tiền còn thiếu: %s VNĐ\n\n'
                        'Trạm cân không được phép xuất vé cho xe ra cổng. Vui lòng yêu cầu khách hàng nộp thêm tiền cọc!'
                    ) % (
                        picking.partner_id.name,
                        '{:,.0f}'.format(total_amount),
                        '{:,.0f}'.format(picking.partner_id.deposit_balance),
                        '{:,.0f}'.format(total_amount - picking.partner_id.deposit_balance)
                    ))
        return super().button_validate()

    def _action_done(self):
        """Tự động trừ tiền ký quỹ của khách hàng ngay khi hoàn tất cân xe xuất kho."""
        res = super()._action_done()
        for picking in self:
            if picking.picking_type_id.code == 'outgoing' and picking.partner_id.quarry_customer_type == 'prepaid' and not picking.is_deposit_deducted:
                total_amount = picking._calculate_picking_total_amount()
                if total_amount > 0:
                    old_balance = picking.partner_id.deposit_balance
                    new_balance = old_balance - total_amount
                    picking.partner_id.deposit_balance = new_balance
                    picking.is_deposit_deducted = True
                    picking.deducted_deposit_amount = total_amount
                    msg = _(
                        '<b>[TRẠM CÂN MỎ ĐÁ - TRỪ TIỀN KÝ QUỸ]</b><br/>'
                        '• Khách hàng: %s (Trả trước)<br/>'
                        '• Biển số xe: %s<br/>'
                        '• Giá trị xe đá xuất bến: <b>%s VNĐ</b><br/>'
                        '• Số dư cọc trước khi trừ: %s VNĐ<br/>'
                        '• Số dư cọc còn lại: <b>%s VNĐ</b>'
                    ) % (
                        picking.partner_id.name,
                        picking.vehicle_plate or 'N/A',
                        '{:,.0f}'.format(total_amount),
                        '{:,.0f}'.format(old_balance),
                        '{:,.0f}'.format(new_balance)
                    )
                    picking.message_post(body=msg)
                    picking.partner_id.message_post(body=msg)
        return res
