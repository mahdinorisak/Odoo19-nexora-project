from odoo import api, models


class ReportStockMoves(models.AbstractModel):
    _name = 'report.nexora_app.report_stock_moves_document'
    _description = 'Stock Movements Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        domain = [('state', '=', 'done')]
        if data.get('date_from'):
            domain.append(('date', '>=', '%s 00:00:00' % data['date_from']))
        if data.get('date_to'):
            domain.append(('date', '<=', '%s 23:59:59' % data['date_to']))
        if data.get('product_ids'):
            domain.append(('product_id', 'in', data['product_ids']))
        moves = self.env['nexora.stock.move'].search(domain, order='date')
        return {
            'doc_ids': docids,
            'doc_model': 'nexora.stock.move',
            'docs': moves,
            'moves': moves,
            'data': data,
            'total_in': sum(moves.filtered(lambda m: m.move_type == 'in').mapped('quantity')),
            'total_out': sum(moves.filtered(lambda m: m.move_type == 'out').mapped('quantity')),
        }
