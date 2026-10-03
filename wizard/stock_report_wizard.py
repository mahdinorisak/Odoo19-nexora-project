from odoo import fields, models
from odoo.exceptions import UserError


class NexoraStockReportWizard(models.TransientModel):
    _name = 'nexora.stock.report.wizard'
    _description = 'Stock Report Wizard'

    date_from = fields.Date(string='From',
                            default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='To', default=fields.Date.context_today)
    product_ids = fields.Many2many('nexora.product', string='Products',
                                   help="Leave empty to include all products.")

    def _check_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise UserError("The start date cannot be after the end date.")

    def action_print(self):
        self.ensure_one()
        self._check_dates()
        data = {
            'date_from': fields.Date.to_string(self.date_from) if self.date_from else False,
            'date_to': fields.Date.to_string(self.date_to) if self.date_to else False,
            'product_ids': self.product_ids.ids,
        }
        return self.env.ref('nexora_app.action_report_stock_moves').report_action(
            self, data=data)

    def action_view_moves(self):
        self.ensure_one()
        self._check_dates()
        domain = [('state', '=', 'done')]
        if self.date_from:
            domain.append(('date', '>=', '%s 00:00:00' % self.date_from))
        if self.date_to:
            domain.append(('date', '<=', '%s 23:59:59' % self.date_to))
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Movements',
            'res_model': 'nexora.stock.move',
            'view_mode': 'list,form',
            'domain': domain,
        }
