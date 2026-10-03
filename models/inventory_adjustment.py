from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class NexoraInventoryAdjustment(models.Model):
    _name = 'nexora.inventory.adjustment'
    _description = 'Nexora Inventory Adjustment'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', default='New', copy=False, readonly=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    location_id = fields.Many2one(
        'nexora.location', string='Location', required=True,
        domain="[('usage', '=', 'internal')]",
        default=lambda self: self.env.ref('nexora_app.location_stock',
                                          raise_if_not_found=False))
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user)
    reason = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('counting', 'Counting'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', required=True, copy=False, tracking=True)
    line_ids = fields.One2many('nexora.inventory.adjustment.line', 'adjustment_id',
                               string='Counted Products', copy=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'nexora.inventory.adjustment') or 'New'
        return super().create(vals_list)

    def unlink(self):
        for adjustment in self:
            if adjustment.state not in ('draft', 'cancel'):
                raise UserError("You can only delete draft or cancelled adjustments.")
        return super().unlink()

    def _check_manager(self):
        if not self.env.user.has_group('nexora_app.group_nexora_production_manager'):
            raise UserError("Only Production Managers can do this.")

    def action_start(self):
        self._check_manager()
        for adjustment in self:
            if adjustment.state != 'draft':
                raise UserError("Only draft adjustments can start counting.")
            if not adjustment.line_ids:
                products = self.env['nexora.product'].search([])
                self.env['nexora.inventory.adjustment.line'].create([{
                    'adjustment_id': adjustment.id,
                    'product_id': product.id,
                    'theoretical_qty': product.qty_available,
                    'counted_qty': product.qty_available,
                } for product in products])
            adjustment.state = 'counting'

    def action_validate(self):
        self._check_manager()
        Move = self.env['nexora.stock.move']
        adjustment_loc = self.env.ref('nexora_app.location_adjustment')
        for adjustment in self:
            if adjustment.state != 'counting':
                raise UserError("Only adjustments being counted can be validated.")
            moves_vals = []
            for line in adjustment.line_ids:
                current = line.product_id.qty_available
                line.theoretical_qty = current
                diff = line.counted_qty - current
                if float_is_zero(diff, precision_digits=4):
                    continue
                if diff > 0:
                    src, dest, qty = adjustment_loc, adjustment.location_id, diff
                else:
                    src, dest, qty = adjustment.location_id, adjustment_loc, -diff
                moves_vals.append({
                    'product_id': line.product_id.id,
                    'quantity': qty,
                    'location_src_id': src.id,
                    'location_dest_id': dest.id,
                    'reference': adjustment.name,
                })
            if moves_vals:
                Move.create(moves_vals).action_done()
            adjustment.state = 'done'

    def action_view_moves(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Adjustment Moves',
            'res_model': 'nexora.stock.move',
            'view_mode': 'list,form',
            'domain': [('reference', '=', self.name)],
        }

    def action_cancel(self):
        for adjustment in self:
            if adjustment.state == 'done':
                raise UserError("A done adjustment cannot be cancelled.")
            adjustment.state = 'cancel'

    def action_draft(self):
        for adjustment in self:
            if adjustment.state == 'cancel':
                adjustment.state = 'draft'
