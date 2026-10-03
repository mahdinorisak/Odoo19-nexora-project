from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    nexora_customer_ids = fields.One2many('nexora.customer', 'partner_id',
                                          string='Nexora Customers',
                                          groups='nexora_app.group_nexora_user')
    nexora_customer_count = fields.Integer(compute='_compute_nexora_customer_count',
                                           groups='nexora_app.group_nexora_user')

    @api.depends('nexora_customer_ids')
    def _compute_nexora_customer_count(self):
        for partner in self:
            partner.nexora_customer_count = len(partner.nexora_customer_ids)

    def action_view_nexora_customers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nexora Customers',
            'res_model': 'nexora.customer',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
        }
