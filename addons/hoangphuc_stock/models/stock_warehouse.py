from odoo import models, fields

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_explosive_warehouse = fields.Boolean(
        string='Kho Vật Liệu Nổ (VLNCN)',
        default=False,
        help='Đánh dấu kho lưu trữ vật liệu nổ công nghiệp tuân thủ giấy phép PCCC & An ninh trật tự.'
    )
    max_explosives_kg = fields.Float(
        string='Hạn Mức Thuốc Nổ Tối Đa (Kg)',
        default=0.0,
        help='Giới hạn khối lượng thuốc nổ được phép lưu trữ theo giấy phép.'
    )
    max_detonators_pcs = fields.Integer(
        string='Hạn Mức Kíp Nổ Tối Đa (Cái)',
        default=0,
        help='Giới hạn số lượng kíp nổ được phép lưu trữ theo giấy phép.'
    )
