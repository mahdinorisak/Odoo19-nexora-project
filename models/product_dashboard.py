from odoo import fields, models


class NexoraProduct(models.Model):
    _inherit = 'nexora.product'

    low_stock = fields.Boolean(search='_search_low_stock')

    def _search_low_stock(self, operator, value):
        products = self.search([('min_quantity', '>', 0)])
        products.invalidate_recordset(['qty_available', 'low_stock'])
        low = products.filtered('low_stock')
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', low.ids)]
        return [('id', 'not in', low.ids)]
