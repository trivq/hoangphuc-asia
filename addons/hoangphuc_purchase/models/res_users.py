from odoo import models, fields, api


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

    @api.model
    def _sync_approval_filter_users(self):
        """Đồng bộ danh sách người dùng được gán bộ lọc mặc định 'Cần Phê Duyệt'."""
        filter_ref = self.env.ref('hoangphuc_purchase.filter_po_need_my_approval_default', raise_if_not_found=False)
        if not filter_ref:
            return
        approvers = self.sudo().search([
            '|', ('is_general_manager', '=', True), ('is_board_chairman', '=', True)
        ])
        filter_ref.sudo().write({'user_ids': [(6, 0, approvers.ids)]})

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        if any('is_general_manager' in v or 'is_board_chairman' in v for v in vals_list):
            self._sync_approval_filter_users()
        return users

    def write(self, vals):
        res = super().write(vals)
        if 'is_general_manager' in vals or 'is_board_chairman' in vals:
            self._sync_approval_filter_users()
        return res
