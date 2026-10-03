from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraVendor(models.Model):
    _name = 'nexora.vendor'
    _description = 'Nexora Vendor'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(copy=False)
    vendor_category_id = fields.Many2one('nexora.vendor.category',
                                         string='Vendor Category', tracking=True)
    phone = fields.Char()
    email = fields.Char()
    street = fields.Char()
    city = fields.Char()
    country_id = fields.Many2one('res.country', string='Country')
    lead_time_days = fields.Integer(string='Lead Time (days)')
    rating = fields.Selection([
        ('0', 'Not rated'),
        ('1', 'Poor'),
        ('2', 'Average'),
        ('3', 'Good'),
        ('4', 'Excellent'),
    ], default='0', tracking=True)
    notes = fields.Text()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.constrains('email')
    def _check_email(self):
        for vendor in self:
            if vendor.email and '@' not in vendor.email:
                raise ValidationError("Please enter a valid email address.")

    @api.constrains('lead_time_days')
    def _check_lead_time(self):
        for vendor in self:
            if vendor.lead_time_days < 0:
                raise ValidationError("Lead time cannot be negative.")

    @api.constrains('code')
    def _check_code_unique(self):
        for vendor in self:
            if vendor.code and self.search_count(
                    [('code', '=', vendor.code), ('id', '!=', vendor.id)]):
                raise ValidationError("Vendor code must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('nexora.vendor')
        return super().create(vals_list)
