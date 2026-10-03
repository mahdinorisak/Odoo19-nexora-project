from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class NexoraPurchaseOrder(models.Model):
    _name = 'nexora.purchase.order'
    _description = 'Nexora Purchase Order'
    _inherit = ['mail.thread']
    _order = 'order_date desc, id desc'

    name = fields.Char(string='Order Number', default='New', copy=False, readonly=True)
    vendor_id = fields.Many2one('nexora.vendor', string='Vendor',
                                required=True, tracking=True)
    order_date = fields.Date(default=fields.Date.context_today, required=True)
    expected_date = fields.Date(string='Expected Delivery')
    user_id = fields.Many2one('res.users', string='Buyer',
                              default=lambda self: self.env.user, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('received', 'Received'),
        ('cancel', 'Cancelled'),
    ], default='draft', required=True, copy=False, tracking=True)
    notes = fields.Text()
    line_ids = fields.One2many('nexora.purchase.order.line', 'order_id',
                               string='Order Lines')
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
            order.amount_total = untaxed + order.amount_tax

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        if self.vendor_id and self.vendor_id.lead_time_days:
            self.expected_date = fields.Date.add(
                self.order_date or fields.Date.today(),
                days=self.vendor_id.lead_time_days)

    @api.constrains('order_date', 'expected_date')
    def _check_dates(self):
        for order in self:
            if order.expected_date and order.expected_date < order.order_date:
                raise ValidationError("Expected delivery cannot be before the order date.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'nexora.purchase.order') or 'New'
        return super().create(vals_list)

    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError("You can only delete draft or cancelled purchase orders.")
        return super().unlink()

    def action_confirm(self):
        for order in self:
            if not order.line_ids:
                raise UserError("Add at least one order line before confirming.")
            order.state = 'confirmed'

    def action_receive(self):
        vendor_loc = self.env.ref('nexora_app.location_vendors')
        stock_loc = self.env.ref('nexora_app.location_stock')
        for order in self:
            moves = self.env['nexora.stock.move'].create([{
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'location_src_id': vendor_loc.id,
                'location_dest_id': stock_loc.id,
                'reference': order.name,
            } for line in order.line_ids])
            moves.action_done()
            order.state = 'received'

    def action_cancel(self):
        for order in self:
            if order.state == 'received':
                raise UserError("A received order cannot be cancelled.")
            order.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'
