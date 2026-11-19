from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mrp_production_id = fields.Many2one(
        'mrp.production',
        string='Lệnh Sản Xuất Nguồn (MO)',
        index=True,
        tracking=True,
        copy=False,
        help='Lệnh sản xuất mỏ đá liên quan đến chuyến hàng thành phẩm này.'
    )

class StockMove(models.Model):
    _inherit = 'stock.move'

    quarry_production_id = fields.Many2one(
        'mrp.production',
        string='Lệnh Sản Xuất Nguồn (MO)',
        related='picking_id.mrp_production_id',
        store=True,
        index=True,
        copy=False,
        help='Lệnh sản xuất liên quan qua phiếu chuyển hàng thành phẩm.'
    )

    scale_vehicle_plate = fields.Char(
        string='Biển Số Xe (BKS)',
        related='picking_id.vehicle_plate',
        store=True,
    )
    scale_driver_name = fields.Char(
        string='Tài Xế',
        related='picking_id.driver_name',
        store=True,
    )
    scale_weigh_time = fields.Datetime(
        string='Thời Gian Cân',
        related='picking_id.weigh_time',
        store=True,
    )
    scale_gross_weight = fields.Float(
        string='Khối Lượng Tổng (Kg)',
        related='picking_id.gross_weight',
        store=True,
    )
    scale_tare_weight = fields.Float(
        string='Khối Lượng Bì (Kg)',
        related='picking_id.tare_weight',
        store=True,
    )
    scale_net_weight = fields.Float(
        string='Khối Lượng Tịnh (Kg)',
        related='picking_id.net_weight',
        store=True,
    )
    scale_volume_m3 = fields.Float(
        string='Thể Tích (m³)',
        related='picking_id.volume_m3',
        store=True,
    )
