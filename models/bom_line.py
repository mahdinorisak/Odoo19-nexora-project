from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraBomLine(models.Model):
    _name = 'nexora.bom.line'
    _description = 'Nexora BOM Line'
    _order = 'bom_id, id'

    bom_id = fields.Many2one('nexora.bom', string='BOM', required=True,
                             ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='bom_id.currency_id')
    component_id = fields.Many2one('nexora.product', string='Component', required=True)
    quantity = fields.Float(default=1.0, required=True)
    cost = fields.Monetary(compute='_compute_cost', currency_field='currency_id')

    @api.depends('quantity', 'component_id.cost_price')
    def _compute_cost(self):
        for line in self:
            line.cost = line.quantity * line.component_id.cost_price

    @api.constrains('quantity', 'component_id')
    def _check_line(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError("Component quantity must be greater than zero.")
            if line.component_id == line.bom_id.product_id:
                raise ValidationError("A product cannot be a component of itself.")
