from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    po_tier_approval_limit = fields.Float(
        string='Hạn Mức Duyệt Mua Hàng Cấp 1 (TGĐ)',
        config_parameter='hoangphuc_purchase.purchase_approval_limit',
        default=20000000.0,
        help='Hạn mức mua hàng tối đa để Tổng Giám Đốc phê duyệt hoàn tất (BR-03). '
             'Đơn hàng có tổng tiền vượt quá hạn mức này sẽ phải trình Chủ Tịch HĐQT phê duyệt.'
    )

    def set_values(self):
        super().set_values()
        # Tự động tính toán lại phân cấp phê duyệt cho các đơn hàng chưa chốt duyệt
        pending_orders = self.env['purchase.order'].search([
            ('approval_state', 'in', ['draft', 'waiting_gm', 'waiting_chairman'])
        ])
        if pending_orders:
            pending_orders._compute_approval_tier()
