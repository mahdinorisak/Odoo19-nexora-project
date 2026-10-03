from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraLocation(models.Model):
    _name = 'nexora.location'
    _description = 'Nexora Location'
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(required=True)
    complete_name = fields.Char(compute='_compute_complete_name', recursive=True,
                                store=True)
    parent_id = fields.Many2one('nexora.location', string='Parent Location',
                                ondelete='restrict')
    warehouse_id = fields.Many2one('nexora.warehouse', string='Warehouse',
                                   ondelete='restrict')
    usage = fields.Selection([
        ('internal', 'Internal'),
        ('vendor', 'Vendor'),
        ('customer', 'Customer'),
        ('production', 'Production'),
        ('inventory', 'Inventory Adjustment'),
    ], default='internal', required=True)
    active = fields.Boolean(default=True)

    @api.depends('name', 'parent_id.complete_name', 'warehouse_id.code')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = '%s / %s' % (
                    location.parent_id.complete_name, location.name)
            elif location.warehouse_id and location.warehouse_id.code:
                location.complete_name = '%s / %s' % (
                    location.warehouse_id.code, location.name)
            else:
                location.complete_name = location.name

    @api.constrains('parent_id')
    def _check_parent_loop(self):
        for location in self:
            parent = location.parent_id
            while parent:
                if parent == location:
                    raise ValidationError("A location cannot be its own ancestor.")
                parent = parent.parent_id
