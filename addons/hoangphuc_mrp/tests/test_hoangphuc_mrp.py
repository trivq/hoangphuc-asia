from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
from odoo import fields
import datetime

@tagged('post_install', '-at_install')
class TestHoangPhucMrp(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_stone_raw = cls.env['product.product'].create({
            'name': 'Đá Nguyên Khai Moong Mỏ',
            'is_storable': True,
            'is_quarry_stone': True,
        })
        cls.product_stone_1x2 = cls.env['product.product'].create({
            'name': 'Đá Thành Phẩm 1x2',
            'is_storable': True,
            'is_quarry_stone': True,
            'density': 1.6,
        })

        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_stone_1x2.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.product_stone_raw.id,
                    'product_qty': 1.1,
                }),
            ],
        })

    def test_br02_safety_check(self):
        """Kiểm tra quy tắc BR-02: Bắt buộc kiểm tra an toàn đầu ca trước khi phát lệnh."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_stone_1x2.id,
            'product_qty': 100.0,
            'bom_id': self.bom.id,
            'safety_checked': False,
        })
        with self.assertRaises(UserError):
            mo.action_confirm()

        mo.safety_checked = True
        mo.action_confirm()
        self.assertEqual(mo.state, 'confirmed')

    def test_br04_downtime_explanation(self):
        """Kiểm tra quy tắc BR-04: Dừng máy >= 10 phút bắt buộc phải có giải trình kỹ thuật."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_stone_1x2.id,
            'product_qty': 50.0,
            'bom_id': self.bom.id,
            'safety_checked': True,
        })
        mo.action_confirm()
        mo.qty_producing = 50.0

        # Thêm lượt dừng máy 15 phút chưa có giải trình
        downtime = self.env['mrp.production.downtime'].create({
            'production_id': mo.id,
            'date_start': fields.Datetime.now() - datetime.timedelta(minutes=30),
            'date_end': fields.Datetime.now() - datetime.timedelta(minutes=15),
            'duration_minutes': 15,
            'cause': 'jam',
            'explanation': '',
        })
        self.assertEqual(mo.downtime_minutes, 15)

        # Chốt sản xuất khi chưa giải trình -> Phải báo lỗi
        with self.assertRaises(UserError):
            mo.button_mark_done()

        # Bổ sung giải trình kỹ thuật -> Chốt thành công
        downtime.explanation = 'Kẹt phễu cấp liệu do đá tảng >800mm, đã xử lý an toàn.'
        for move in mo.move_raw_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

    def test_downtime_minutes_sum(self):
        """Kiểm tra tính tổng thời gian dừng máy từ nhiều lượt dừng máy."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_stone_1x2.id,
            'product_qty': 20.0,
            'bom_id': self.bom.id,
            'safety_checked': True,
        })
        self.env['mrp.production.downtime'].create([
            {
                'production_id': mo.id,
                'duration_minutes': 5,
                'cause': 'weather',
            },
            {
                'production_id': mo.id,
                'duration_minutes': 8,
                'cause': 'electrical',
            },
        ])
        self.assertEqual(mo.downtime_minutes, 13)

    def test_quarry_finished_picking_and_smart_button(self):
        """Kiểm tra phiếu nhập kho bãi thành phẩm mỏ đá và smart button Transfers."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_stone_1x2.id,
            'product_qty': 100.0,
            'bom_id': self.bom.id,
            'safety_checked': True,
            'crushing_plant': 'plant_1',
            'raw_stone_input_qty': 110.0,
        })
        mo.action_confirm()
        # Đảm bảo picking scale được tạo và liên kết
        self.assertTrue(mo.picking_ids)
        scale_picking = mo.picking_ids.filtered(lambda p: p.is_scale_picking)
        self.assertTrue(scale_picking)
        self.assertEqual(mo.delivery_count, len(mo.picking_ids))

        # Kiểm tra gọi action_view_mo_delivery
        action = mo.action_view_mo_delivery()
        self.assertTrue(action)

    def test_copy_data_does_not_force_done(self):
        """Kiểm tra sao chép lệnh sản xuất không kế thừa picking_id làm trạng thái copy bị done."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_stone_1x2.id,
            'product_qty': 100.0,
            'bom_id': self.bom.id,
            'safety_checked': True,
        })
        mo.action_confirm()
        mo.qty_producing = 100.0
        for move in mo.move_raw_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

        # Sao chép MO đã hoàn tất
        mo_copy = mo.copy()
        self.assertEqual(mo_copy.state, 'draft')
        for move in mo_copy.move_finished_ids:
            self.assertFalse(move.picking_id)
            self.assertEqual(move.state, 'draft')

    def test_action_quick_fill_scale_input(self):
        """Kiểm tra chức năng áp khối lượng cấp liệu vào nguyên liệu tiêu hao."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_stone_1x2.id,
            'product_qty': 50.0,
            'bom_id': self.bom.id,
            'safety_checked': True,
            'raw_stone_input_qty': 55.0,
        })
        mo.action_confirm()
        mo.action_quick_fill_scale_input()
        for raw_move in mo.move_raw_ids:
            self.assertEqual(raw_move.quantity, 55.0)
