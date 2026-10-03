from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraDepartment(models.Model):
    _name = 'nexora.department'
    _description = 'Nexora Department'
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(required=True)
    complete_name = fields.Char(compute='_compute_complete_name', recursive=True,
                                store=True)
    parent_id = fields.Many2one('nexora.department', string='Parent Department',
                                ondelete='restrict')
    manager_id = fields.Many2one('nexora.employee', string='Manager')
    employee_ids = fields.One2many('nexora.employee', 'department_id',
                                   string='Employees')
    employee_count = fields.Integer(compute='_compute_employee_count')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for dept in self:
            if dept.parent_id:
                dept.complete_name = '%s / %s' % (dept.parent_id.complete_name, dept.name)
            else:
                dept.complete_name = dept.name

    @api.depends('employee_ids')
    def _compute_employee_count(self):
        for dept in self:
            dept.employee_count = len(dept.employee_ids)

    @api.constrains('parent_id')
    def _check_parent_loop(self):
        for dept in self:
            parent = dept.parent_id
            while parent:
                if parent == dept:
                    raise ValidationError("A department cannot be its own ancestor.")
                parent = parent.parent_id
