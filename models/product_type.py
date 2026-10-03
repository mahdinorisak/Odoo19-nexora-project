from odoo import fields, models


class NexoraProductType(models.Model):
    _name = 'nexora.product.type'
    _description = 'Nexora Product Type'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text()
    active = fields.Boolean(default=True)