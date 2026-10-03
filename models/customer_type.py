from odoo import api, fields, models


class NexoraCustomerType(models.Model):
    _name = 'nexora.customer.type'
    _description = 'Nexora Customer Type'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text()
    customer_ids = fields.One2many('nexora.customer', 'customer_type_id',
                                   string='Customers')
    customer_count = fields.Integer(compute='_compute_customer_count')
    active = fields.Boolean(default=True)

    @api.depends('customer_ids')
    def _compute_customer_count(self):
        for record in self:
            record.customer_count = len(record.customer_ids)
