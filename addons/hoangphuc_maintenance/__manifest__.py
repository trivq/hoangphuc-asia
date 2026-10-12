{
    'name': 'Hoàng Phúc - Thiết Bị & Bảo Trì Cơ Giới Mỏ (Sóng 2)',
    'version': '20.0.1.0.0',
    'category': 'Manufacturing/Maintenance',
    'summary': 'Định mức nhiên liệu, dừng máy >=10 phút, nghiệm thu 3 bên, đối soát tiêu hao dầu cảnh báo >10%',
    'description': """
Mở rộng Ứng dụng Bảo Trì (Maintenance) cho Mỏ đá Hoàng Phúc:
=============================================================
1. Hồ Sơ Máy Móc & Thiết Bị Cơ Giới Mỏ (maintenance.equipment):
   - Biển số/số hiệu máy, phân loại máy mỏ (máy xúc, xe ben, trạm nghiền, máy khoan).
   - Định mức tiêu hao nhiên liệu chuẩn (Lít/giờ hoặc Lít/100km).
   - Quản lý trạng thái an toàn đầu ca (Khóa máy nếu phát hiện lỗi nguy hiểm - BR-02).
2. Phân Loại & Nghiệm Thu Phiếu Sửa Chữa (maintenance.request):
   - Phân biệt Bảo dưỡng định kỳ vs Sửa chữa đột xuất (BR-10).
   - Theo dõi thời gian dừng máy (Downtime >= 10 phút bắt buộc giải trình - BR-04).
   - Nghiệm thu 3 bên (Lái xe, Thợ sửa chữa, Quản đốc mỏ) trước khi mở khóa máy (BR-07).
3. Nhật Ký Cấp Dầu & Đối Soát Tiêu Hao Nhiên Liệu (hoangphuc.fuel.log):
   - Tính toán mức tiêu hao thực tế (L/h) so với định mức chuẩn.
   - Cảnh báo đỏ nếu chênh lệch vượt quá 10% (BR-08) và bắt buộc giải trình kỹ thuật.
    """,
    'author': 'Tri Vo - Paracel',
    'website': 'https://hoangphucstone.vn',
    'depends': ['base', 'maintenance'],
    'data': [
        'security/ir.access.csv',
        'views/maintenance_equipment_views.xml',
        'views/maintenance_request_views.xml',
        'views/fuel_log_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
