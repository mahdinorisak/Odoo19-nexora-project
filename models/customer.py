from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraCustomer(models.Model):
    _name = 'nexora.customer'
    _description = 'Nexora Customer'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(copy=False)
    customer_type_id = fields.Many2one('nexora.customer.type', string='Customer Type',
                                       tracking=True)
    phone = fields.Char()
    email = fields.Char()
    street = fields.Char()
    city = fields.Char()
    country_id = fields.Many2one('res.country', string='Country')
    full_address = fields.Char(compute='_compute_full_address')
    notes = fields.Text()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.depends('street', 'city', 'country_id')
    def _compute_full_address(self):
        for customer in self:
            parts = [customer.street, customer.city, customer.country_id.name]
            customer.full_address = ', '.join(p for p in parts if p)

    @api.constrains('email')
    def _check_email(self):
        for customer in self:
            if customer.email and '@' not in customer.email:
                raise ValidationError("Please enter a valid email address.")

    @api.constrains('code')
    def _check_code_unique(self):
        for customer in self:
            if customer.code and self.search_count(
                    [('code', '=', customer.code), ('id', '!=', customer.id)]):
                raise ValidationError("Customer code must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('nexora.customer')
        return super().create(vals_list)
