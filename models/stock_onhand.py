from odoo import fields, models


class NexoraStockOnHand(models.Model):
    _name = 'nexora.stock.onhand'
    _description = 'Stock On Hand by Location'
    _auto = False
    _order = 'product_id, location_id'

    product_id = fields.Many2one('nexora.product', string='Product', readonly=True)
    location_id = fields.Many2one('nexora.location', string='Location', readonly=True)
    quantity = fields.Float(string='On Hand', readonly=True)

    def init(self):
        cr = self.env.cr
        cr.execute("DROP VIEW IF EXISTS %s CASCADE" % self._table)
        cr.execute("""
            CREATE VIEW %s AS (
                SELECT row_number() OVER (ORDER BY q.product_id, q.location_id) AS id,
                       q.product_id,
                       q.location_id,
                       SUM(q.quantity) AS quantity
                FROM (
                    SELECT m.product_id, m.location_dest_id AS location_id, m.quantity
                    FROM nexora_stock_move m
                    JOIN nexora_location l ON l.id = m.location_dest_id
                    WHERE m.state = 'done' AND l.usage = 'internal'
                    UNION ALL
                    SELECT m.product_id, m.location_src_id AS location_id, -m.quantity
                    FROM nexora_stock_move m
                    JOIN nexora_location l ON l.id = m.location_src_id
                    WHERE m.state = 'done' AND l.usage = 'internal'
                ) q
                GROUP BY q.product_id, q.location_id
                HAVING SUM(q.quantity) <> 0
            )
        """ % self._table)
