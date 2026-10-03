from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestNexora(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Product = cls.env['nexora.product']
        cls.customer = cls.env['nexora.customer'].create({'name': 'Test Customer'})
        cls.vendor = cls.env['nexora.vendor'].create({'name': 'Test Vendor'})
        cls.chair = Product.create({'name': 'Test Chair', 'cost_price': 50,
                                    'sale_price': 100})
        cls.plank = Product.create({'name': 'Test Plank', 'cost_price': 5,
                                    'sale_price': 8})
        cls.stock = cls.env.ref('nexora_app.location_stock')
        cls.vendors = cls.env.ref('nexora_app.location_vendors')
        cls.customers = cls.env.ref('nexora_app.location_customers')

    def _move(self, product, qty, src, dest):
        move = self.env['nexora.stock.move'].create({
            'product_id': product.id,
            'quantity': qty,
            'location_src_id': src.id,
            'location_dest_id': dest.id,
        })
        move.action_done()
        return move

    def _sale_order(self):
        return self.env['nexora.sale.order'].create({
            'customer_id': self.customer.id,
            'tax_rate': 10,
            'line_ids': [(0, 0, {'product_id': self.chair.id,
                                 'quantity': 2, 'discount': 10})],
        })

    # Products
    def test_product_code_and_margin(self):
        self.assertTrue(self.chair.code.startswith('PRD-'))
        self.assertEqual(self.chair.margin, 50)

    def test_negative_price_is_blocked(self):
        with self.assertRaises(ValidationError):
            self.env['nexora.product'].create({'name': 'Bad', 'cost_price': -1})

    def test_product_code_must_be_unique(self):
        with self.assertRaises(ValidationError):
            self.env['nexora.product'].create(
                {'name': 'Copy', 'code': self.chair.code})

    # Sales
    def test_sale_order_totals(self):
        order = self._sale_order()
        line = order.line_ids
        self.assertEqual(line.unit_price, 100)
        self.assertAlmostEqual(line.subtotal, 180)
        self.assertAlmostEqual(order.amount_untaxed, 180)
        self.assertAlmostEqual(order.amount_tax, 18)
        self.assertAlmostEqual(order.amount_total, 198)
        self.assertTrue(order.name.startswith('SO-'))

    def test_confirm_needs_lines(self):
        order = self.env['nexora.sale.order'].create(
            {'customer_id': self.customer.id})
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_confirmed_order_cannot_be_deleted(self):
        order = self._sale_order()
        order.action_confirm()
        self.assertEqual(order.state, 'confirmed')
        with self.assertRaises(UserError):
            order.unlink()

    # Purchasing and stock
    def test_receiving_a_purchase_creates_stock(self):
        po = self.env['nexora.purchase.order'].create({
            'vendor_id': self.vendor.id,
            'line_ids': [(0, 0, {'product_id': self.plank.id, 'quantity': 10})],
        })
        po.action_confirm()
        po.action_receive()
        self.plank.invalidate_recordset()
        self.assertEqual(po.state, 'received')
        self.assertEqual(self.plank.qty_available, 10)

    def test_cannot_move_more_than_on_hand(self):
        self._move(self.plank, 5, self.vendors, self.stock)
        with self.assertRaises(UserError):
            self._move(self.plank, 50, self.stock, self.customers)

    def test_low_stock_flag_and_cron(self):
        self.plank.min_quantity = 10
        self.plank.invalidate_recordset()
        self.assertTrue(self.plank.low_stock)
        self.assertTrue(self.env['nexora.product']._cron_check_low_stock())

    # Manufacturing
    def test_manufacturing_flow(self):
        bom = self.env['nexora.bom'].create({
            'product_id': self.chair.id,
            'quantity': 1,
            'line_ids': [(0, 0, {'component_id': self.plank.id, 'quantity': 2})],
        })
        self._move(self.plank, 10, self.vendors, self.stock)
        mo = self.env['nexora.manufacturing.order'].create(
            {'product_id': self.chair.id, 'quantity': 3})
        self.assertEqual(mo.bom_id, bom)
        mo.action_confirm()
        self.assertEqual(mo.line_ids.quantity, 6)
        mo.action_start()
        mo.action_done()
        (self.plank | self.chair).invalidate_recordset()
        self.assertEqual(mo.state, 'done')
        self.assertEqual(self.plank.qty_available, 4)
        self.assertEqual(self.chair.qty_available, 3)

    def test_manufacturing_shortage(self):
        self.env['nexora.bom'].create({
            'product_id': self.chair.id,
            'quantity': 1,
            'line_ids': [(0, 0, {'component_id': self.plank.id, 'quantity': 2})],
        })
        mo = self.env['nexora.manufacturing.order'].create(
            {'product_id': self.chair.id, 'quantity': 50})
        mo.action_confirm()
        with self.assertRaises(UserError):
            mo.action_start()
