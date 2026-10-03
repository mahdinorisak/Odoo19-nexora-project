from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class NexoraPurchaseRequest(models.Model):
    _name = 'nexora.purchase.request'
    _description = 'Nexora Purchase Request'
    _inherit = ['mail.thread']
    _order = 'request_date desc, id desc'

    name = fields.Char(string='Request Number', default='New', copy=False,
                       readonly=True)
    user_id = fields.Many2one('res.users', string='Requested By',
                              default=lambda self: self.env.user, tracking=True)
    employee_id = fields.Many2one('nexora.employee', string='Employee',
                                  compute='_compute_employee_id', store=True,
                                  readonly=False)
    request_date = fields.Date(default=fields.Date.context_today, required=True)
    date_needed = fields.Date(string='Needed By')
    vendor_id = fields.Many2one('nexora.vendor', string='Suggested Vendor')
    reason = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('ordered', 'Ordered'),
        ('cancel', 'Cancelled'),
    ], default='draft', required=True, copy=False, tracking=True)
    approved_by = fields.Many2one('res.users', string='Decided By',
                                  copy=False, readonly=True)
    line_ids = fields.One2many('nexora.purchase.request.line', 'request_id',
                               string='Requested Items')
    purchase_order_id = fields.Many2one('nexora.purchase.order',
                                        string='Purchase Order',
                                        copy=False, readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    amount_total = fields.Monetary(compute='_compute_amount_total', store=True,
                                   currency_field='currency_id')

    @api.depends('user_id')
    def _compute_employee_id(self):
        for request in self:
            request.employee_id = self.env['nexora.employee'].search(
                [('user_id', '=', request.user_id.id)], limit=1)

    @api.depends('line_ids.subtotal')
    def _compute_amount_total(self):
        for request in self:
            request.amount_total = sum(request.line_ids.mapped('subtotal'))

    @api.constrains('request_date', 'date_needed')
    def _check_dates(self):
        for request in self:
            if request.date_needed and request.date_needed < request.request_date:
                raise ValidationError("The needed-by date cannot be before the request date.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'nexora.purchase.request') or 'New'
        return super().create(vals_list)

    def unlink(self):
        for request in self:
            if request.state not in ('draft', 'cancel'):
                raise UserError("You can only delete draft or cancelled requests.")
        return super().unlink()

    def _check_manager(self):
        if not self.env.user.has_group('nexora_app.group_nexora_production_manager'):
            raise UserError("Only Production Managers can do this.")

    def action_submit(self):
        for request in self:
            if request.state != 'draft':
                raise UserError("Only draft requests can be submitted.")
            if not request.line_ids:
                raise UserError("Add at least one item before submitting.")
            request.state = 'submitted'

    def action_approve(self):
        self._check_manager()
        user = self.env.user
        is_admin = user.has_group('nexora_app.group_nexora_admin')
        for request in self:
            if request.state != 'submitted':
                raise UserError("Only submitted requests can be approved.")
            if request.user_id == user and not is_admin:
                raise UserError("You cannot approve your own request.")
            request.write({'state': 'approved', 'approved_by': user.id})

    def action_reject(self):
        self._check_manager()
        for request in self:
            if request.state != 'submitted':
                raise UserError("Only submitted requests can be rejected.")
            request.write({'state': 'rejected', 'approved_by': self.env.user.id})

    def action_create_order(self):
        self._check_manager()
        self.ensure_one()
        if self.state != 'approved':
            raise UserError("Only approved requests can become purchase orders.")
        if not self.vendor_id:
            raise UserError("Select a suggested vendor before creating the purchase order.")
        order = self.env['nexora.purchase.order'].create({
            'vendor_id': self.vendor_id.id,
            'notes': 'Created from %s' % self.name,
            'line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'description': line.description,
                'quantity': line.quantity,
                'unit_cost': line.estimated_cost,
            }) for line in self.line_ids],
        })
        self.write({'state': 'ordered', 'purchase_order_id': order.id})
        return self.action_view_order()

    def action_view_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nexora.purchase.order',
            'res_id': self.purchase_order_id.id,
            'view_mode': 'form',
        }

    def action_cancel(self):
        for request in self:
            if request.state == 'ordered':
                raise UserError("An ordered request cannot be cancelled.")
            request.state = 'cancel'

    def action_draft(self):
        for request in self:
            if request.state in ('rejected', 'cancel'):
                request.state = 'draft'
