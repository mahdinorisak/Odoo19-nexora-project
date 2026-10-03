from odoo import api, fields, models


class NexoraVendorCategory(models.Model):
    _name = 'nexora.vendor.category'
    _description = 'Nexora Vendor Category'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text()
    vendor_ids = fields.One2many('nexora.vendor', 'vendor_category_id',
                                 string='Vendors')
    vendor_count = fields.Integer(compute='_compute_vendor_count')
    active = fields.Boolean(default=True)

    @api.depends('vendor_ids')
    def _compute_vendor_count(self):
        for record in self:
            record.vendor_count = len(record.vendor_ids)
