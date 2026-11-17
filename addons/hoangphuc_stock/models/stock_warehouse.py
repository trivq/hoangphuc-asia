from odoo import models, fields, api

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    warehouse_type = fields.Selection([
        ('stone', 'Kho Đá / Thành Phẩm Mỏ (Trạm Cân)'),
        ('spare_parts', 'Kho Vật Tư - Phụ Tùng Thiết Bị'),
        ('explosives', 'Kho Vật Liệu Nổ Công Nghiệp (VLNCN)'),
        ('general', 'Kho Khác / Phổ Thông'),
    ], string='Phân Loại Kho Mỏ Đá', compute='_compute_warehouse_type', store=True, readonly=False,
       help='Xác định tính chất kho hàng để tự động phân luồng hiển thị cho các loại hoạt động xuất/nhập/điều chuyển.')

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

    @api.depends('is_explosive_warehouse', 'code', 'name')
    def _compute_warehouse_type(self):
        for wh in self:
            code = (wh.code or '').upper()
            name_lower = (wh.name or '').lower()
            if wh.is_explosive_warehouse or code == 'VLN' or 'vật liệu nổ' in name_lower or 'vlncn' in name_lower:
                wh.warehouse_type = 'explosives'
            elif code in ('KVT', 'VT') or 'vật tư' in name_lower or 'phụ tùng' in name_lower:
                wh.warehouse_type = 'spare_parts'
            elif code in ('WH', 'KTP', 'DA', 'MO') or 'thành phẩm' in name_lower or 'đá' in name_lower:
                wh.warehouse_type = 'stone'
            else:
                wh.warehouse_type = 'stone'
