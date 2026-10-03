from odoo import fields, models


class NexoraPrintingOption(models.Model):
    _name = 'nexora.printing.option'
    _description = 'Nexora Printing Option'
    _order = 'printing_type_id, name'

    name = fields.Char(required=True)
    printing_type_id = fields.Many2one('nexora.printing.type', string='Printing Type',
                                       required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='printing_type_id.currency_id')
    extra_price = fields.Monetary(currency_field='currency_id')
    description = fields.Text()
    active = fields.Boolean(default=True)
