from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    density = fields.Float(
        string='Tỷ Trọng Đá (Tấn/m³)',
        digits=(12, 3),
        default=1.600,
        help='Tỷ trọng riêng dùng để quy đổi khối lượng cân sang thể tích mét khối (m3).'
    )
    is_quarry_stone = fields.Boolean(
        string='Sản Phẩm Đá Mỏ',
        default=False,
        help='Đánh dấu sản phẩm là đá khai thác hoặc đá thành phẩm qua trạm cân.'
    )
    is_explosive = fields.Boolean(
        string='Vật Liệu Nổ CN (VLNCN)',
        default=False,
        help='Đánh dấu hàng hóa là thuốc nổ, kíp nổ hoặc phụ kiện nổ mìn.'
    )
    is_quarry_spare_part = fields.Boolean(
        string='Phụ Tùng Cơ Giới Mỏ',
        default=False,
        help='Đánh dấu là vật tư, phụ tùng thay thế cho máy móc thiết bị mỏ.'
    )
