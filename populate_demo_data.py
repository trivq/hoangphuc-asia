import odoo
from odoo import api, fields, SUPERUSER_ID
import datetime

def populate_demo_data(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    company = env.ref('base.main_company')
    vnd_currency = env.ref('base.VND', raise_if_not_found=False) or company.currency_id
    std_layout = env.ref('web.external_layout_standard', raise_if_not_found=False)
    if std_layout and not company.external_report_layout_id:
        company.external_report_layout_id = std_layout

    # -------------------------------------------------------------
    # 0. CẤU HÌNH NHÓM QUYỀN (SECURITY GROUPS) CHO QUẢN LÝ KHO & LÔ
    # -------------------------------------------------------------
    admin_user = env.ref('base.user_admin')
    stock_groups = [
        env.ref('stock.group_production_lot', raise_if_not_found=False),
        env.ref('stock.group_stock_multi_locations', raise_if_not_found=False),
        env.ref('stock.group_stock_multi_warehouses', raise_if_not_found=False),
    ]
    groups_to_add = [g.id for g in stock_groups if g]
    if groups_to_add:
        admin_user.write({'group_ids': [(4, gid) for gid in groups_to_add]})
        base_user_grp = env.ref('base.group_user', raise_if_not_found=False)
        if base_user_grp:
            base_user_grp.write({'implied_ids': [(4, gid) for gid in groups_to_add]})

    # -------------------------------------------------------------
    # 1. THIẾT LẬP KHO HÀNG (STOCK WAREHOUSES & LOCATIONS)
    # -------------------------------------------------------------
    wh_obj = env['stock.warehouse']
    
    # 1.1 Kho Thành Phẩm Đá Chính
    wh_main = wh_obj.search([('code', 'in', ['WH', 'KTP'])], limit=1)
    if wh_main:
        wh_main.write({
            'name': 'Kho Thành Phẩm Mỏ Đá Hoàng Phúc',
            'is_explosive_warehouse': False,
        })
    else:
        wh_main = wh_obj.create({
            'name': 'Kho Thành Phẩm Mỏ Đá Hoàng Phúc',
            'code': 'WH',
            'is_explosive_warehouse': False,
        })

    # 1.2 Kho Vật Liệu Nổ Công Nghiệp (VLNCN) - Tuân thủ an toàn PCCC & Hạn mức
    wh_vln = wh_obj.search([('code', '=', 'VLN')], limit=1)
    if not wh_vln:
        wh_vln = wh_obj.create({
            'name': 'Kho Vật Liệu Nổ Mỏ Núi Dài (VLNCN)',
            'code': 'VLN',
            'is_explosive_warehouse': True,
            'max_explosives_kg': 5000.0,    # Hạn mức thuốc nổ tối đa 5,000 kg
            'max_detonators_pcs': 50000,    # Hạn mức kíp nổ tối đa 50,000 cái
        })
    else:
        wh_vln.write({
            'name': 'Kho Vật Liệu Nổ Mỏ Núi Dài (VLNCN)',
            'is_explosive_warehouse': True,
            'max_explosives_kg': 5000.0,
            'max_detonators_pcs': 50000,
        })

    # 1.3 Kho Vật Tư - Phụ Tùng & Dầu Mỡ Mỏ
    wh_vt = wh_obj.search([('code', '=', 'KVT')], limit=1)
    if not wh_vt:
        wh_vt = wh_obj.create({
            'name': 'Kho Vật Tư - Phụ Tùng & Dầu Mỡ Mỏ Núi Dài',
            'code': 'KVT',
            'is_explosive_warehouse': False,
        })
    else:
        wh_vt.write({
            'name': 'Kho Vật Tư - Phụ Tùng & Dầu Mỡ Mỏ Núi Dài',
            'is_explosive_warehouse': False,
        })

    # -------------------------------------------------------------
    # 2. ĐƠN VỊ TÍNH (UOM) & DANH MỤC SẢN PHẨM (PRODUCT CATEGORIES)
    # -------------------------------------------------------------
    uom_kg = env.ref('uom.product_uom_kgm')
    uom_unit = env.ref('uom.product_uom_unit')
    uom_meter = env.ref('uom.product_uom_meter')
    uom_liter = env.ref('uom.product_uom_litre')
    uom_ton = env.ref('uom.product_uom_ton')

    cat_obj = env['product.category']
    goods_cat = env.ref('product.product_category_all', raise_if_not_found=False) or cat_obj.search([('name', '=', 'Goods')], limit=1)
    
    categories = {}
    cats_data = [
        'Vật Liệu Nổ Công Nghiệp (VLNCN)',
        'Vật Tư & Phụ Tùng Cơ Giới Mỏ',
        'Nhiên Liệu - Dầu Mỡ Mỏ',
        'Đá Khai Thác & Thành Phẩm',
    ]
    for cname in cats_data:
        c_rec = cat_obj.search([('name', '=', cname)], limit=1)
        if not c_rec:
            c_rec = cat_obj.create({
                'name': cname,
                'parent_id': goods_cat.id if goods_cat else False,
            })
        categories[cname] = c_rec

    # -------------------------------------------------------------
    # 3. DANH MỤC HÀNG HÓA & SẢN PHẨM (PRODUCTS)
    # -------------------------------------------------------------
    prod_tmpl_obj = env['product.template']
    products_data = [
        # Đá mỏ & thành phẩm
        {
            'name': 'Đá 1x2 (Đá Bê Tông)',
            'density': 1.55,
            'is_quarry_stone': True,
            'list_price': 220000.0,
            'standard_price': 160000.0,
            'uom_id': uom_ton.id,
            'categ_id': categories['Đá Khai Thác & Thành Phẩm'].id,
            'tracking': False,
        },
        {
            'name': 'Đá 4x6 (Đá Cấp Phối Móng)',
            'density': 1.60,
            'is_quarry_stone': True,
            'list_price': 190000.0,
            'standard_price': 140000.0,
            'uom_id': uom_ton.id,
            'categ_id': categories['Đá Khai Thác & Thành Phẩm'].id,
            'tracking': False,
        },
        {
            'name': 'Đá Base A (Cấp Phối Đắp Nền)',
            'density': 1.68,
            'is_quarry_stone': True,
            'list_price': 175000.0,
            'standard_price': 125000.0,
            'uom_id': uom_ton.id,
            'categ_id': categories['Đá Khai Thác & Thành Phẩm'].id,
            'tracking': False,
        },
        {
            'name': 'Đá Mi Bụi (Bột Đá Sàng)',
            'density': 1.48,
            'is_quarry_stone': True,
            'list_price': 130000.0,
            'standard_price': 90000.0,
            'uom_id': uom_ton.id,
            'categ_id': categories['Đá Khai Thác & Thành Phẩm'].id,
            'tracking': False,
        },
        {
            'name': 'Đá Hộc Khai Thác Mỏ',
            'density': 1.62,
            'is_quarry_stone': True,
            'list_price': 160000.0,
            'standard_price': 110000.0,
            'uom_id': uom_ton.id,
            'categ_id': categories['Đá Khai Thác & Thành Phẩm'].id,
            'tracking': False,
        },
        # Vật liệu nổ công nghiệp (VLNCN) - Quản lý theo Lô (tracking='lot')
        {
            'name': 'Thuốc Nổ Nhũ Tương Mỏ (Dầu)',
            'density': 1.15,
            'is_explosive': True,
            'list_price': 45000.0,
            'standard_price': 38000.0,
            'uom_id': uom_kg.id,
            'categ_id': categories['Vật Liệu Nổ Công Nghiệp (VLNCN)'].id,
            'tracking': 'lot',
        },
        {
            'name': 'Thuốc Nổ ANFO Mỏ Núi Dài',
            'density': 0.95,
            'is_explosive': True,
            'list_price': 35000.0,
            'standard_price': 29500.0,
            'uom_id': uom_kg.id,
            'categ_id': categories['Vật Liệu Nổ Công Nghiệp (VLNCN)'].id,
            'tracking': 'lot',
        },
        {
            'name': 'Kíp Nổ Vi Sai Phi Điện MS25 (Dây 5m)',
            'density': 0.0,
            'is_explosive': True,
            'list_price': 26000.0,
            'standard_price': 21000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Liệu Nổ Công Nghiệp (VLNCN)'].id,
            'tracking': 'lot',
        },
        {
            'name': 'Kíp Nổ Vi Sai Phi Điện MS50 (Dây 7m)',
            'density': 0.0,
            'is_explosive': True,
            'list_price': 28000.0,
            'standard_price': 22500.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Liệu Nổ Công Nghiệp (VLNCN)'].id,
            'tracking': 'lot',
        },
        {
            'name': 'Kíp Nổ Điện Số 8 Tức Thời',
            'density': 0.0,
            'is_explosive': True,
            'list_price': 22000.0,
            'standard_price': 18000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Liệu Nổ Công Nghiệp (VLNCN)'].id,
            'tracking': 'lot',
        },
        {
            'name': 'Dây Nổ Chịu Nước Phi 6 (12g/m)',
            'density': 0.0,
            'is_explosive': True,
            'list_price': 15000.0,
            'standard_price': 12000.0,
            'uom_id': uom_meter.id,
            'categ_id': categories['Vật Liệu Nổ Công Nghiệp (VLNCN)'].id,
            'tracking': 'lot',
        },
        {
            'name': 'Dây Cháy Chậm An Toàn',
            'density': 0.0,
            'is_explosive': True,
            'list_price': 9000.0,
            'standard_price': 7500.0,
            'uom_id': uom_meter.id,
            'categ_id': categories['Vật Liệu Nổ Công Nghiệp (VLNCN)'].id,
            'tracking': 'lot',
        },
        # Vật tư & Phụ tùng cơ giới mỏ (BR-10)
        {
            'name': 'Răng Gầu Máy Xúc Komatsu PC450',
            'is_quarry_spare_part': True,
            'list_price': 1800000.0,
            'standard_price': 1450000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Tư & Phụ Tùng Cơ Giới Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Lốp Xe Ben Mỏ Howo 12.00R20',
            'is_quarry_spare_part': True,
            'list_price': 7800000.0,
            'standard_price': 6500000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Tư & Phụ Tùng Cơ Giới Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Tuy-Ô Thủy Lực Áp Cao 4 Lớp Thép 32mm (L=2.5m)',
            'is_quarry_spare_part': True,
            'list_price': 2200000.0,
            'standard_price': 1750000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Tư & Phụ Tùng Cơ Giới Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Dầu Thủy Lực Castrol Hyspin AWS 68 (Phuy 200L)',
            'is_quarry_spare_part': True,
            'list_price': 75000.0,
            'standard_price': 62000.0,
            'uom_id': uom_liter.id,
            'categ_id': categories['Nhiên Liệu - Dầu Mỡ Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Dầu Nhớt Động Cơ Caltex Delo 400 15W-40 (Xô 18L)',
            'is_quarry_spare_part': True,
            'list_price': 95000.0,
            'standard_price': 78000.0,
            'uom_id': uom_liter.id,
            'categ_id': categories['Nhiên Liệu - Dầu Mỡ Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Mỡ Bò Bôi Trơn Chịu Nhiệt Sinopec HP-R (Xô 15kg)',
            'is_quarry_spare_part': True,
            'list_price': 120000.0,
            'standard_price': 95000.0,
            'uom_id': uom_kg.id,
            'categ_id': categories['Nhiên Liệu - Dầu Mỡ Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Lưới Sàng Đá 1x2 Thép Mangan 65Mn (1.5m x 2m)',
            'is_quarry_spare_part': True,
            'list_price': 3500000.0,
            'standard_price': 2800000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Tư & Phụ Tùng Cơ Giới Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Búa Đập Đá Sơ Cấp Trạm Nghiền 250T/h',
            'is_quarry_spare_part': True,
            'list_price': 4200000.0,
            'standard_price': 3400000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Tư & Phụ Tùng Cơ Giới Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Con Lăn Băng Tải Mỏ D89x600mm',
            'is_quarry_spare_part': True,
            'list_price': 320000.0,
            'standard_price': 250000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Tư & Phụ Tùng Cơ Giới Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Bình Ắc Quy GS 12V-150Ah Cho Xe Howo',
            'is_quarry_spare_part': True,
            'list_price': 3100000.0,
            'standard_price': 2600000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Tư & Phụ Tùng Cơ Giới Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Vòng Bi Tang Trống SKF 22320 CC/W33',
            'is_quarry_spare_part': True,
            'list_price': 5400000.0,
            'standard_price': 4300000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Tư & Phụ Tùng Cơ Giới Mỏ'].id,
            'tracking': False,
        },
        {
            'name': 'Dây Curoa Trạm Nghiền B120',
            'is_quarry_spare_part': True,
            'list_price': 180000.0,
            'standard_price': 140000.0,
            'uom_id': uom_unit.id,
            'categ_id': categories['Vật Tư & Phụ Tùng Cơ Giới Mỏ'].id,
            'tracking': False,
        },
        # Nhiên liệu mỏ
        {
            'name': 'Dầu Diesel 0.05S (DO Mỏ)',
            'list_price': 21500.0,
            'standard_price': 19800.0,
            'uom_id': uom_liter.id,
            'categ_id': categories['Nhiên Liệu - Dầu Mỡ Mỏ'].id,
            'tracking': False,
        },
    ]

    products = {}
    for p_val in products_data:
        vals = {
            'name': p_val['name'],
            'type': 'consu',
            'is_storable': True,
            'list_price': p_val.get('list_price', 0.0),
            'standard_price': p_val.get('standard_price', 0.0),
            'density': p_val.get('density', 1.6),
            'is_quarry_stone': p_val.get('is_quarry_stone', False),
            'is_explosive': p_val.get('is_explosive', False),
            'is_quarry_spare_part': p_val.get('is_quarry_spare_part', False),
            'tracking': p_val.get('tracking') or False,
        }
        if p_val.get('uom_id'):
            vals['uom_id'] = p_val['uom_id']
        if p_val.get('categ_id'):
            vals['categ_id'] = p_val['categ_id']

        existing = prod_tmpl_obj.search([('name', '=', p_val['name'])], limit=1)
        if not existing:
            existing = prod_tmpl_obj.create(vals)
        else:
            existing.write(vals)
        products[p_val['name']] = existing.product_variant_id

    # -------------------------------------------------------------
    # 4. ĐỐI TÁC: KHÁCH HÀNG & NHÀ CUNG CẤP (PARTNERS)
    # -------------------------------------------------------------
    partner_obj = env['res.partner']
    partners_data = [
        # Khách hàng
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
            'deposit_balance': 3500000.0,
            'phone': '0988.112.233',
            'street': 'Thị trấn Hà Trung, Thanh Hóa',
        },
        # Nhà cung cấp vật tư cơ giới
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
        # Nhà cung cấp Vật Liệu Nổ Công Nghiệp (VLNCN)
        {
            'name': 'Tổng Công ty Kinh tế Kỹ thuật Công nghiệp Quốc phòng (GAET)',
            'is_company': True,
            'supplier_rank': 1,
            'phone': '024.3822.8888',
            'street': 'Số 47 Phạm Văn Đồng, Cầu Giấy, Hà Nội',
        },
        {
            'name': 'Công ty TNHH MTV Hóa chất 21 (Nhà máy Z121 - BQP)',
            'is_company': True,
            'supplier_rank': 1,
            'phone': '0210.3865.121',
            'street': 'Xã Phú Hộ, Thị xã Phú Thọ, Phú Thọ',
        },
        {
            'name': 'Tổng Công ty Hóa chất mỏ (MICCO) - Vinacomin',
            'is_company': True,
            'supplier_rank': 1,
            'phone': '024.3854.1234',
            'street': 'Số 1 Phan Đình Giót, Thanh Xuân, Hà Nội',
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

    # -------------------------------------------------------------
    # 5. THIẾT BỊ / XE MÁY MỎ (MAINTENANCE EQUIPMENT)
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 6. QUẢN LÝ LÔ VẬT LIỆU NỔ CÔNG NGHIỆP (STOCK LOTS)
    # -------------------------------------------------------------
    lot_obj = env['stock.lot']
    lots_data = [
        {
            'name': 'LOT-TN-2026-01',
            'product_id': products['Thuốc Nổ Nhũ Tương Mỏ (Dầu)'].id,
            'mfg_date': '2026-01-15',
            'exp_date': '2027-01-15',
            'manufacturer': 'Tổng Công ty Kinh tế Kỹ thuật Công nghiệp Quốc phòng (GAET) - Nhà máy Z115',
            'license_number': 'GP-VLN-089/2026/BCT',
        },
        {
            'name': 'LOT-ANFO-2026-02',
            'product_id': products['Thuốc Nổ ANFO Mỏ Núi Dài'].id,
            'mfg_date': '2026-02-01',
            'exp_date': '2026-08-01',
            'manufacturer': 'Tổng Công ty Hóa chất mỏ (MICCO)',
            'license_number': 'GP-VLN-112/2026/BCT',
        },
        {
            'name': 'LOT-KN-MS25-26',
            'product_id': products['Kíp Nổ Vi Sai Phi Điện MS25 (Dây 5m)'].id,
            'mfg_date': '2026-02-10',
            'exp_date': '2028-02-10',
            'manufacturer': 'Công ty TNHH MTV Hóa chất 21 (Nhà máy Z121 - BQP)',
            'license_number': 'GP-VKN-045/2026/BCT',
        },
        {
            'name': 'LOT-KN-MS50-26',
            'product_id': products['Kíp Nổ Vi Sai Phi Điện MS50 (Dây 7m)'].id,
            'mfg_date': '2026-02-10',
            'exp_date': '2028-02-10',
            'manufacturer': 'Công ty TNHH MTV Hóa chất 21 (Nhà máy Z121 - BQP)',
            'license_number': 'GP-VKN-045/2026/BCT',
        },
        {
            'name': 'LOT-KNE8-26',
            'product_id': products['Kíp Nổ Điện Số 8 Tức Thời'].id,
            'mfg_date': '2026-01-20',
            'exp_date': '2028-01-20',
            'manufacturer': 'Công ty TNHH MTV Hóa chất 21 (Nhà máy Z121 - BQP)',
            'license_number': 'GP-VKN-046/2026/BCT',
        },
        {
            'name': 'LOT-DN-WP26',
            'product_id': products['Dây Nổ Chịu Nước Phi 6 (12g/m)'].id,
            'mfg_date': '2026-01-20',
            'exp_date': '2028-01-20',
            'manufacturer': 'Nhà máy Z115 - Tổng công ty GAET',
            'license_number': 'GP-VLN-090/2026/BCT',
        },
        {
            'name': 'LOT-DCC-26',
            'product_id': products['Dây Cháy Chậm An Toàn'].id,
            'mfg_date': '2026-01-20',
            'exp_date': '2028-01-20',
            'manufacturer': 'Nhà máy Z115 - Tổng công ty GAET',
            'license_number': 'GP-VLN-091/2026/BCT',
        },
    ]

    lots = {}
    for l_data in lots_data:
        l_rec = lot_obj.search([('name', '=', l_data['name']), ('product_id', '=', l_data['product_id'])], limit=1)
        if not l_rec:
            l_rec = lot_obj.create(l_data)
        else:
            l_rec.write(l_data)
        lots[l_data['name']] = l_rec

    # -------------------------------------------------------------
    # 7. SỐ DƯ TỒN KHO THỰC TẾ (STOCK QUANTS)
    # -------------------------------------------------------------
    quant_obj = env['stock.quant']

    # 7.1 Tồn kho Kho Vật Liệu Nổ (VLN/Stock)
    # Tổng thuốc nổ = 3,200 + 1,500 = 4,700 kg <= Hạn mức an toàn 5,000 kg!
    # Tổng kíp nổ = 1,500 + 1,000 + 500 = 3,000 cái <= Hạn mức an toàn 50,000 cái!
    vln_quants = [
        ('Thuốc Nổ Nhũ Tương Mỏ (Dầu)', 'LOT-TN-2026-01', 3200.0),
        ('Thuốc Nổ ANFO Mỏ Núi Dài', 'LOT-ANFO-2026-02', 1500.0),
        ('Kíp Nổ Vi Sai Phi Điện MS25 (Dây 5m)', 'LOT-KN-MS25-26', 1500.0),
        ('Kíp Nổ Vi Sai Phi Điện MS50 (Dây 7m)', 'LOT-KN-MS50-26', 1000.0),
        ('Kíp Nổ Điện Số 8 Tức Thời', 'LOT-KNE8-26', 500.0),
        ('Dây Nổ Chịu Nước Phi 6 (12g/m)', 'LOT-DN-WP26', 2500.0),
        ('Dây Cháy Chậm An Toàn', 'LOT-DCC-26', 1000.0),
    ]
    for p_name, lot_name, qty in vln_quants:
        prod = products[p_name]
        lot = lots[lot_name]
        q = quant_obj.search([
            ('product_id', '=', prod.id),
            ('location_id', '=', wh_vln.lot_stock_id.id),
            ('lot_id', '=', lot.id),
        ], limit=1)
        if not q:
            quant_obj.create({
                'product_id': prod.id,
                'location_id': wh_vln.lot_stock_id.id,
                'lot_id': lot.id,
                'quantity': qty,
            })
        else:
            q.quantity = qty

    # 7.2 Tồn kho Kho Vật Tư - Phụ Tùng & Dầu Mỡ (KVT/Stock)
    vt_quants = [
        ('Răng Gầu Máy Xúc Komatsu PC450', 24.0),
        ('Lốp Xe Ben Mỏ Howo 12.00R20', 12.0),
        ('Tuy-Ô Thủy Lực Áp Cao 4 Lớp Thép 32mm (L=2.5m)', 15.0),
        ('Dầu Thủy Lực Castrol Hyspin AWS 68 (Phuy 200L)', 1600.0),
        ('Dầu Nhớt Động Cơ Caltex Delo 400 15W-40 (Xô 18L)', 360.0),
        ('Mỡ Bò Bôi Trơn Chịu Nhiệt Sinopec HP-R (Xô 15kg)', 150.0),
        ('Lưới Sàng Đá 1x2 Thép Mangan 65Mn (1.5m x 2m)', 6.0),
        ('Búa Đập Đá Sơ Cấp Trạm Nghiền 250T/h', 8.0),
        ('Con Lăn Băng Tải Mỏ D89x600mm', 30.0),
        ('Bình Ắc Quy GS 12V-150Ah Cho Xe Howo', 6.0),
        ('Vòng Bi Tang Trống SKF 22320 CC/W33', 4.0),
        ('Dây Curoa Trạm Nghiền B120', 20.0),
    ]
    for p_name, qty in vt_quants:
        prod = products[p_name]
        q = quant_obj.search([
            ('product_id', '=', prod.id),
            ('location_id', '=', wh_vt.lot_stock_id.id),
        ], limit=1)
        if not q:
            quant_obj.create({
                'product_id': prod.id,
                'location_id': wh_vt.lot_stock_id.id,
                'quantity': qty,
            })
        else:
            q.quantity = qty

    # 7.3 Tồn kho Kho Đá Thành Phẩm (WH/Stock)
    tp_quants = [
        ('Đá 1x2 (Đá Bê Tông)', 15000.0),
        ('Đá 4x6 (Đá Cấp Phối Móng)', 12000.0),
        ('Đá Base A (Cấp Phối Đắp Nền)', 20000.0),
        ('Đá Mi Bụi (Bột Đá Sàng)', 8000.0),
        ('Đá Hộc Khai Thác Mỏ', 25000.0),
    ]
    for p_name, qty in tp_quants:
        prod = products[p_name]
        q = quant_obj.search([
            ('product_id', '=', prod.id),
            ('location_id', '=', wh_main.lot_stock_id.id),
        ], limit=1)
        if not q:
            quant_obj.create({
                'product_id': prod.id,
                'location_id': wh_main.lot_stock_id.id,
                'quantity': qty,
            })
        else:
            q.quantity = qty

    # -------------------------------------------------------------
    # 8. ĐƠN BÁN HÀNG THEO HỢP ĐỒNG ĐÁ (SALE ORDERS)
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 9. PHIẾU XUẤT / NHẬP KHO THỰC TẾ (STOCK PICKINGS)
    # -------------------------------------------------------------
    picking_obj = env['stock.picking']
    vendor_loc = env.ref('stock.stock_location_suppliers')
    cust_loc = env.ref('stock.stock_location_customers')

    # 9.1 PHIẾU CÂN XE TRẠM CÂN MỎ ĐÁ (KHO THÀNH PHẨM)
    # Phiếu cân xuất bán: Howo 36C-284.91
    existing_p1 = picking_obj.search([('vehicle_plate', '=', '36C-284.91'), ('is_scale_picking', '=', True)], limit=1)
    if not existing_p1:
        p1 = picking_obj.create({
            'picking_type_id': wh_main.out_type_id.id,
            'partner_id': customer_1.id,
            'location_id': wh_main.lot_stock_id.id,
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
                    'uom_id': products['Đá 1x2 (Đá Bê Tông)'].uom_id.id,
                    'location_id': wh_main.lot_stock_id.id,
                    'location_dest_id': customer_1.property_stock_customer.id,
                })
            ]
        })

    # Phiếu cân nhập đá thô moong mỏ: Howo 36C-315.68
    existing_p2 = picking_obj.search([('vehicle_plate', '=', '36C-315.68'), ('is_scale_picking', '=', True)], limit=1)
    if not existing_p2:
        p2 = picking_obj.create({
            'picking_type_id': wh_main.in_type_id.id,
            'is_scale_picking': True,
            'vehicle_plate': '36C-315.68',
            'driver_name': 'Lê Hoàng Long',
            'weigh_scale_number': 'Trạm Cân Số 2',
            'crushing_plant': 'plant_1',
            'tare_weight': 15100.0,
            'gross_weight': 46300.0,
            'density': 1.62,
            'location_id': vendor_loc.id,
            'location_dest_id': wh_main.lot_stock_id.id,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Đá Hộc Khai Thác Mỏ'].id,
                    'product_uom_qty': 31.20,
                    'quantity': 31.20,
                    'uom_id': products['Đá Hộc Khai Thác Mỏ'].uom_id.id,
                    'location_id': vendor_loc.id,
                    'location_dest_id': wh_main.lot_stock_id.id,
                })
            ]
        })

    # 9.2 PHIẾU KHO VẬT LIỆU NỔ CÔNG NGHIỆP (VLNCN)
    supp_gaet = partners['Tổng Công ty Kinh tế Kỹ thuật Công nghiệp Quốc phòng (GAET)']

    # VLN-01: Phiếu Nhập Kho VLNCN từ GAET (Đã hoàn tất)
    existing_vln_in = picking_obj.search([('origin', '=', 'HĐ-VLN-01/2026/GAET')], limit=1)
    if not existing_vln_in:
        p_vln_in = picking_obj.create({
            'picking_type_id': wh_vln.in_type_id.id,
            'partner_id': supp_gaet.id,
            'origin': 'HĐ-VLN-01/2026/GAET',
            'location_id': vendor_loc.id,
            'location_dest_id': wh_vln.lot_stock_id.id,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Thuốc Nổ Nhũ Tương Mỏ (Dầu)'].id,
                    'product_uom_qty': 1000.0,
                    'quantity': 1000.0,
                    'uom_id': uom_kg.id,
                    'location_id': vendor_loc.id,
                    'location_dest_id': wh_vln.lot_stock_id.id,
                }),
                (0, 0, {
                    'product_id': products['Kíp Nổ Vi Sai Phi Điện MS50 (Dây 7m)'].id,
                    'product_uom_qty': 500.0,
                    'quantity': 500.0,
                    'uom_id': uom_unit.id,
                    'location_id': vendor_loc.id,
                    'location_dest_id': wh_vln.lot_stock_id.id,
                }),
            ]
        })
        for m in p_vln_in.move_ids:
            if m.product_id == products['Thuốc Nổ Nhũ Tương Mỏ (Dầu)']:
                if m.move_line_ids:
                    m.move_line_ids[0].lot_id = lots['LOT-TN-2026-01'].id
            elif m.product_id == products['Kíp Nổ Vi Sai Phi Điện MS50 (Dây 7m)']:
                if m.move_line_ids:
                    m.move_line_ids[0].lot_id = lots['LOT-KN-MS50-26'].id

    # VLN-02: Phiếu Xuất Kho VLNCN nổ mìn đợt 1 (Đã hoàn tất)
    existing_vln_out1 = picking_obj.search([('blasting_passport_code', '=', 'HC-NM-2026-03-01')], limit=1)
    if not existing_vln_out1:
        p_vln_out1 = picking_obj.create({
            'picking_type_id': wh_vln.out_type_id.id,
            'origin': 'Phiếu Lĩnh VLNCN Đợt 1 - Tầng Moong +45m',
            'blasting_passport_code': 'HC-NM-2026-03-01',
            'blasting_commander': 'Lê Đình Linh (Chứng chỉ CHTNM-TH-2025)',
            'location_id': wh_vln.lot_stock_id.id,
            'location_dest_id': cust_loc.id,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Thuốc Nổ Nhũ Tương Mỏ (Dầu)'].id,
                    'product_uom_qty': 450.0,
                    'quantity': 450.0,
                    'uom_id': uom_kg.id,
                    'location_id': wh_vln.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
                (0, 0, {
                    'product_id': products['Kíp Nổ Vi Sai Phi Điện MS25 (Dây 5m)'].id,
                    'product_uom_qty': 120.0,
                    'quantity': 120.0,
                    'uom_id': uom_unit.id,
                    'location_id': wh_vln.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
                (0, 0, {
                    'product_id': products['Dây Nổ Chịu Nước Phi 6 (12g/m)'].id,
                    'product_uom_qty': 150.0,
                    'quantity': 150.0,
                    'uom_id': uom_meter.id,
                    'location_id': wh_vln.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
            ]
        })
        for m in p_vln_out1.move_ids:
            if m.product_id == products['Thuốc Nổ Nhũ Tương Mỏ (Dầu)']:
                if m.move_line_ids:
                    m.move_line_ids[0].lot_id = lots['LOT-TN-2026-01'].id
            elif m.product_id == products['Kíp Nổ Vi Sai Phi Điện MS25 (Dây 5m)']:
                if m.move_line_ids:
                    m.move_line_ids[0].lot_id = lots['LOT-KN-MS25-26'].id
            elif m.product_id == products['Dây Nổ Chịu Nước Phi 6 (12g/m)']:
                if m.move_line_ids:
                    m.move_line_ids[0].lot_id = lots['LOT-DN-WP26'].id

    # VLN-03: Phiếu Xuất Kho VLNCN nổ mìn đợt 2 bạt taluy (Sẵn sàng - Chờ bấm xuất)
    existing_vln_out2 = picking_obj.search([('blasting_passport_code', '=', 'HC-NM-2026-03-02')], limit=1)
    if not existing_vln_out2:
        p_vln_out2 = picking_obj.create({
            'picking_type_id': wh_vln.out_type_id.id,
            'origin': 'Phiếu Lĩnh VLNCN Đợt 2 - Bạt Taluy Mức +30m',
            'blasting_passport_code': 'HC-NM-2026-03-02',
            'blasting_commander': 'Lê Đình Linh (Chứng chỉ CHTNM-TH-2025)',
            'location_id': wh_vln.lot_stock_id.id,
            'location_dest_id': cust_loc.id,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Thuốc Nổ ANFO Mỏ Núi Dài'].id,
                    'product_uom_qty': 380.0,
                    'quantity': 380.0,
                    'uom_id': uom_kg.id,
                    'location_id': wh_vln.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
                (0, 0, {
                    'product_id': products['Kíp Nổ Vi Sai Phi Điện MS50 (Dây 7m)'].id,
                    'product_uom_qty': 80.0,
                    'quantity': 80.0,
                    'uom_id': uom_unit.id,
                    'location_id': wh_vln.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
                (0, 0, {
                    'product_id': products['Dây Nổ Chịu Nước Phi 6 (12g/m)'].id,
                    'product_uom_qty': 100.0,
                    'quantity': 100.0,
                    'uom_id': uom_meter.id,
                    'location_id': wh_vln.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
            ]
        })
        for m in p_vln_out2.move_ids:
            if m.product_id == products['Thuốc Nổ ANFO Mỏ Núi Dài']:
                if m.move_line_ids:
                    m.move_line_ids[0].lot_id = lots['LOT-ANFO-2026-02'].id
            elif m.product_id == products['Kíp Nổ Vi Sai Phi Điện MS50 (Dây 7m)']:
                if m.move_line_ids:
                    m.move_line_ids[0].lot_id = lots['LOT-KN-MS50-26'].id
            elif m.product_id == products['Dây Nổ Chịu Nước Phi 6 (12g/m)']:
                if m.move_line_ids:
                    m.move_line_ids[0].lot_id = lots['LOT-DN-WP26'].id

    # 9.3 PHIẾU XUẤT CẤP VẬT TƯ, PHỤ TÙNG CƠ GIỚI MỎ (GẮN ĐÍCH DANH THIẾT BỊ - BR-10)
    # VT-01: Xuất phụ tùng cho Máy xúc Komatsu PC450 (EX-01)
    existing_vt_ex01 = picking_obj.search([('origin', '=', 'XK-VT/2026/EX-01')], limit=1)
    if not existing_vt_ex01:
        picking_obj.create({
            'picking_type_id': wh_vt.out_type_id.id,
            'origin': 'XK-VT/2026/EX-01',
            'equipment_id': equipments['EX-01'].id,
            'location_id': wh_vt.lot_stock_id.id,
            'location_dest_id': cust_loc.id,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Răng Gầu Máy Xúc Komatsu PC450'].id,
                    'product_uom_qty': 4.0,
                    'quantity': 4.0,
                    'uom_id': uom_unit.id,
                    'location_id': wh_vt.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
                (0, 0, {
                    'product_id': products['Mỡ Bò Bôi Trơn Chịu Nhiệt Sinopec HP-R (Xô 15kg)'].id,
                    'product_uom_qty': 15.0,
                    'quantity': 15.0,
                    'uom_id': uom_kg.id,
                    'location_id': wh_vt.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
            ]
        })

    # VT-02: Xuất phụ tùng khắc phục sự cố bục tuy-ô Máy xúc Hitachi (EX-02)
    existing_vt_ex02 = picking_obj.search([('origin', '=', 'XK-VT/2026/EX-02')], limit=1)
    if not existing_vt_ex02:
        picking_obj.create({
            'picking_type_id': wh_vt.out_type_id.id,
            'origin': 'XK-VT/2026/EX-02',
            'equipment_id': equipments['EX-02'].id,
            'location_id': wh_vt.lot_stock_id.id,
            'location_dest_id': cust_loc.id,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Tuy-Ô Thủy Lực Áp Cao 4 Lớp Thép 32mm (L=2.5m)'].id,
                    'product_uom_qty': 1.0,
                    'quantity': 1.0,
                    'uom_id': uom_unit.id,
                    'location_id': wh_vt.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
                (0, 0, {
                    'product_id': products['Dầu Thủy Lực Castrol Hyspin AWS 68 (Phuy 200L)'].id,
                    'product_uom_qty': 40.0,
                    'quantity': 40.0,
                    'uom_id': uom_liter.id,
                    'location_id': wh_vt.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
            ]
        })

    # VT-03: Xuất 2 quả lốp cho Xe ben Howo 36C-284.91
    existing_vt_howo = picking_obj.search([('origin', '=', 'XK-VT/2026/36C-284.91')], limit=1)
    if not existing_vt_howo:
        picking_obj.create({
            'picking_type_id': wh_vt.out_type_id.id,
            'origin': 'XK-VT/2026/36C-284.91',
            'equipment_id': equipments['36C-284.91'].id,
            'location_id': wh_vt.lot_stock_id.id,
            'location_dest_id': cust_loc.id,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Lốp Xe Ben Mỏ Howo 12.00R20'].id,
                    'product_uom_qty': 2.0,
                    'quantity': 2.0,
                    'uom_id': uom_unit.id,
                    'location_id': wh_vt.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
            ]
        })

    # VT-04: Xuất lưới sàng đá & con lăn cho Trạm nghiền CRUSH-01
    existing_vt_crush = picking_obj.search([('origin', '=', 'XK-VT/2026/CRUSH-01')], limit=1)
    if not existing_vt_crush:
        picking_obj.create({
            'picking_type_id': wh_vt.out_type_id.id,
            'origin': 'XK-VT/2026/CRUSH-01',
            'equipment_id': equipments['CRUSH-01'].id,
            'location_id': wh_vt.lot_stock_id.id,
            'location_dest_id': cust_loc.id,
            'move_ids': [
                (0, 0, {
                    'product_id': products['Lưới Sàng Đá 1x2 Thép Mangan 65Mn (1.5m x 2m)'].id,
                    'product_uom_qty': 2.0,
                    'quantity': 2.0,
                    'uom_id': uom_unit.id,
                    'location_id': wh_vt.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
                (0, 0, {
                    'product_id': products['Con Lăn Băng Tải Mỏ D89x600mm'].id,
                    'product_uom_qty': 4.0,
                    'quantity': 4.0,
                    'uom_id': uom_unit.id,
                    'location_id': wh_vt.lot_stock_id.id,
                    'location_dest_id': cust_loc.id,
                }),
            ]
        })

    # -------------------------------------------------------------
    # 10. ĐƠN MUA HÀNG (PURCHASE ORDERS) - PHÂN CẤP DUYỆT BR-03
    # -------------------------------------------------------------
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
                    'price_unit': 1450000.0,
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
                    'price_unit': 7500000.0,
                })
            ]
        })

    # -------------------------------------------------------------
    # 11. YÊU CẦU BẢO TRÌ SỰ CỐ DỪNG MÁY & NGHIỆM THU 3 BÊN (BR-04, BR-07)
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 12. NHẬT KÝ CẤP DẦU & ĐỐI SOÁT TIÊU HAO CẢNH BÁO > 10% (BR-08)
    # -------------------------------------------------------------
    fuel_log_obj = env['hoangphuc.fuel.log']
    
    # Log 1: Máy xúc EX-01 (Tiêu hao bình thường)
    existing_fl1 = fuel_log_obj.search([('equipment_id', '=', equipments['EX-01'].id)], limit=1)
    if not existing_fl1:
        fuel_log_obj.create({
            'equipment_id': equipments['EX-01'].id,
            'log_date': fields.Date.today(),
            'driver_name': 'Trần Văn Quyết',
            'previous_meter': 1420.0,
            'current_meter': 1430.0,
            'fuel_liters': 320.0,
            'fuel_station': 'Téc Dầu Kho Mỏ Núi Dài',
        })

    # Log 2: Xe ben 36C-315.68 (Cảnh báo đỏ vượt > 10% - BR-08)
    existing_fl2 = fuel_log_obj.search([('equipment_id', '=', equipments['36C-315.68'].id)], limit=1)
    if not existing_fl2:
        fuel_log_obj.create({
            'equipment_id': equipments['36C-315.68'].id,
            'log_date': fields.Date.today(),
            'driver_name': 'Lê Hoàng Long',
            'previous_meter': 2100.0,
            'current_meter': 2110.0,
            'fuel_liters': 245.0,
            'fuel_station': 'Xe Bồn Cấp Dầu Lưu Động Bãi Moong',
            'technical_explanation': 'Đường vận chuyển từ moong sâu lên bãi sàng bị sình lầy do mưa đêm, xe phải gài 2 cầu chạy số 1 liên tục làm tăng tiêu hao nhiên liệu (BR-08).',
        })
    # -------------------------------------------------------------
    # 13. SẢN XUẤT TRỰC TIẾP MỎ ĐÁ & TRẠM NGHIỀN SÀNG (MRP / SXTT)
    # -------------------------------------------------------------
    bom_obj = env['mrp.bom']
    prod_stone_1x2 = products['Đá 1x2 (Đá Bê Tông)']
    prod_stone_raw = products['Đá Hộc Khai Thác Mỏ']
    prod_stone_4x6 = products['Đá 4x6 (Đá Cấp Phối Móng)']

    # 13.1 Định mức sản xuất (BOM) Đá 1x2 từ Đá Hộc moong mỏ
    bom_1x2 = bom_obj.search([('product_tmpl_id', '=', prod_stone_1x2.product_tmpl_id.id)], limit=1)
    if not bom_1x2:
        bom_1x2 = bom_obj.create({
            'product_tmpl_id': prod_stone_1x2.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': prod_stone_raw.id,
                    'product_qty': 1.10,  # 1.1 tấn đá hộc ra 1.0 tấn đá 1x2 (hao hụt 10% ra mạt đá)
                })
            ]
        })

    # 13.2 Định mức sản xuất (BOM) Đá 4x6 từ Đá Hộc moong mỏ
    bom_4x6 = bom_obj.search([('product_tmpl_id', '=', prod_stone_4x6.product_tmpl_id.id)], limit=1)
    if not bom_4x6:
        bom_4x6 = bom_obj.create({
            'product_tmpl_id': prod_stone_4x6.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': prod_stone_raw.id,
                    'product_qty': 1.05,
                })
            ]
        })

    # 13.3 Lệnh sản xuất (MO)
    mo_obj = env['mrp.production']
    
    # MO 1: Đã hoàn tất trong ca sáng (Ca 1: 06:00 - 14:00) - Có dừng máy 25 phút giải trình (BR-04)
    existing_mo1 = mo_obj.search([('crushing_plant', '=', 'plant_1'), ('production_shift', '=', 'shift_1')], limit=1)
    if not existing_mo1:
        mo1 = mo_obj.create({
            'product_id': prod_stone_1x2.id,
            'product_qty': 300.0,
            'bom_id': bom_1x2.id,
            'crushing_plant': 'plant_1',
            'production_shift': 'shift_1',
            'operator_name': 'Lê Hoàng Long',
            'safety_checked': True,
            'safety_inspector': 'Nguyễn Văn An (Giám sát An toàn Mỏ)',
            'quarry_pit_location': 'Moong Khai Thác Mỏ Núi Dài - Tầng Mức +45m',
            'vehicle_trips_count': 16,
            'raw_stone_input_qty': 330.0,
            'quarry_stock_yard': 'Bãi Thành Phẩm Đá 1x2 - Moong Chính Cạnh Trạm Cân Số 1',
            'operating_hours': 7.5,
            'downtime_ids': [(0, 0, {
                'date_start': fields.Datetime.now() - datetime.timedelta(hours=4),
                'date_end': fields.Datetime.now() - datetime.timedelta(hours=3, minutes=35),
                'duration_minutes': 25,
                'cause': 'jam',
                'explanation': 'Đá tảng quá cỡ >800mm từ xe Howo đổ vào làm kẹt miệng hàm nghiền sơ cấp C106. Kíp vận hành đã ngắt điện an toàn, dùng búa đập vỡ đá tảng và thông phễu cấp liệu mất 25 phút (BR-04).',
            })],
        })
        mo1.action_confirm()
        mo1.qty_producing = 300.0
        for move in mo1.move_raw_ids:
            move.quantity = 330.0
        mo1.button_mark_done()

    # MO 2: Lệnh sản xuất đang chạy trong ca chiều (Ca 2: 14:00 - 22:00) - Sẵn sàng cho demo
    existing_mo2 = mo_obj.search([('crushing_plant', '=', 'plant_1'), ('production_shift', '=', 'shift_2')], limit=1)
    if not existing_mo2:
        mo2 = mo_obj.create({
            'product_id': prod_stone_1x2.id,
            'product_qty': 200.0,
            'bom_id': bom_1x2.id,
            'crushing_plant': 'plant_1',
            'production_shift': 'shift_2',
            'operator_name': 'Trần Văn Cường',
            'safety_checked': True,
            'safety_inspector': 'Nguyễn Văn An (Giám sát An toàn Mỏ)',
            'quarry_pit_location': 'Moong Khai Thác Mỏ Núi Dài - Tầng Mức +45m',
            'vehicle_trips_count': 11,
            'raw_stone_input_qty': 220.0,
            'quarry_stock_yard': 'Bãi Thành Phẩm Đá 1x2 - Moong Chính Cạnh Trạm Cân Số 1',
            'operating_hours': 4.0,
        })
        mo2.action_confirm()

    # Đồng bộ / cập nhật phiếu nhập kho bãi thành phẩm cho các lệnh sản xuất
    for mo in (existing_mo1 or mo1) | (existing_mo2 or mo2):
        if hasattr(mo, '_create_or_update_finished_picking'):
            mo._create_or_update_finished_picking()

    print("SUCCESS: Hoang Phuc demo data (Warehouses, VLNCN Lots, Quants, Equipment Spare Parts, MRP Crushing) populated successfully!")

