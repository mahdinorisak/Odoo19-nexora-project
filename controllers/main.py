from odoo import http
from odoo.http import request


class NexoraController(http.Controller):

    @staticmethod
    def _product_data(product):
        return {
            'code': product.code,
            'name': product.name,
            'sale_price': product.sale_price,
            'qty_available': product.qty_available,
            'min_quantity': product.min_quantity,
            'low_stock': product.low_stock,
        }

    @http.route('/nexora/api/stock', type='http', auth='user', methods=['GET'])
    def stock_list(self, **kwargs):
        products = request.env['nexora.product'].search([])
        return request.make_json_response(
            [self._product_data(p) for p in products])

    @http.route('/nexora/api/stock/<string:code>', type='http', auth='user',
                methods=['GET'])
    def stock_one(self, code, **kwargs):
        product = request.env['nexora.product'].search(
            [('code', '=', code)], limit=1)
        if not product:
            return request.make_json_response(
                {'error': 'Product not found', 'code': code}, status=404)
        return request.make_json_response(self._product_data(product))
