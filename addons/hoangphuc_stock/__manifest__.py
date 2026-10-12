{
    'name': 'Hoàng Phúc - Quản Lý Kho & Trạm Cân Mỏ Đá (Sóng 1)',
    'version': '1.0.0',
    'category': 'Inventory/Quarry',
    'summary': 'Tích hợp Trạm cân xe vào Stock Picking, quy đổi tỷ trọng Tấn/m3, quản lý kho VLNCN và cấp phát vật tư',
    'description': """
Mở rộng Ứng dụng Kho (Inventory / Stock) cho Mỏ đá Hoàng Phúc:
=============================================================
1. Tích hợp Trạm Cân Xe trực tiếp trên Phiếu Xuất/Nhập Kho (stock.picking):
   - Biển số xe, tài xế, khối lượng bì, khối lượng tổng, tự động tính khối lượng tịnh.
   - Lấy tỷ trọng riêng của từng loại đá để quy đổi ra thể tích m3.
   - Tự động cập nhật khối lượng tịnh hoặc m3 vào dòng chi tiết phiếu kho.
   - In Phiếu Cân Điện Tử song ngữ trực tiếp từ phiếu kho.
2. Quản lý Kho & Lô Vật Liệu Nổ Công Nghiệp (VLNCN):
   - Hạn mức lưu kho an toàn (kg thuốc nổ, kíp nổ) trên stock.warehouse.
   - Quản lý Lô VLNCN (stock.lot): Ngày sản xuất, hạn sử dụng, nhà sản xuất, giấy phép.
   - Phiếu xuất kho VLNCN theo mã hộ chiếu nổ mìn và chỉ huy nổ mìn.
3. Xuất kho vật tư, phụ tùng thay thế:
   - Gắn đích danh thiết bị mỏ chịu chi phí (equipment_id).
    """,
    'author': 'Tri Vo - Paracel',
    'website': 'https://hoangphucstone.vn',
    'depends': ['base', 'stock', 'product'],
    'data': [
        'views/stock_picking_views.xml',
        'views/product_views.xml',
        'views/stock_lot_views.xml',
        'views/stock_warehouse_views.xml',
        'report/scale_ticket_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
