import odoo
from odoo import api, fields, SUPERUSER_ID

def populate_demo_data(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    company = env.ref('base.main_company')
    vnd_currency = env.ref('base.VND', raise_if_not_found=False) or company.currency_id

    # 1. Products
    prod_tmpl_obj = env['product.template']
    products_data = [
        {'name': 'Đá 1x2 (Đá Bê Tông)', 'density': 1.55, 'is_quarry_stone': True, 'list_price': 220000.0, 'standard_price': 160000.0},
        {'name': 'Đá 4x6 (Đá Cấp Phối Móng)', 'density': 1.60, 'is_quarry_stone': True, 'list_price': 190000.0, 'standard_price': 140000.0},
        {'name': 'Đá Base A (Cấp Phối Đắp Nền)', 'density': 1.68, 'is_quarry_stone': True, 'list_price': 175000.0, 'standard_price': 125000.0},
        {'name': 'Đá Mi Bụi (Bột Đá Sàng)', 'density': 1.48, 'is_quarry_stone': True, 'list_price': 130000.0, 'standard_price': 90000.0},
        {'name': 'Đá Hộc Khai Thác Mỏ', 'density': 1.62, 'is_quarry_stone': True, 'list_price': 160000.0, 'standard_price': 110000.0},
        {'name': 'Thuốc Nổ Nhũ Tương Mỏ (Dầu)', 'density': 1.15, 'is_explosive': True, 'list_price': 45000.0, 'standard_price': 38000.0},
        {'name': 'Kíp Nổ Vi Sai Phi Điện', 'density': 0.0, 'is_explosive': True, 'list_price': 25000.0, 'standard_price': 20000.0},
        {'name': 'Răng Gầu Máy Xúc Komatsu PC450', 'is_quarry_spare_part': True, 'list_price': 1800000.0, 'standard_price': 1450000.0},
        {'name': 'Lốp Xe Ben Mỏ Howo 12.00R20', 'is_quarry_spare_part': True, 'list_price': 7800000.0, 'standard_price': 6500000.0},
        {'name': 'Dầu Diesel 0.05S (DO Mỏ)', 'list_price': 21500.0, 'standard_price': 19800.0},
    ]

    products = {}
    for p_val in products_data:
        existing = prod_tmpl_obj.search([('name', '=', p_val['name'])], limit=1)
        if not existing:
            vals = {
                'name': p_val['name'],
                'type': 'consu',
                'list_price': p_val.get('list_price', 0.0),
                'standard_price': p_val.get('standard_price', 0.0),
                'density': p_val.get('density', 1.6),
                'is_quarry_stone': p_val.get('is_quarry_stone', False),
                'is_explosive': p_val.get('is_explosive', False),
                'is_quarry_spare_part': p_val.get('is_quarry_spare_part', False),
            }
            existing = prod_tmpl_obj.create(vals)
        products[p_val['name']] = existing.product_variant_id

    # 2. Customers & Suppliers
    partner_obj = env['res.partner']
    partners_data = [
        {
            'name': 'Công ty CP Xây Dựng & Cầu Đường 47',
            'is_company': True,
            'customer_rank': 1,
            'quarry_customer_type': 'credit',
            'quarry_credit_limit': 500000000.0,
            'quarry_payment_term_days': 30,
            'phone': '0912.345.678',
            'street': 'Khu công nghiệp Lễ Môn, TP. Thanh Hóa',
        },
        {
            'name': 'Công ty Bê Tông Tươi Xuân Mai - Nghi Sơn',
            'is_company': True,
            'customer_rank': 1,
            'quarry_customer_type': 'prepaid',
            'deposit_balance': 120000000.0,
            'phone': '0936.888.999',
            'street': 'Khu kinh tế Nghi Sơn, Tĩnh Gia, Thanh Hóa',
        },
        {
            'name': 'Hợp Tác Xã Vận Tải & VLXD Hải Hòa',
            'is_company': True,
            'customer_rank': 1,
            'quarry_customer_type': 'prepaid',
            'deposit_balance': 3500000.0, # Warning low balance
            'phone': '0988.112.233',
            'street': 'Thị trấn Hà Trung, Thanh Hóa',
        },
        {
            'name': 'Doanh Nghiệp Tư Nhân Túy Hoài',
            'is_company': True,
            'supplier_rank': 1,
            'phone': '0903.456.789',
            'street': 'Hà Trung, Thanh Hóa',
        },
        {
            'name': 'Công Ty Phụ Tùng Cơ Giới Đức Soạn',
            'is_company': True,
            'supplier_rank': 1,
            'phone': '0915.667.889',
            'street': 'Bỉm Sơn, Thanh Hóa',
        },
        {
            'name': 'Đại Lý Lốp & Săm Tiến Lốp',
            'is_company': True,
            'supplier_rank': 1,
            'phone': '0979.334.556',
            'street': 'Quốc lộ 1A, Hà Trung, Thanh Hóa',
        },
    ]

    partners = {}
    for pt in partners_data:
        existing = partner_obj.search([('name', '=', pt['name'])], limit=1)
        if not existing:
            existing = partner_obj.create(pt)
        else:
            existing.write(pt)
        partners[pt['name']] = existing

    # 3. Equipment (Máy móc thiết bị mỏ)
    eq_obj = env['maintenance.equipment']
    eq_data = [
        {
            'name': 'Máy Xúc Đào Komatsu PC450-8',
            'vehicle_plate': 'EX-01',
            'equipment_quarry_type': 'excavator',
            'standard_fuel_rate': 32.5,
            'pre_shift_safety_status': 'safe',
        },
        {
            'name': 'Máy Xúc Đào Hitachi Zaxis 350',
            'vehicle_plate': 'EX-02',
            'equipment_quarry_type': 'excavator',
            'standard_fuel_rate': 28.0,
            'pre_shift_safety_status': 'locked',
            'safety_lock_reason': 'Chảy dầu phớt ty thủy lực gầu múc (BR-02)',
        },
        {
            'name': 'Xe Ben Mỏ Howo 371HP (3 Giò)',
            'vehicle_plate': '36C-284.91',
            'equipment_quarry_type': 'truck',
            'standard_fuel_rate': 18.0,
            'pre_shift_safety_status': 'safe',
        },
        {
            'name': 'Xe Ben Mỏ Howo 371HP (4 Giò)',
            'vehicle_plate': '36C-315.68',
            'equipment_quarry_type': 'truck',
            'standard_fuel_rate': 21.0,
            'pre_shift_safety_status': 'safe',
        },
        {
            'name': 'Trạm Nghiền Sàng Liên Hợp 250 T/h',
            'vehicle_plate': 'CRUSH-01',
            'equipment_quarry_type': 'crusher',
            'standard_fuel_rate': 65.0,
            'pre_shift_safety_status': 'safe',
        },
    ]

    equipments = {}
    for eq in eq_data:
        existing = eq_obj.search([('name', '=', eq['name'])], limit=1)
        if not existing:
            existing = eq_obj.create(eq)
        else:
            existing.write(eq)
        equipments[eq['vehicle_plate']] = existing

    # 4. Sale Orders (Đơn bán hàng theo hợp đồng đá)
    so_obj = env['sale.order']
    customer_1 = partners['Công ty CP Xây Dựng & Cầu Đường 47']
    existing_so = so_obj.search([('partner_id', '=', customer_1.id), ('contract_ref', '=', 'HĐ-47/2026/HP-DA')], limit=1)
    if not existing_so:
        so = so_obj.create({
            'partner_id': customer_1.id,
            'project_name': 'Dự Án Cao Tốc Bắc - Nam (Gói Thầu XL-02)',
            'contract_ref': 'HĐ-47/2026/HP-DA',
            'quarry_uom_type': 'ton',
            'order_line': [
                (0, 0, {
                    'product_id': products['Đá 1x2 (Đá Bê Tông)'].id,
                    'product_uom_qty': 5000.0,
                    'price_unit': 220000.0,
                }),
                (0, 0, {
                    'product_id': products['Đá 4x6 (Đá Cấp Phối Móng)'].id,
                    'product_uom_qty': 3000.0,
                    'price_unit': 190000.0,
                })
            ]
        })

    # 5. Stock Pickings (Phiếu xuất / nhập kho trạm cân)
    picking_obj = env['stock.picking']
    picking_type_out = env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
    picking_type_in = env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
    move_uom_field = 'uom_id' if 'uom_id' in env['stock.move']._fields else 'product_uom'

    # Scale ticket 1: Xuất đá thành phẩm xe Howo 36C-284.91
    existing_pick = picking_obj.search([('vehicle_plate', '=', '36C-284.91')], limit=1)
    if not existing_pick and picking_type_out:
        p1 = picking_obj.create({
            'picking_type_id': picking_type_out.id,
            'partner_id': customer_1.id,
            'location_id': picking_type_out.default_location_src_id.id,
            'location_dest_id': customer_1.property_stock_customer.id,
            'is_scale_picking': True,
            'vehicle_plate': '36C-284.91',
            'driver_name': 'Nguyễn Văn Mạnh',
            'weigh_scale_number': 'Trạm Cân Số 1',
            'crushing_plant': 'plant_1',
            'tare_weight': 14250.0,
            'gross_weight': 38450.0,
            'density': 1.55,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Đá 1x2 (Đá Bê Tông)'].id,
                    'product_uom_qty': 24.20,
                    'quantity': 24.20,
                    move_uom_field: products['Đá 1x2 (Đá Bê Tông)'].uom_id.id,
                    'location_id': picking_type_out.default_location_src_id.id,
                    'location_dest_id': customer_1.property_stock_customer.id,
                })
            ]
        })

    # Scale ticket 2: Nhập đá thô cấp liệu trạm nghiền
    existing_pick_in = picking_obj.search([('vehicle_plate', '=', '36C-315.68')], limit=1)
    if not existing_pick_in and picking_type_in:
        p2 = picking_obj.create({
            'picking_type_id': picking_type_in.id,
            'is_scale_picking': True,
            'vehicle_plate': '36C-315.68',
            'driver_name': 'Lê Hoàng Long',
            'weigh_scale_number': 'Trạm Cân Số 2',
            'crushing_plant': 'plant_1',
            'tare_weight': 15100.0,
            'gross_weight': 46300.0,
            'density': 1.62,
            'location_id': picking_type_in.default_location_src_id.id,
            'location_dest_id': picking_type_in.default_location_dest_id.id,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Đá Hộc Khai Thác Mỏ'].id,
                    'product_uom_qty': 31.20,
                    'quantity': 31.20,
                    move_uom_field: products['Đá Hộc Khai Thác Mỏ'].uom_id.id,
                    'location_id': picking_type_in.default_location_src_id.id,
                    'location_dest_id': picking_type_in.default_location_dest_id.id,
                })
            ]
        })

    # 6. Purchase Orders (Mua hàng phân cấp duyệt <=20M & >20M)
    po_obj = env['purchase.order']
    supp_tien_lop = partners['Đại Lý Lốp & Săm Tiến Lốp']
    supp_duc_soan = partners['Công Ty Phụ Tùng Cơ Giới Đức Soạn']

    # PO 1: <= 20M: Phụ tùng máy xúc EX-01 (Đã duyệt TGĐ)
    existing_po1 = po_obj.search([('partner_id', '=', supp_duc_soan.id)], limit=1)
    if not existing_po1:
        po1 = po_obj.create({
            'partner_id': supp_duc_soan.id,
            'equipment_id': equipments['EX-01'].id,
            'supplier_payment_term_type': 'special_1m',
            'is_single_source': True,
            'single_source_reason': 'Phụ tùng chính hãng Komatsu từ nhà phân phối độc quyền khu vực Bắc Trung Bộ.',
            'approval_state': 'approved',
            'field_inspected': True,
            'order_line': [
                (0, 0, {
                    'product_id': products['Răng Gầu Máy Xúc Komatsu PC450'].id,
                    'product_qty': 10.0,
                    'price_unit': 1450000.0, # 14.5M <= 20M
                })
            ]
        })

    # PO 2: > 20M: Mua Lốp xe ben Howo (Chờ CT HĐQT duyệt)
    existing_po2 = po_obj.search([('partner_id', '=', supp_tien_lop.id)], limit=1)
    if not existing_po2:
        po2 = po_obj.create({
            'partner_id': supp_tien_lop.id,
            'equipment_id': equipments['36C-284.91'].id,
            'supplier_payment_term_type': 'special_1m',
            'is_single_source': False,
            'quote_source_1': 'Đại Lý Lốp & Săm Tiến Lốp (45.000.000 VNĐ)',
            'quote_price_1': 45000000.0,
            'quote_source_2': 'Công ty Phụ Tùng Nam Định (48.500.000 VNĐ)',
            'quote_price_2': 48500000.0,
            'quote_source_3': 'Lốp Xe Hà Nội Chi Nhánh Thanh Hóa (49.000.000 VNĐ)',
            'quote_price_3': 49000000.0,
            'approval_state': 'waiting_chairman',
            'order_line': [
                (0, 0, {
                    'product_id': products['Lốp Xe Ben Mỏ Howo 12.00R20'].id,
                    'product_qty': 6.0,
                    'price_unit': 7500000.0, # 45M > 20M
                })
            ]
        })

    # 7. Maintenance Request (Sự cố máy xúc EX-02 có dừng máy 45 phút & nghiệm thu 3 bên)
    maint_req_obj = env['maintenance.request']
    existing_mr = maint_req_obj.search([('equipment_id', '=', equipments['EX-02'].id)], limit=1)
    if not existing_mr:
        maint_req_obj.create({
            'name': 'Sự Cố Bục Tuy-Ô Thủy Lực Ty Gầu Múc EX-02',
            'equipment_id': equipments['EX-02'].id,
            'request_category': 'corrective',
            'downtime_minutes': 45,
            'downtime_cause': 'hydraulic',
            'downtime_explanation': 'Đá tảng lăn va đập làm rách tuy-ô thủy lực áp cao cấp cho ty gầu múc. Đã thay mới tuy-ô 4 lớp thép 32mm và châm thêm 40L dầu thủy lực 68.',
            'driver_confirmed': True,
            'driver_notes': 'Lái máy đã vận hành thử 15 phút, áp lực xúc khỏe, không còn rò rỉ dầu.',
            'mechanic_confirmed': True,
            'manager_confirmed': True,
        })

    # 8. Fuel Logs (Nhật ký cấp dầu & Cảnh báo vượt >10%)
    fuel_log_obj = env['hoangphuc.fuel.log']
    
    # Log 1: Máy xúc EX-01 (Tiêu hao bình thường)
    fuel_log_obj.create({
        'equipment_id': equipments['EX-01'].id,
        'log_date': fields.Date.today(),
        'driver_name': 'Trần Văn Quyết',
        'previous_meter': 1420.0,
        'current_meter': 1430.0,
        'fuel_liters': 320.0, # 32.0 L/h vs std 32.5 L/h (-1.5%)
        'fuel_station': 'Téc Dầu Kho Mỏ Núi Dài',
    })

    # Log 2: Xe ben 36C-315.68 (Cảnh báo đỏ vượt > 10% - BR-08)
    fuel_log_obj.create({
        'equipment_id': equipments['36C-315.68'].id,
        'log_date': fields.Date.today(),
        'driver_name': 'Lê Hoàng Long',
        'previous_meter': 2100.0,
        'current_meter': 2110.0,
        'fuel_liters': 245.0, # 24.5 L/h vs std 21.0 L/h (+16.7% > 10%)
        'fuel_station': 'Xe Bồn Cấp Dầu Lưu Động Bãi Moong',
        'technical_explanation': 'Đường vận chuyển từ moong sâu lên bãi sàng bị sình lầy do mưa đêm, xe phải gài 2 cầu chạy số 1 liên tục làm tăng tiêu hao nhiên liệu (BR-08).',
    })

    print("SUCCESS: Hoang Phuc demo data populated successfully!")
