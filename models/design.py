from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraDesign(models.Model):
    _name = 'nexora.design'
    _description = 'Nexora Custom Design'
    _inherit = ['mail.thread', 'image.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(copy=False)
    designer_id = fields.Many2one('nexora.employee', string='Designer', tracking=True)
    description = fields.Text()
    product_ids = fields.One2many('nexora.product', 'design_id', string='Products')
    product_count = fields.Integer(compute='_compute_product_count')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.depends('product_ids')
    def _compute_product_count(self):
        for design in self:
            design.product_count = len(design.product_ids)

    @api.constrains('code')
    def _check_code_unique(self):
        for design in self:
            if design.code and self.search_count(
                    [('code', '=', design.code), ('id', '!=', design.id)]):
                raise ValidationError("Design code must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('nexora.design')
        return super().create(vals_list)

    def action_view_products(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'nexora.product',
            'view_mode': 'list,form',
            'domain': [('design_id', '=', self.id)],
        }


class NexoraProduct(models.Model):
    _inherit = 'nexora.product'

    design_id = fields.Many2one('nexora.design', string='Design', ondelete='set null')
