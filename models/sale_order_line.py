from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraSaleOrderLine(models.Model):
    _name = 'nexora.sale.order.line'
    _description = 'Nexora Sale Order Line'
    _order = 'order_id, id'

    order_id = fields.Many2one('nexora.sale.order', string='Order',
                               required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id')
    product_id = fields.Many2one('nexora.product', string='Product', required=True)
    description = fields.Char(compute='_compute_description', store=True,
                              readonly=False, precompute=True)
    quantity = fields.Float(default=1.0)
    unit_price = fields.Monetary(compute='_compute_unit_price', store=True,
                                 readonly=False, precompute=True,
                                 currency_field='currency_id')
    printing_type_id = fields.Many2one('nexora.printing.type', string='Printing')
    printing_option_id = fields.Many2one('nexora.printing.option', string='Printing Option')
    extra_price = fields.Monetary(related='printing_option_id.extra_price',
                                  currency_field='currency_id')
    discount = fields.Float(string='Discount (%)')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True,
                               currency_field='currency_id')

    @api.depends('product_id')
    def _compute_description(self):
        for line in self:
            line.description = line.product_id.name or ''

    @api.depends('product_id')
    def _compute_unit_price(self):
        for line in self:
            line.unit_price = line.product_id.sale_price

    @api.depends('quantity', 'unit_price', 'discount', 'printing_option_id.extra_price')
    def _compute_subtotal(self):
        for line in self:
            price = line.unit_price + line.printing_option_id.extra_price
            line.subtotal = line.quantity * price * (1 - line.discount / 100.0)

    @api.onchange('printing_type_id')
    def _onchange_printing_type_id(self):
        if self.printing_option_id.printing_type_id != self.printing_type_id:
            self.printing_option_id = False

    @api.constrains('quantity', 'discount')
    def _check_values(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            if not 0 <= line.discount <= 100:
                raise ValidationError("Discount must be between 0 and 100.")

    @api.constrains('printing_type_id', 'printing_option_id')
    def _check_printing(self):
        for line in self:
            option = line.printing_option_id
            if option and option.printing_type_id != line.printing_type_id:
                raise ValidationError("The printing option does not belong to the selected printing type.")
