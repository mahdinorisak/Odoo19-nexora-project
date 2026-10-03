from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraEmployee(models.Model):
    _name = 'nexora.employee'
    _description = 'Nexora Employee'
    _inherit = ['mail.thread', 'image.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(copy=False)
    job_title = fields.Char(string='Job Position')
    department_id = fields.Many2one('nexora.department', string='Department',
                                    tracking=True)
    manager_id = fields.Many2one('nexora.employee', string='Manager')
    user_id = fields.Many2one('res.users', string='Related User')
    phone = fields.Char()
    email = fields.Char()
    hire_date = fields.Date()
    notes = fields.Text()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.constrains('email')
    def _check_email(self):
        for emp in self:
            if emp.email and '@' not in emp.email:
                raise ValidationError("Please enter a valid email address.")

    @api.constrains('code')
    def _check_code_unique(self):
        for emp in self:
            if emp.code and self.search_count(
                    [('code', '=', emp.code), ('id', '!=', emp.id)]):
                raise ValidationError("Employee code must be unique.")

    @api.constrains('manager_id')
    def _check_manager(self):
        for emp in self:
            if emp.manager_id == emp:
                raise ValidationError("An employee cannot be their own manager.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('nexora.employee')
        return super().create(vals_list)
