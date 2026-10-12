# HƯỚNG DẪN TRIỂN KHAI VÀ KỊCH BẢN DEMO ODOO 19 ENTERPRISE (EE)
## BỘ MODULE CUSTOM MỞ RỘNG ỨNG DỤNG ODOO CHUẨN CHO MỎ ĐÁ HOÀNG PHÚC
### (ƯU TIÊN SÓNG 1 VÀ SÓNG 2 THEO TẬP TÀI LIỆU QUY TRÌNH NGHIỆP VỤ)

Tài liệu này hướng dẫn chi tiết cách vận hành và demo bộ giải pháp Odoo 19 Enterprise (EE) cho Ban Lãnh Đạo Công ty Cổ phần Khai Thác & Chế Biến Đá Hoàng Phúc dựa trên [Tập Tài Liệu Thu Thập Quy Trình Nghiệp Vụ](file:///home/ubuntu/source/HoangPhuc/Tap_Tai_Lieu_Quy_Trinh.md) và tuân thủ nguyên tắc [CLAUDE.md](file:///home/ubuntu/source/HoangPhuc/CLAUDE.md) (kế thừa trực tiếp ứng dụng tiêu chuẩn của Odoo, không viết ứng dụng tách rời độc lập).

---

## I. MÔI TRƯỜNG VẬN HÀNH & KIẾN TRÚC HỆ THỐNG

### 1. Môi trường triển khai:
- **Môi trường Odoo 20 Community Edition (CE) (Docker Compose tại thư mục HoangPhuc)**:
  - **Thư mục cài đặt**: `/home/ubuntu/source/HoangPhuc`
  - **Địa chỉ truy cập Web**: [http://localhost:10017](http://localhost:10017)
  - **Tên cơ sở dữ liệu**: `hoangphuc_db`
  - **Tài khoản đăng nhập**: `admin` / `admin`
  - **Lệnh khởi động**: `docker compose up -d`
  - **Lệnh nạp dữ liệu demo**:
    ```bash
    docker compose exec -T web odoo shell -d hoangphuc_db --no-http << 'EOF'
    with open('/mnt/extra-addons/hoangphuc_stock/populate_demo_data.py') as f:
        exec(f.read())
    populate_demo_data(env.cr)
    env.cr.commit()
    EOF
    ```

- **Môi trường Odoo 19 Enterprise (EE) (Setup tại odoo19-docker-setup)**:
  - **Thư mục cài đặt**: `/home/ubuntu/source/odoo19-docker-setup`
  - **Địa chỉ truy cập Web**: [http://localhost:10020](http://localhost:10020)
  - **Tên cơ sở dữ liệu**: `ok` (Odoo 19 Enterprise)
  - **Tài khoản đăng nhập**: `admin` / `admin`

### 2. Kiến trúc Module Custom (Kế thừa trực tiếp Odoo Standard):
Hệ thống không tạo các bảng hay menu độc lập dư thừa mà **mở rộng trực tiếp các module nghiệp vụ cốt lõi của Odoo 19**:

```
/home/ubuntu/source/HoangPhuc/addons/
├── hoangphuc_stock/          # Kế thừa Inventory (stock.picking, product.template, stock.lot, stock.warehouse)
│                              # -> Trạm cân xe, tỷ trọng tấn/m3, kho VLNCN, cấp phát phụ tùng, in phiếu cân
├── hoangphuc_sale/           # Kế thừa Sales (sale.order, res.partner)
│                              # -> Hợp đồng đá, dự án công trình, kiểm soát hạn mức nợ & ký quỹ thời gian thực
├── hoangphuc_purchase/       # Kế thừa Purchases (purchase.order)
│                              # -> Gắn xe máy (BR-10), quy tắc 3 báo giá (BR-02), duyệt <=20M và >20M (BR-03), nghiệm thu hiện trường (BR-05)
└── hoangphuc_maintenance/    # Kế thừa Maintenance (maintenance.equipment, maintenance.request, hoangphuc.fuel.log)
                               # -> Định mức dầu L/h, dừng máy >=10 phút (BR-04), nghiệm thu 3 bên (BR-07), đối soát dầu cảnh báo >10% (BR-08)
```

---

## II. MA TRẬN ĐÁP ỨNG QUY TRÌNH & BUSINESS RULES (SÓNG 1 & SÓNG 2)

| Sóng | Quy trình nghiệp vụ trong tài liệu | Ứng dụng Odoo chuẩn kế thừa | Tính năng & Business Rules đáp ứng |
| :--- | :--- | :--- | :--- |
| **Sóng 1** | **1. Xuất kho thành phẩm** | **Inventory** (`stock.picking`) | • Tích hợp Tab **Trạm Cân Mỏ Đá**: Cân bì, cân tổng, tự động tính khối lượng tịnh (`net_weight`).<br>• Tự động quy đổi khối lượng sang thể tích $m^3$ theo tỷ trọng riêng từng loại đá.<br>• Nút **"Áp Khối Lượng Cân"**: Tự động điền số lượng tịnh vào chi tiết phiếu xuất kho.<br>• Nút **"In Phiếu Cân"**: In trực tiếp Phiếu Cân Xe Điện Tử song ngữ chuẩn mỏ.<br>• Kiểm tra số dư ký quỹ / hạn mức nợ của khách hàng ngay trên phiếu kho. |
| **Sóng 1** | **2. Nhập kho thành phẩm & Cấp liệu đá thô** | **Inventory** (`stock.picking`) | • Cân xe đá nguyên khai từ moong mỏ vào các trạm nghiền sàng (Trạm 1, Trạm 2).<br>• Ghi nhận số chuyến xe, phân loại đá thô và theo dõi sản lượng cấp liệu. |
| **Sóng 1** | **3. Quản lý kho vật tư phụ tùng** | **Inventory** (`stock.picking`) | • Phiếu xuất kho phụ tùng bắt buộc gắn đích danh thiết bị / xe máy mỏ (`equipment_id`) theo **BR-10**. |
| **Sóng 1** | **4. Quản lý kho vật liệu nổ (VLNCN)** | **Inventory** (`stock.lot`, `stock.warehouse`) | • Khai báo hạn mức lưu trữ tối đa (kg thuốc nổ, kíp nổ) trên Kho mỏ.<br>• Quản lý Lô VLNCN: Ngày sản xuất, Hạn sử dụng, Nhà máy sản xuất (GAET, MICCO), Số giấy phép.<br>• Phiếu xuất kho VLNCN gắn Mã hộ chiếu nổ mìn và Chỉ huy nổ mìn chịu trách nhiệm. |
| **Sóng 2** | **5. Bán hàng & Thu hồi Công nợ** | **Sales** (`sale.order`, `res.partner`) | • Khai báo Hợp đồng đá mỏ: Gắn tên Dự án/Công trình (Cao tốc, Cầu đường), Quy cách tính giá (Tấn hoặc $m^3$).<br>• Hồ sơ Khách hàng (`res.partner`): Phân loại Trả trước (Ký quỹ tiền cọc) vs Công nợ có hạn mức.<br>• Cảnh báo thời gian thực: Tự động cảnh báo đỏ/vàng trên Đơn hàng nếu khách chưa nộp tiền cọc hoặc vượt hạn mức nợ. |
| **Sóng 2** | **6. Mua hàng & Phê duyệt vật tư** | **Purchases** (`purchase.order`) | • **BR-10**: Bắt buộc gắn đích danh xe/máy xúc/trạm nghiền chịu chi phí.<br>• **BR-02, BR-04**: Bắt buộc nhập thông tin so sánh 3 báo giá cạnh tranh; giải trình văn bản nếu mua 1 nguồn duy nhất.<br>• **BR-03**: Phân cấp phê duyệt thẩm quyền tài chính:<br>  * Đơn hàng <= 20.000.000 VNĐ: TGĐ phê duyệt.<br>  * Đơn hàng > 20.000.000 VNĐ: TGĐ kiểm tra -> Chủ tịch HĐQT phê duyệt cuối cùng.<br>• **BR-05**: Nghiệm thu thực tế và đính kèm ảnh hiện trường tại moong mỏ hoặc xưởng.<br>• **BR-08**: Quản lý chính sách công nợ NCC đặc thù (Túy Hoài, Đức Soạn, Tiến Lốp nợ 1 tháng). |
| **Sóng 2** | **7. Quản lý Máy móc, Thiết bị & Bảo trì** | **Maintenance** (`maintenance.equipment`, `maintenance.request`) | • Hồ sơ Thiết bị: Biển số/số hiệu máy, định mức nhiên liệu chuẩn (L/h).<br>• **BR-02**: Trạng thái an toàn đầu ca; nút **Khóa máy khẩn cấp** nếu phát hiện lỗi nguy hiểm.<br>• **BR-10**: Phân loại rạch ròi: "Bảo dưỡng định kỳ" vs "Sửa chữa đột xuất".<br>• **BR-04**: Theo dõi Downtime: Nếu thời gian dừng máy >= 10 phút, bắt buộc có giải trình kỹ thuật.<br>• **BR-07**: Biên bản nghiệm thu chạy thử 3 bên (Lái xe, Thợ sửa chữa, Quản đốc mỏ) trước khi mở khóa máy.<br>• **BR-08**: Nhật ký cấp dầu & đối soát tiêu hao: Tự động tính L/h và **bật cảnh báo đỏ nếu chênh lệch > 10%**. |

---

## III. KỊCH BẢN DEMO TỪNG BƯỚC CHO KHÁCH HÀNG

### Kịch bản 1: Cân Xe Xuất Bán Đá & In Phiếu Cân Điện Tử (Sóng 1 & Sóng 2)
1. **Truy cập**: Đăng nhập [http://localhost:10020](http://localhost:10020), vào ứng dụng **Kho vận (Inventory)** → chọn **Phiếu Giao Hàng (Delivery Orders)**.
2. **Mở phiếu mẫu**: Mở phiếu xuất kho cho xe `36C-284.91` (Khách hàng: *Công ty CP Xây Dựng & Cầu Đường 47*).
3. **Thao tác Trạm Cân (Tab "Trạm Cân Mỏ Đá")**:
   - Biển số xe: `36C-284.91`, Tài xế: `Nguyễn Văn Mạnh`.
   - Khối lượng bì xe: `14,250 Kg`.
   - Khối lượng tổng khi có đá: `38,450 Kg`.
   - Hệ thống tự động tính:
     * **Khối Lượng Tịnh**: `24,200 Kg (24.20 Tấn)`.
     * Tỷ trọng đá 1x2: `1.55 tấn/m³`.
     * **Thể Tích Quy Đổi**: `15.61 m³`.
4. **Nút "Áp Khối Lượng Cân"**: Nhấn nút trên thanh tác vụ → Số lượng `24.20 Tấn` tự động được điền vào dòng chi tiết xuất kho mà thủ kho không cần gõ tay.
5. **Nút "In Phiếu Cân"**: Nhấn nút → Hệ thống sinh ngay file PDF **Phiếu Cân Xe Điện Tử** song ngữ có đầy đủ chữ ký Lái xe, Người cân, thông số bì/tổng/tịnh/m3.

---

### Kịch bản 2: Bán Hàng Dự Án & Cảnh Báo Công Nợ Khách Hàng (Sóng 2)
1. **Truy cập**: Vào ứng dụng **Bán hàng (Sales)** → **Đơn Bán Hàng (Orders)**.
2. **Xem đơn hàng dự án**: Mở đơn hàng `HĐ-47/2026/HP-DA`:
   - Dự án công trình: `Dự Án Cao Tốc Bắc - Nam (Gói Thầu XL-02)`.
   - Quy cách: Bán theo Tấn.
3. **Trình diễn kiểm soát hạn mức & ký quỹ**:
   - Mở khách hàng *Hợp Tác Xã Vận Tải & VLXD Hải Hòa*: Số dư tiền cọc chỉ còn `3,500,000 VNĐ`.
   - Tạo báo giá cho khách này → Hệ thống lập tức hiển thị huy hiệu cảnh báo màu vàng: *"LƯU Ý: Số dư ký quỹ sắp hết (Còn lại: 3,500,000 VNĐ). Cần nhắc khách nộp bổ sung."*
   - Khách hàng không có tiền cọc (0 VNĐ) → Hệ thống cảnh báo đỏ: *"CẢNH BÁO: Khách hàng chưa nộp tiền ký quỹ! Không cho phép xuất đá."*

---

### Kịch bản 3: Mua Sắm Vật Tư - Gắn Đích Danh Thiết Bị & Duyệt Đa Cấp (Sóng 2)
1. **Truy cập**: Vào ứng dụng **Mua hàng (Purchase)** → **Đơn Mua Hàng (Purchase Orders)**.
2. **Trường hợp A: Đơn hàng <= 20 Triệu VNĐ (TGĐ Phê Duyệt - BR-03)**:
   - Mở đơn mua phụ tùng máy xúc `EX-01` (Giá trị: `14,500,000 VNĐ`).
   - Thiết bị chịu chi phí: `Máy Xúc Đào Komatsu PC450-8 (EX-01)` (Tuân thủ BR-10).
   - Thẩm quyền: Tự động gắn nhãn **"Cấp 1: <= 20 Triệu (TGĐ Phê Duyệt)"**.
   - Trình duyệt → Nút **"TGĐ Phê Duyệt"** sáng lên → TGĐ duyệt là chuyển thẳng sang trạng thái `Đã Phê Duyệt Thẩm Quyền` để xác nhận đơn hàng.
3. **Trường hợp B: Đơn hàng > 20 Triệu VNĐ (Chủ Tịch HĐQT Phê Duyệt - BR-03)**:
   - Mở đơn mua 6 quả lốp xe ben Howo (Giá trị: `45,000,000 VNĐ`).
   - Thẩm quyền: Tự động chuyển **"Cấp 2: > 20 Triệu (Chủ Tịch HĐQT Phê Duyệt)"**.
   - Tab **"Quy Tắc 3 Báo Giá & Chỉ Định Thầu (BR-02)"**:
     * NCC 1: *Đại Lý Lốp & Săm Tiến Lốp* (45,000,000 VNĐ).
     * NCC 2: *Công ty Phụ Tùng Nam Định* (48,500,000 VNĐ).
     * NCC 3: *Lốp Xe Hà Nội CN Thanh Hóa* (49,000,000 VNĐ).
   - Luồng duyệt: Người lập nhấn **"Trình Phê Duyệt"** → TGĐ nhấn **"TGĐ Phê Duyệt"** (hệ thống ghi chú: TGĐ đã rà soát và chuyển lên cấp trên) → Nút **"Chủ Tịch HĐQT Phê Duyệt"** hiển thị để Chủ tịch HĐQT chốt quyết định cuối cùng!
4. **Nghiệm thu hiện trường (BR-05)**: Tab "Nghiệm Thu Bàn Giao Hiện Trường" cho phép tick chọn người nhận hàng và xem ảnh chụp phụ tùng tại bãi moong.

---

### Kịch bản 4: Quản Lý Cơ Giới Mỏ, Downtime & Nghiệm Thu 3 Bên (Sóng 2)
1. **Truy cập**: Vào ứng dụng **Bảo trì (Maintenance)** → **Thiết bị (Equipment)**.
2. **Khóa máy khẩn cấp khi phát hiện lỗi đầu ca (BR-02)**:
   - Mở máy xúc `EX-02` (Hitachi Zaxis 350).
   - Thiết bị đang có trạng thái **"Khóa Thiết Bị (Không Đạt An Toàn)"** do chảy dầu phớt ty thủy lực.
   - Nút **"Khóa Máy"** và **"Mở Khóa Máy"** giúp Quản đốc kiểm soát an toàn vận hành trực tiếp.
3. **Phiếu yêu cầu sửa chữa & Theo dõi dừng máy (BR-04, BR-10)**:
   - Mở phiếu sửa chữa máy xúc `EX-02`:
   - Phân loại: **Sửa Chữa Đột Xuất (Sự Cố/Hỏng Hóc)**.
   - Thời gian dừng máy: `45 phút` (>= 10 phút).
   - Bắt buộc giải trình kỹ thuật: *"Đá tảng lăn va đập làm rách tuy-ô thủy lực áp cao cấp cho ty gầu múc. Đã thay mới tuy-ô 4 lớp thép 32mm và châm thêm 40L dầu thủy lực 68."*
4. **Biên bản nghiệm thu 3 bên trước khi mở máy (BR-07)**:
   - 1. Lái xe vận hành thử (OK) + Ghi chú chạy thử 15 phút êm ái.
   - 2. Thợ sửa chữa hoàn thành (OK).
   - 3. Quản đốc mỏ phê duyệt mở máy (OK).
   - Nhấn nút **"Nghiệm Thu 3 Bên (BR-07)"** → Hệ thống xác nhận đủ 3 bên và tự động mở khóa thiết bị `EX-02` trở lại vận hành an toàn!

---

### Kịch bản 5: Nhật Ký Cấp Dầu & Cảnh Báo Vượt Định Mức >10% (BR-08)
1. **Truy cập**: Vào menu **Bảo trì (Maintenance)** → chọn menu **"Nhật Ký Cấp Dầu (BR-08)"**.
2. **Trường hợp bình thường**:
   - Mở phiếu cấp dầu Máy xúc `EX-01`: Chạy 10 giờ, cấp 320 lít dầu → Tiêu hao: `32.0 L/h` (Định mức chuẩn: 32.5 L/h, chênh lệch -1.5% → Huy hiệu màu xanh an toàn).
3. **Trường hợp cảnh báo đỏ vượt định mức >10% (BR-08)**:
   - Mở phiếu cấp dầu Xe ben `36C-315.68`:
   - Giờ cũ: 2,100h, Giờ mới: 2,110h (Chạy 10 giờ).
   - Lượng dầu cấp: 245 lít → Tiêu hao thực tế: `24.5 L/h` (Định mức chuẩn: 21.0 L/h → **Vượt quá +16.7%**!).
   - **Hệ thống lập tức kích hoạt Cảnh báo đỏ**: *"CẢNH BÁO BR-08: Lượng dầu tiêu hao thực tế vượt quá định mức chuẩn trên 10%! Bắt buộc phải có giải trình kỹ thuật trước khi lưu."*
   - Ghi nhận giải trình kỹ thuật: *"Đường vận chuyển từ moong sâu lên bãi sàng bị sình lầy do mưa đêm, xe phải gài 2 cầu chạy số 1 liên tục..."*

---

## IV. TỔNG KẾT GIÁ TRỊ MANG LẠI CHO KHÁCH HÀNG

1. **Giữ nguyên 100% trải nghiệm Odoo EE chuẩn**: Người dùng không phải học một hệ thống xa lạ; mọi thao tác diễn ra quen thuộc trên Kho, Bán hàng, Mua hàng, Bảo trì.
2. **Bịt kín các lỗ hổng quản trị ngành mỏ**:
   - Tránh gian lận khối lượng và thất thoát đá qua trạm cân.
   - Tránh nợ xấu nhờ cơ chế khóa xe thời gian thực theo số dư ký quỹ.
   - Kiểm soát chi phí phụ tùng máy móc (gắn đích danh xe, 3 báo giá, duyệt phân cấp tài chính).
   - Chặn đứng thất thoát dầu DO nhờ cơ chế cảnh báo tự động khi vượt định mức >10%.
   - Tuân thủ quy định an toàn lao động và pháp lý mỏ đá (kho VLNCN, checklist đầu ca, nghiệm thu 3 bên).
