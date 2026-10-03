from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraBom(models.Model):
    _name = 'nexora.bom'
    _description = 'Nexora Bill of Materials'
    _order = 'name'

    name = fields.Char(compute='_compute_name', store=True)
    code = fields.Char(string='Reference')
    product_id = fields.Many2one('nexora.product', string='Finished Product',
                                 required=True)
    quantity = fields.Float(string='Produced Quantity', default=1.0, required=True)
    line_ids = fields.One2many('nexora.bom.line', 'bom_id', string='Components')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    component_cost = fields.Monetary(compute='_compute_component_cost',
                                     currency_field='currency_id')
    active = fields.Boolean(default=True)

    @api.depends('product_id.name', 'code')
    def _compute_name(self):
        for bom in self:
            name = bom.product_id.name or 'New BOM'
            bom.name = '[%s] %s' % (bom.code, name) if bom.code else name

    @api.depends('line_ids.cost', 'quantity')
    def _compute_component_cost(self):
        for bom in self:
            total = sum(bom.line_ids.mapped('cost'))
            bom.component_cost = total / bom.quantity if bom.quantity else 0.0

    @api.constrains('quantity')
    def _check_quantity(self):
        for bom in self:
            if bom.quantity <= 0:
                raise ValidationError("Produced quantity must be greater than zero.")
