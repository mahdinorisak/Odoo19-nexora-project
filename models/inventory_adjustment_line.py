from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraInventoryAdjustmentLine(models.Model):
    _name = 'nexora.inventory.adjustment.line'
    _description = 'Nexora Inventory Adjustment Line'
    _order = 'adjustment_id, product_id'

    adjustment_id = fields.Many2one('nexora.inventory.adjustment', string='Adjustment',
                                    required=True, ondelete='cascade')
    product_id = fields.Many2one('nexora.product', string='Product', required=True)
    theoretical_qty = fields.Float(string='On Hand')
    counted_qty = fields.Float(string='Counted')
    difference = fields.Float(compute='_compute_difference', store=True)

    @api.depends('theoretical_qty', 'counted_qty')
    def _compute_difference(self):
        for line in self:
            line.difference = line.counted_qty - line.theoretical_qty

    @api.constrains('counted_qty')
    def _check_counted(self):
        for line in self:
            if line.counted_qty < 0:
                raise ValidationError("The counted quantity cannot be negative.")

    @api.constrains('adjustment_id', 'product_id')
    def _check_unique_product(self):
        for line in self:
            if self.search_count([('adjustment_id', '=', line.adjustment_id.id),
                                  ('product_id', '=', line.product_id.id),
                                  ('id', '!=', line.id)]):
                raise ValidationError("A product can only appear once per adjustment.")
