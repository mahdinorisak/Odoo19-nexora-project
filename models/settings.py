from odoo import api, fields, models


def _default_tax_rate(env):
    value = env['ir.config_parameter'].sudo().get_param(
        'nexora_app.default_tax_rate', '0')
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nexora_default_tax_rate = fields.Float(
        string='Default Tax (%)',
        config_parameter='nexora_app.default_tax_rate')
    nexora_confirmation_email = fields.Selection(
        [('send', 'Send an email to the customer'),
         ('skip', 'Do not send an email')],
        string='Order Confirmation Email', default='send',
        config_parameter='nexora_app.send_confirmation_email')


class NexoraSaleOrderSettings(models.Model):
    _inherit = 'nexora.sale.order'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'tax_rate' in fields_list and 'tax_rate' not in res:
            res['tax_rate'] = _default_tax_rate(self.env)
        return res

    def _send_confirmation_email(self):
        mode = self.env['ir.config_parameter'].sudo().get_param(
            'nexora_app.send_confirmation_email', 'send')
        if mode == 'skip':
            return
        return super()._send_confirmation_email()


class NexoraPurchaseOrderSettings(models.Model):
    _inherit = 'nexora.purchase.order'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'tax_rate' in fields_list and 'tax_rate' not in res:
            res['tax_rate'] = _default_tax_rate(self.env)
        return res
