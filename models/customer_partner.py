from odoo import fields, models
from odoo.exceptions import UserError


class NexoraCustomer(models.Model):
    _inherit = 'nexora.customer'

    partner_id = fields.Many2one('res.partner', string='Contact',
                                 copy=False, ondelete='set null')

    def action_create_partner(self):
        for customer in self:
            if customer.partner_id:
                raise UserError("This customer is already linked to a contact.")
            customer.partner_id = self.env['res.partner'].create({
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email,
                'street': customer.street,
                'city': customer.city,
                'country_id': customer.country_id.id,
                'ref': customer.code,
            })

    def action_open_partner(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
        }
