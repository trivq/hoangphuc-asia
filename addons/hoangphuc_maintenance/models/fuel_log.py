from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HoangPhucFuelLog(models.Model):
    _name = 'hoangphuc.fuel.log'
    _description = 'Nhật Ký Cấp Dầu & Đối Soát Tiêu Hao Nhiên Liệu Mỏ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'log_date desc, id desc'

    name = fields.Char(
        string='Mã Phiếu Cấp Dầu',
        default='Mới',
        copy=False,
        readonly=True
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Thiết Bị / Xe Cơ Giới Mỏ',
        required=True,
        tracking=True
    )
    log_date = fields.Date(
        string='Ngày Cấp Dầu',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    previous_meter = fields.Float(
        string='Chỉ Số Cũ (Giờ/Km)',
        digits=(12, 1),
        default=0.0,
        tracking=True
    )
    current_meter = fields.Float(
        string='Chỉ Số Mới (Giờ/Km)',
        digits=(12, 1),
        default=0.0,
        tracking=True
    )
    operating_units = fields.Float(
        string='Giờ/Km Hoạt Động',
        digits=(12, 1),
        compute='_compute_fuel_stats',
        store=True,
        tracking=True
    )
    fuel_liters = fields.Float(
        string='Lượng Dầu Cấp Thực Tế (Lít)',
        digits=(12, 2),
        default=0.0,
        required=True,
        tracking=True
    )
    standard_fuel_rate = fields.Float(
        related='equipment_id.standard_fuel_rate',
        string='Định Mức Chuẩn (L/h)',
        readonly=True
    )
    actual_fuel_rate = fields.Float(
        string='Tiêu Hao Thực Tế (L/h)',
        digits=(10, 2),
        compute='_compute_fuel_stats',
        store=True,
        tracking=True
    )
    variance_percent = fields.Float(
        string='Chênh Lệch Định Mức (%)',
        digits=(10, 1),
        compute='_compute_fuel_stats',
        store=True,
        tracking=True
    )
    is_over_limit = fields.Boolean(
        string='Cảnh Báo Vượt > 10% (BR-08)',
        compute='_compute_fuel_stats',
        store=True,
        tracking=True
    )
    technical_explanation = fields.Text(
        string='Giải Trình Kỹ Thuật Tiêu Hao Dầu',
        tracking=True,
        help='Bắt buộc giải trình nếu tiêu hao vượt quá 10% so với định mức mỏ (BR-08).'
    )
    fuel_station = fields.Char(
        string='Cột Bơm / Téc Dầu',
        default='Téc Dầu Kho Mỏ Núi Dài'
    )
    driver_name = fields.Char(string='Lái Máy Nhận Dầu')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Mới') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('hoangphuc.fuel.log') or _('PCD-%s') % fields.Date.today()
        return super().create(vals_list)

    @api.depends('previous_meter', 'current_meter', 'fuel_liters', 'equipment_id.standard_fuel_rate')
    def _compute_fuel_stats(self):
        for log in self:
            op_units = 0.0
            if log.current_meter > log.previous_meter:
                op_units = log.current_meter - log.previous_meter
            log.operating_units = op_units

            actual_rate = 0.0
            if op_units > 0 and log.fuel_liters > 0:
                actual_rate = round(log.fuel_liters / op_units, 2)
            log.actual_fuel_rate = actual_rate

            std_rate = log.standard_fuel_rate or 0.0
            variance = 0.0
            over_limit = False
            if std_rate > 0 and actual_rate > 0:
                variance = round(((actual_rate - std_rate) / std_rate) * 100.0, 1)
                if variance > 10.0:
                    over_limit = True
            log.variance_percent = variance
            log.is_over_limit = over_limit

    @api.constrains('is_over_limit', 'technical_explanation')
    def _check_fuel_variance(self):
        for log in self:
            if log.is_over_limit and not (log.technical_explanation or '').strip():
                raise UserError(_('CẢNH BÁO BR-08: Lượng dầu tiêu hao thực tế vượt quá định mức %s%% (> 10%%)!\nBắt buộc phải nhập Giải trình kỹ thuật trước khi lưu.') % log.variance_percent)
