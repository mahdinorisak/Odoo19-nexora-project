from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraProductVariant(models.Model):
    _name = 'nexora.product.variant'
    _description = 'Nexora Product Variant'
    _order = 'product_id, name'

    name = fields.Char(compute='_compute_name', store=True)
    product_id = fields.Many2one('nexora.product', string='Product', required=True,
                                 ondelete='cascade')
    size = fields.Char()
    color = fields.Char()
    sku = fields.Char(string='SKU', copy=False)
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    extra_price = fields.Monetary(currency_field='currency_id')
    final_price = fields.Monetary(compute='_compute_final_price',
                                  currency_field='currency_id')
    active = fields.Boolean(default=True)

    @api.depends('product_id.name', 'size', 'color')
    def _compute_name(self):
        for variant in self:
            parts = [p for p in (variant.size, variant.color) if p]
            base = variant.product_id.name or ''
            variant.name = '%s (%s)' % (base, ' / '.join(parts)) if parts else base

    @api.depends('product_id.sale_price', 'extra_price')
    def _compute_final_price(self):
        for variant in self:
            variant.final_price = variant.product_id.sale_price + variant.extra_price

    @api.constrains('size', 'color')
    def _check_attributes(self):
        for variant in self:
            if not variant.size and not variant.color:
                raise ValidationError("A variant needs a size or a color.")

    @api.constrains('product_id', 'size', 'color')
    def _check_unique_combination(self):
        for variant in self:
            if self.with_context(active_test=False).search_count([
                    ('product_id', '=', variant.product_id.id),
                    ('size', '=', variant.size),
                    ('color', '=', variant.color),
                    ('id', '!=', variant.id)]):
                raise ValidationError("This size and color already exists for the product.")

    @api.constrains('sku')
    def _check_sku_unique(self):
        for variant in self:
            if variant.sku and self.with_context(active_test=False).search_count(
                    [('sku', '=', variant.sku), ('id', '!=', variant.id)]):
                raise ValidationError("SKU must be unique.")


class NexoraProduct(models.Model):
    _inherit = 'nexora.product'

    variant_ids = fields.One2many('nexora.product.variant', 'product_id',
                                  string='Variants')
    variant_count = fields.Integer(compute='_compute_variant_count')

    @api.depends('variant_ids')
    def _compute_variant_count(self):
        for product in self:
            product.variant_count = len(product.variant_ids)
