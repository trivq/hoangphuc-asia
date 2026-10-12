{
    'name': 'Hoàng Phúc - Bán Hàng & Hạn Mức Công Nợ Mỏ Đá (Sóng 2)',
    'version': '20.0.1.0.0',
    'category': 'Sales/Quarry',
    'summary': 'Tích hợp Hợp đồng đá mỏ, theo dõi dự án công trình, kiểm soát hạn mức nợ và ký quỹ thời gian thực',
    'description': """
Mở rộng Ứng dụng Bán Hàng (Sale) cho Mỏ đá Hoàng Phúc:
======================================================
1. Quản lý Hợp đồng Bán Đá & Dự án Công trình (sale.order):
   - Tên công trình/dự án tiếp nhận đá (Cao tốc, Cầu đường, Trạm trộn...).
   - Số hợp đồng mỏ đá.
   - Quy cách bán: theo Tấn (trọng lượng) hoặc theo Mét khối (thể tích m3).
2. Kiểm soát Hạn Mức Tín Dụng & Tiền Gửi Ký Quỹ (res.partner & sale.order):
   - Phân loại khách hàng: Trả trước (Ký quỹ tiền cọc) vs Công nợ có hạn mức.
   - Quản lý số dư tiền cọc ký quỹ (deposit_balance).
   - Quản lý hạn mức tín dụng tối đa (quarry_credit_limit).
   - Tự động hiển thị trạng thái tín dụng và cảnh báo khi khách hàng không đủ điều kiện xuất hàng.
    """,
    'author': 'Tri Vo - Paracel',
    'website': 'https://hoangphucstone.vn',
    'depends': ['base', 'sale', 'hoangphuc_stock'],
    'data': [
        'views/partner_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
