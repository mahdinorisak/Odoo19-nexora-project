from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraUom(models.Model):
    _name = 'nexora.uom'
    _description = 'Nexora Unit of Measure'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char(string='Symbol', required=True)
    active = fields.Boolean(default=True)
    product_count = fields.Integer(compute='_compute_product_count')

    def _compute_product_count(self):
        data = self.env['nexora.product']._read_group(
            [('uom_id', 'in', self.ids)], ['uom_id'], ['__count'])
        counts = {uom.id: count for uom, count in data}
        for uom in self:
            uom.product_count = counts.get(uom.id, 0)

    @api.constrains('name')
    def _check_name_unique(self):
        for uom in self:
            if self.with_context(active_test=False).search_count(
                    [('name', '=', uom.name), ('id', '!=', uom.id)]):
                raise ValidationError("Unit names must be unique.")

    @api.model
    def _assign_default_units(self):
        piece = self.env.ref('nexora_app.uom_piece', raise_if_not_found=False)
        if not piece:
            return True
        products = self.env['nexora.product'].with_context(active_test=False).search(
            [('uom_id', '=', False)])
        if products:
            products.write({'uom_id': piece.id})
        return True


class NexoraProduct(models.Model):
    _inherit = 'nexora.product'

    def _default_uom_id(self):
        uom = self.env.ref('nexora_app.uom_piece', raise_if_not_found=False)
        return uom.id if uom else False

    uom_id = fields.Many2one('nexora.uom', string='Unit', ondelete='restrict',
                             default=_default_uom_id)


class NexoraBomLine(models.Model):
    _inherit = 'nexora.bom.line'

    uom_id = fields.Many2one('nexora.uom', string='Unit',
                             related='component_id.uom_id')


class NexoraPurchaseOrderLine(models.Model):
    _inherit = 'nexora.purchase.order.line'

    uom_id = fields.Many2one('nexora.uom', string='Unit',
                             related='product_id.uom_id')


class NexoraSaleOrderLineUnit(models.Model):
    _inherit = 'nexora.sale.order.line'

    uom_id = fields.Many2one('nexora.uom', string='Unit',
                             related='product_id.uom_id')


class NexoraPurchaseRequestLine(models.Model):
    _inherit = 'nexora.purchase.request.line'

    uom_id = fields.Many2one('nexora.uom', string='Unit',
                             related='product_id.uom_id')


class NexoraProductionLine(models.Model):
    _inherit = 'nexora.production.line'

    uom_id = fields.Many2one('nexora.uom', string='Unit',
                             related='product_id.uom_id')


class NexoraStockMove(models.Model):
    _inherit = 'nexora.stock.move'

    uom_id = fields.Many2one('nexora.uom', string='Unit',
                             related='product_id.uom_id')
