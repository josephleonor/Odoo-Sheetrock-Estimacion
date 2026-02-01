from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = 'project.task'

    x_contractor_id = fields.Many2one('res.partner', string="Contratista Asignado", help="Contratista externo encargado de la ejecución")
    sheetrock_sale_line_id = fields.Many2one('sale.order.line', string="Partida de Presupuesto", domain="[('is_sheetrock_calculation', '=', True)]")
