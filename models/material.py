from odoo import fields, models


class NexoraMaterial(models.Model):
    _name = 'nexora.material'
    _description = 'Nexora Material'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    cost = fields.Float(string='Cost per Unit')
    description = fields.Text()
    active = fields.Boolean(default=True)