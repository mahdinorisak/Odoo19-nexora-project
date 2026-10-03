from odoo import api, fields, models
from odoo.exceptions import UserError


class NexoraSaleOrder(models.Model):
    _name = 'nexora.sale.order'
    _description = 'Nexora Sale Order'
    _inherit = ['mail.thread']
    _order = 'order_date desc, id desc'

    name = fields.Char(string='Order Number', default='New', copy=False, readonly=True)
    customer_id = fields.Many2one('nexora.customer', string='Customer',
                                  required=True, tracking=True)
    order_date = fields.Datetime(default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Salesperson',
                              default=lambda self: self.env.user, tracking=True)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', required=True, copy=False, tracking=True)
    notes = fields.Text()
    line_ids = fields.One2many('nexora.sale.order.line', 'order_id', string='Order Lines')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    tax_rate = fields.Float(string='Tax (%)')
    amount_untaxed = fields.Monetary(compute='_compute_amounts', store=True,
                                     currency_field='currency_id')
    amount_tax = fields.Monetary(compute='_compute_amounts', store=True,
                                 currency_field='currency_id')
    amount_total = fields.Monetary(compute='_compute_amounts', store=True,
                                   currency_field='currency_id')

    @api.depends('line_ids.subtotal', 'tax_rate')
    def _compute_amounts(self):
        for order in self:
            untaxed = sum(order.line_ids.mapped('subtotal'))
            order.amount_untaxed = untaxed
            order.amount_tax = untaxed * order.tax_rate / 100.0
            order.amount_total = order.amount_untaxed + order.amount_tax

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('nexora.sale.order') or 'New'
        return super().create(vals_list)

    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError("You can only delete quotations or cancelled orders.")
        return super().unlink()

    def action_confirm(self):
        for order in self:
            if not order.line_ids:
                raise UserError("Add at least one order line before confirming.")
            order.state = 'confirmed'
            order._send_confirmation_email()

    def _send_confirmation_email(self):
        self.ensure_one()
        template = self.env.ref('nexora_app.mail_template_sale_confirmed',
                                raise_if_not_found=False)
        if template and self.customer_id.email:
            template.send_mail(self.id, force_send=False)

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        for order in self:
            if order.state == 'done':
                raise UserError("A done order cannot be cancelled.")
            order.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'
