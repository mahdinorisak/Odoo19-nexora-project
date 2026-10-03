from odoo import api, fields, models


class NexoraProductCategory(models.Model):
    _name = 'nexora.product.category'
    _description = 'Nexora Product Category'
    _parent_name = 'parent_id'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    parent_id = fields.Many2one('nexora.product.category', string='Parent Category', ondelete='restrict')
    child_ids = fields.One2many('nexora.product.category', 'parent_id', string='Sub Categories')
    description = fields.Text()
    active = fields.Boolean(default=True)