from odoo import fields, models


class NexoraProductionLine(models.Model):
    _name = 'nexora.production.line'
    _description = 'Nexora Production Line'
    _order = 'production_id, id'

    production_id = fields.Many2one('nexora.manufacturing.order', string='Order',
                                    required=True, ondelete='cascade')
    product_id = fields.Many2one('nexora.product', string='Component', required=True)
    quantity = fields.Float(string='Required', required=True)
    available = fields.Float(string='On Hand', related='product_id.qty_available')
