from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError


class MrpProductionDowntime(models.Model):
    _name = 'mrp.production.downtime'
    _description = 'Nhật Ký Dừng Máy Trạm Nghiền (BR-04 Downtime)'
    _order = 'date_start desc, id desc'

    production_id = fields.Many2one(
        'mrp.production',
        string='Lệnh Sản Xuất',
        required=True,
        ondelete='cascade',
        index=True
    )
    date_start = fields.Datetime(
        string='Thời Gian Bắt Đầu',
        default=fields.Datetime.now,
        required=True
    )
    date_end = fields.Datetime(
        string='Thời Gian Kết Thúc'
    )
    duration_minutes = fields.Integer(
        string='Thời Lượng (Phút)',
        compute='_compute_duration_minutes',
        store=True,
        readonly=False,
        help='Thời gian dừng máy tính bằng phút. Tự động tính khi có giờ kết thúc hoặc nhập trực tiếp.'
    )
    cause = fields.Selection([
        ('jam', 'Tắc Phễu / Kẹt Đá Quá Cỡ'),
        ('electrical', 'Sự Cố Điện / Mất Điện Lưới'),
        ('mechanical', 'Sự Cố Cơ Khí / Rách Băng Tải / Kẹt Sàng'),
        ('weather', 'Mưa Lớn / Thời Tiết Mất An Toàn'),
        ('maintenance', 'Bảo Dưỡng Định Kỳ Đầu Ca'),
        ('other', 'Nguyên Nhân Khác'),
    ], string='Nguyên Nhân Dừng Máy', required=True, default='jam')

    explanation = fields.Text(
        string='Giải Trình Kỹ Thuật (BR-04)',
        help='Bắt buộc nhập giải trình kỹ thuật nếu thời gian dừng máy >= 10 phút (BR-04).'
    )

    @api.depends('date_start', 'date_end')
    def _compute_duration_minutes(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                diff = rec.date_end - rec.date_start
                rec.duration_minutes = max(0, int(diff.total_seconds() / 60))
            elif not rec.duration_minutes:
                rec.duration_minutes = 0

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise UserError(_('Thời gian kết thúc dừng máy không thể trước thời gian bắt đầu!'))
