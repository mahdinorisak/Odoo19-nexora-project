import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class NexoraProduct(models.Model):
    _name = 'nexora.product'
    _description = 'Nexora Product'
    _inherit = ['mail.thread', 'image.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(copy=False)
    category_id = fields.Many2one('nexora.product.category', string='Category')
    product_type_id = fields.Many2one('nexora.product.type', string='Product Type')
    material_id = fields.Many2one('nexora.material', string='Main Material')
    printing_type_ids = fields.Many2many('nexora.printing.type', string='Printing Types')
    description = fields.Text()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    cost_price = fields.Monetary(currency_field='currency_id')
    sale_price = fields.Monetary(currency_field='currency_id', tracking=True)
    margin = fields.Monetary(compute='_compute_margin', store=True,
                             currency_field='currency_id')
    min_quantity = fields.Float(string='Minimum Quantity')
    qty_available = fields.Float(string='On Hand', compute='_compute_qty_available')
    low_stock = fields.Boolean(compute='_compute_qty_available')
    active = fields.Boolean(default=True)

    @api.depends('cost_price', 'sale_price')
    def _compute_margin(self):
        for product in self:
            product.margin = product.sale_price - product.cost_price

    def _compute_qty_available(self):
        Move = self.env['nexora.stock.move']
        for product in self:
            qty = 0.0
            if product.id:
                domain = [('product_id', '=', product.id), ('state', '=', 'done')]
                incoming = Move.search(domain + [('location_dest_id.usage', '=', 'internal')])
                outgoing = Move.search(domain + [('location_src_id.usage', '=', 'internal')])
                qty = sum(incoming.mapped('quantity')) - sum(outgoing.mapped('quantity'))
            product.qty_available = qty
            product.low_stock = qty < product.min_quantity

    @api.constrains('cost_price', 'sale_price')
    def _check_prices(self):
        for product in self:
            if product.cost_price < 0 or product.sale_price < 0:
                raise ValidationError("Prices cannot be negative.")

    @api.constrains('code')
    def _check_code_unique(self):
        for product in self:
            if product.code and self.search_count(
                    [('code', '=', product.code), ('id', '!=', product.id)]):
                raise ValidationError("Product code must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('nexora.product')
        return super().create(vals_list)

    @api.model
    def _cron_check_low_stock(self):
        products = self.search([('min_quantity', '>', 0)]).filtered('low_stock')
        for product in products:
            product.message_post(body="Low stock: %s on hand, minimum is %s." % (
                product.qty_available, product.min_quantity))
        _logger.info("Low stock check: %s product(s) below minimum.", len(products))
        return True
