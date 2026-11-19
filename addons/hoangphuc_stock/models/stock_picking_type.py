from odoo import models, fields, api

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    picking_category = fields.Selection([
        ('stone', 'Đá Thành Phẩm (Trạm Cân)'),
        ('spare_parts', 'Vật Tư - Phụ Tùng Thiết Bị'),
        ('explosives', 'Vật Liệu Nổ Công Nghiệp (VLNCN)'),
        ('general', 'Khác / Tiêu Chuẩn'),
    ], string='Phân Loại Nghiệp Vụ Kho', compute='_compute_picking_category', store=True, readonly=False,
       help='Quy định loại tab hiển thị trên phiếu kho (Trạm cân, Phụ tùng, VLNCN...)')

    @api.depends('warehouse_id', 'warehouse_id.warehouse_type', 'warehouse_id.code', 'warehouse_id.name', 'warehouse_id.is_explosive_warehouse', 'code', 'name')
    def _compute_picking_category(self):
        for ptype in self:
            wh = ptype.warehouse_id
            name_lower = (ptype.name or '').lower()
            wh_name_lower = (wh.name or '').lower() if wh else ''
            wh_code = (wh.code or '').upper() if wh else ''

            if wh and getattr(wh, 'warehouse_type', False):
                ptype.picking_category = wh.warehouse_type
            elif (wh and wh.is_explosive_warehouse) or wh_code == 'VLN' or 'vật liệu nổ' in wh_name_lower or 'vlncn' in wh_name_lower or 'nổ mìn' in name_lower:
                ptype.picking_category = 'explosives'
            elif wh_code in ('KVT', 'VT') or 'vật tư' in wh_name_lower or 'phụ tùng' in wh_name_lower or 'phụ tùng' in name_lower or 'vật tư' in name_lower:
                ptype.picking_category = 'spare_parts'
            elif wh_code in ('WH', 'KTP', 'DA', 'MO') or 'thành phẩm' in wh_name_lower or 'mỏ đá' in wh_name_lower or 'đá' in wh_name_lower or 'cân' in name_lower:
                ptype.picking_category = 'stone'
            else:
                ptype.picking_category = 'stone'
