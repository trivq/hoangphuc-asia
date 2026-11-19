from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_general_manager = fields.Boolean(
        string='Là Tổng Giám Đốc (TGĐ)',
        help='Người dùng này có thẩm quyền Tổng Giám Đốc để phê duyệt các đơn mua sắm đến hạn mức quy định (mặc định <= 20 triệu VNĐ).'
    )
    is_board_chairman = fields.Boolean(
        string='Là Chủ Tịch HĐQT',
        help='Người dùng này có thẩm quyền Chủ Tịch HĐQT để phê duyệt tối cao các đơn mua sắm vượt hạn mức TGĐ (> 20 triệu VNĐ).'
    )
