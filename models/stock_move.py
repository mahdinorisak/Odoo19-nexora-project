from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class NexoraStockMove(models.Model):
    _name = 'nexora.stock.move'
    _description = 'Nexora Stock Move'
    _order = 'date desc, id desc'

    name = fields.Char(string='Move', default='New', copy=False, readonly=True)
    reference = fields.Char(string='Source Document')
    product_id = fields.Many2one('nexora.product', string='Product', required=True)
    quantity = fields.Float(default=1.0, required=True)
    location_src_id = fields.Many2one('nexora.location', string='From', required=True)
    location_dest_id = fields.Many2one('nexora.location', string='To', required=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', required=True, copy=False)
    move_type = fields.Selection([
        ('in', 'Incoming'),
        ('out', 'Outgoing'),
        ('internal', 'Internal'),
        ('other', 'Other'),
    ], compute='_compute_move_type', store=True)

    @api.depends('location_src_id.usage', 'location_dest_id.usage')
    def _compute_move_type(self):
        for move in self:
            src_internal = move.location_src_id.usage == 'internal'
            dest_internal = move.location_dest_id.usage == 'internal'
            if src_internal and dest_internal:
                move.move_type = 'internal'
            elif dest_internal:
                move.move_type = 'in'
            elif src_internal:
                move.move_type = 'out'
            else:
                move.move_type = 'other'

    @api.constrains('quantity', 'location_src_id', 'location_dest_id')
    def _check_move(self):
        for move in self:
            if move.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            if move.location_src_id == move.location_dest_id:
                raise ValidationError("Source and destination must be different.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'nexora.stock.move') or 'New'
        return super().create(vals_list)

    def unlink(self):
        for move in self:
            if move.state == 'done':
                raise UserError("You cannot delete a done stock move. Cancel is not possible either.")
        return super().unlink()

    def action_done(self):
        for move in self:
            if move.state != 'draft':
                raise UserError("Only draft moves can be validated.")
            if move.location_src_id.usage == 'internal':
                move.product_id.invalidate_recordset(['qty_available'])
                if move.product_id.qty_available < move.quantity:
                    raise UserError("Not enough stock for %s. On hand: %s, requested: %s." % (
                        move.product_id.name, move.product_id.qty_available, move.quantity))
            move.state = 'done'

    def action_cancel(self):
        for move in self:
            if move.state == 'done':
                raise UserError("A done move cannot be cancelled.")
            move.state = 'cancel'

    def action_draft(self):
        for move in self:
            if move.state == 'cancel':
                move.state = 'draft'
