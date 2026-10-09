from odoo import models, fields

class StockLot(models.Model):
    _inherit = 'stock.lot'

    mfg_date = fields.Date(
        string='Ngày Sản Xuất (NSX)',
        help='Ngày sản xuất lô vật liệu nổ công nghiệp.'
    )
    exp_date = fields.Date(
        string='Hạn Sử Dụng (HSD)',
        help='Hạn sử dụng ghi trên vỏ bao/hộp vật liệu nổ.'
    )
    manufacturer = fields.Char(
        string='Nhà Sản Xuất VLNCN',
        help='Ví dụ: Tổng công ty Kinh tế Kỹ thuật Công nghiệp Quốc phòng (GAET), Hóa chất mỏ, v.v.'
    )
    license_number = fields.Char(
        string='Số Giấy Phép / Đăng Kiểm VLNCN',
        help='Số giấy phép vận chuyển, lưu kho hoặc kiểm định kỹ thuật.'
    )
