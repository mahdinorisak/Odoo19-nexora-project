from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraPurchaseRequestLine(models.Model):
    _name = 'nexora.purchase.request.line'
    _description = 'Nexora Purchase Request Line'
    _order = 'request_id, id'

    request_id = fields.Many2one('nexora.purchase.request', string='Request',
                                 required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='request_id.currency_id')
    product_id = fields.Many2one('nexora.product', string='Product / Material',
                                 required=True)
    description = fields.Char(compute='_compute_description', store=True,
                              readonly=False, precompute=True)
    quantity = fields.Float(default=1.0)
    estimated_cost = fields.Monetary(compute='_compute_estimated_cost', store=True,
                                     readonly=False, precompute=True,
                                     currency_field='currency_id')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True,
                               currency_field='currency_id')

    @api.depends('product_id')
    def _compute_description(self):
        for line in self:
            line.description = line.product_id.name or ''

    @api.depends('product_id')
    def _compute_estimated_cost(self):
        for line in self:
            line.estimated_cost = line.product_id.cost_price

    @api.depends('quantity', 'estimated_cost')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.estimated_cost

    @api.constrains('quantity', 'estimated_cost')
    def _check_values(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            if line.estimated_cost < 0:
                raise ValidationError("Estimated cost cannot be negative.")
