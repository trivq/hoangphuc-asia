{
    'name': 'Hoàng Phúc - Mua Hàng & Phê Duyệt Vật Tư Mỏ',
    'version': '1.0.0',
    'category': 'Purchases/Quarry',
    'summary': 'Gắn đích danh thiết bị chịu chi phí, quy tắc 3 báo giá, phân cấp duyệt <=20M TGĐ và >20M Chủ tịch HĐQT, nghiệm thu hiện trường',
    'description': """
Mở rộng Ứng dụng Mua Hàng (Purchase) cho Mỏ đá Hoàng Phúc:
==========================================================
1. Gắn Đích Danh Thiết Bị Chịu Chi Phí (purchase.order):
   - Bắt buộc gắn đích danh xe/máy móc/trạm nghiền chịu chi phí phụ tùng (BR-10).
2. Quy Tắc So Sánh 3 Báo Giá Cạnh Tranh (BR-02, BR-04):
   - Nhập thông tin so sánh 3 nhà cung cấp hoặc giải trình bắt buộc khi chỉ định 1 nguồn.
3. Phân Cấp Phê Duyệt Tài Chính (BR-03):
   - Đơn hàng <= 20.000.000 VNĐ: TGĐ phê duyệt hoàn tất.
   - Đơn hàng > 20.000.000 VNĐ: TGĐ rà soát -> Chủ tịch HĐQT phê duyệt cuối cùng.
4. Nghiệm Thu Thực Tế Kèm Ảnh Hiện Trường (BR-05):
   - Nghiệm thu bàn giao trực tiếp tại moong mỏ hoặc xưởng kèm hình ảnh hiện trường.
5. Quản Lý Chính Sách Công Nợ NCC Đặc Thù (BR-08):
   - Ghi nhận chính sách nợ 1 tháng (Túy Hoài, Đức Soạn, Tiến Lốp) hoặc theo đơn.
    """,
    'author': 'Hoang Phuc Mining Solution',
    'website': 'https://hoangphucstone.vn',
    'depends': ['base', 'purchase', 'maintenance'],
    'data': [
        'data/ir_config_parameter_data.xml',
        'views/purchase_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
