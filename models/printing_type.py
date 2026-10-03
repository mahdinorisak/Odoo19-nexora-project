from odoo import fields, models


class NexoraPrintingType(models.Model):
    _name = 'nexora.printing.type'
    _description = 'Nexora Printing Type'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    base_price = fields.Monetary(currency_field='currency_id')
    option_ids = fields.One2many('nexora.printing.option', 'printing_type_id',
                                 string='Options')
    active = fields.Boolean(default=True)
