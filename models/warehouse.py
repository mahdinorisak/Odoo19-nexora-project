from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraWarehouse(models.Model):
    _name = 'nexora.warehouse'
    _description = 'Nexora Warehouse'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    street = fields.Char()
    city = fields.Char()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    location_ids = fields.One2many('nexora.location', 'warehouse_id', string='Locations')
    location_count = fields.Integer(compute='_compute_location_count')
    active = fields.Boolean(default=True)

    @api.depends('location_ids')
    def _compute_location_count(self):
        for warehouse in self:
            warehouse.location_count = len(warehouse.location_ids)

    @api.constrains('code')
    def _check_code_unique(self):
        for warehouse in self:
            if self.search_count([('code', '=', warehouse.code),
                                  ('id', '!=', warehouse.id)]):
                raise ValidationError("Warehouse code must be unique.")
