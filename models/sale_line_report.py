from odoo import fields, models


class NexoraSaleOrderLine(models.Model):
    _inherit = 'nexora.sale.order.line'

    order_date = fields.Datetime(related='order_id.order_date', store=True)
    customer_id = fields.Many2one('nexora.customer', related='order_id.customer_id',
                                  store=True)
    order_state = fields.Selection(related='order_id.state', store=True,
                                   string='Order Status')
