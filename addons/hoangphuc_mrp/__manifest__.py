{
    'name': 'Hoàng Phúc - Quản Lý Sản Xuất & Trạm Nghiền Sàng',
    'version': '1.0.0',
    'category': 'Manufacturing/Quarry',
    'summary': 'Quản lý lệnh sản xuất mỏ đá, trạm nghiền, ca kíp, cấp liệu moong mỏ, kiểm tra an toàn đầu ca (BR-02) và dừng máy (BR-04)',
    'description': """
Mở rộng Ứng dụng Sản Xuất (Manufacturing / MRP) cho Mỏ đá Hoàng Phúc:
=====================================================================
Căn cứ theo Biểu mẫu quy trình Sản xuất trực tiếp mỏ đá (SXTT):
1. Điều Hành Trạm Nghiền Sàng Mỏ Đá (mrp.production):
   - Trạm nghiền sàng (Trạm 1 - 250 T/h, Trạm 2 - 150 T/h).
   - Ca sản xuất (Ca 1, Ca 2, Ca 3) và người vận hành trạm.
2. Kiểm Tra Điều Kiện & An Toàn Đầu Ca (BR-02):
   - Đạt an toàn đầu ca trước khi cho phép vận hành trạm nghiền.
   - Chặn chạy lệnh sản xuất nếu mất an toàn hoặc sự cố chưa khắc phục.
3. Cấp Liệu Đá Nguyên Khai Moong Mỏ (Luồng 4B):
   - Khối lượng đá thô cấp vào phễu nghiền (Tấn), số chuyến xe ben Howo.
   - Nút "Áp Khối Lượng Cấp Liệu" tự động cập nhật nguyên liệu tiêu hao.
4. Theo Dõi Vận Hành & Dừng Máy Trạm Nghiền (BR-04 Downtime):
   - Giờ chạy thực tế, thời gian dừng máy (phút), mã nguyên nhân dừng máy (tắc phễu, mất điện, thời tiết).
   - Bắt buộc giải trình kỹ thuật nếu thời gian dừng máy >= 10 phút.
5. Bàn Giao Nhập Kho Bãi Thành Phẩm (Luồng 4.5):
   - Chỉ định bãi tập kết đá thành phẩm (Đá 1x2, Đá 4x6, Đá Base).
    """,
    'author': 'Tri Vo - Paracel',
    'website': 'https://hoangphucstone.vn',
    'depends': ['base', 'mrp', 'hoangphuc_stock'],
    'data': [
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
