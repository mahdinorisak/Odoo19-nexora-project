from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class NexoraManufacturingOrder(models.Model):
    _name = 'nexora.manufacturing.order'
    _description = 'Nexora Manufacturing Order'
    _inherit = ['mail.thread']
    _order = 'date_planned desc, id desc'

    name = fields.Char(string='Reference', default='New', copy=False, readonly=True)
    product_id = fields.Many2one('nexora.product', string='Product',
                                 required=True, tracking=True)
    bom_id = fields.Many2one('nexora.bom', string='Bill of Materials',
                             compute='_compute_bom_id', store=True,
                             readonly=False, precompute=True,
                             domain="[('product_id', '=', product_id)]")
    quantity = fields.Float(string='Quantity to Produce', default=1.0, required=True)
    date_planned = fields.Datetime(string='Planned Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', required=True, copy=False, tracking=True)
    line_ids = fields.One2many('nexora.production.line', 'production_id',
                               string='Components', copy=False)
    notes = fields.Text()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.depends('product_id')
    def _compute_bom_id(self):
        for order in self:
            order.bom_id = self.env['nexora.bom'].search(
                [('product_id', '=', order.product_id.id)], limit=1) if order.product_id else False

    @api.constrains('quantity')
    def _check_quantity(self):
        for order in self:
            if order.quantity <= 0:
                raise ValidationError("Quantity to produce must be greater than zero.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'nexora.manufacturing.order') or 'New'
        return super().create(vals_list)

    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError("You can only delete draft or cancelled manufacturing orders.")
        return super().unlink()

    def action_confirm(self):
        for order in self:
            if not order.bom_id:
                raise UserError("Select a Bill of Materials first.")
            if not order.bom_id.line_ids:
                raise UserError("The Bill of Materials has no components.")
            order.line_ids.unlink()
            factor = order.quantity / order.bom_id.quantity
            self.env['nexora.production.line'].create([{
                'production_id': order.id,
                'product_id': bom_line.component_id.id,
                'quantity': bom_line.quantity * factor,
            } for bom_line in order.bom_id.line_ids])
            order.state = 'confirmed'

    def action_start(self):
        for order in self:
            missing = order.line_ids.filtered(lambda l: l.product_id.qty_available < l.quantity)
            if missing:
                details = ', '.join('%s (need %s, have %s)' % (
                    l.product_id.name, l.quantity, l.product_id.qty_available)
                    for l in missing)
                raise UserError("Not enough components: %s" % details)
            order.state = 'progress'

    def action_done(self):
        stock = self.env.ref('nexora_app.location_stock')
        production = self.env.ref('nexora_app.location_production')
        Move = self.env['nexora.stock.move']
        for order in self:
            if order.state != 'progress':
                raise UserError("Only orders in progress can be completed.")
            consumed = Move.create([{
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'location_src_id': stock.id,
                'location_dest_id': production.id,
                'reference': order.name,
            } for line in order.line_ids])
            consumed.action_done()
            produced = Move.create([{
                'product_id': order.product_id.id,
                'quantity': order.quantity,
                'location_src_id': production.id,
                'location_dest_id': stock.id,
                'reference': order.name,
            }])
            produced.action_done()
            order.state = 'done'

    def action_cancel(self):
        for order in self:
            if order.state == 'done':
                raise UserError("A done order cannot be cancelled.")
            order.state = 'cancel'

    def action_draft(self):
        for order in self:
            if order.state == 'cancel':
                order.state = 'draft'
