from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NexoraJob(models.Model):
    _name = 'nexora.job'
    _description = 'Nexora Job Position'
    _order = 'name'

    name = fields.Char(string='Job Position', required=True)
    department_id = fields.Many2one('nexora.department', string='Department')
    description = fields.Text()
    employee_ids = fields.One2many('nexora.employee', 'job_id', string='Employees')
    employee_count = fields.Integer(compute='_compute_employee_count')
    active = fields.Boolean(default=True)

    @api.depends('employee_ids')
    def _compute_employee_count(self):
        for job in self:
            job.employee_count = len(job.employee_ids)

    @api.constrains('name', 'department_id')
    def _check_unique(self):
        for job in self:
            if self.with_context(active_test=False).search_count([
                    ('name', '=', job.name),
                    ('department_id', '=', job.department_id.id),
                    ('id', '!=', job.id)]):
                raise ValidationError("This job position already exists in the department.")


class NexoraEmployee(models.Model):
    _inherit = 'nexora.employee'

    job_id = fields.Many2one('nexora.job', string='Job', ondelete='set null',
                             tracking=True)

    @api.onchange('job_id')
    def _onchange_job_id(self):
        if self.job_id:
            self.job_title = self.job_id.name
