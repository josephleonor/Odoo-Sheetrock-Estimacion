from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sheetrock_section_ids = fields.One2many('sheetrock.section', 'sale_line_id', string="Secciones Sheetrock")
    is_sheetrock_calculation = fields.Boolean(related='product_id.is_sheetrock_service', readonly=True)
    
    # Contractor assignment
    contractor_id = fields.Many2one('res.partner', string="Contratista Sugerido", domain="[('supplier_rank','>',0)]")

    estimated_material_cost = fields.Float(string="Costo Est. Materiales")
    estimated_labor_cost = fields.Float(string="Costo Est. Mano Obra")
    estimated_transport_cost = fields.Float(string="Costo Est. Transporte")
    estimated_total_cost = fields.Float(string="Costo Total Interno", compute='_compute_estimated_total', store=True)

    @api.depends('estimated_material_cost', 'estimated_labor_cost', 'estimated_transport_cost')
    def _compute_estimated_total(self):
        for line in self:
            line.estimated_total_cost = line.estimated_material_cost + line.estimated_labor_cost + line.estimated_transport_cost

    def action_open_sheetrock_wizard(self):
        self.ensure_one()
        return {
            'name': _('Calculadora de Muros Sheetrock'),
            'type': 'ir.actions.act_window',
            'res_model': 'sheetrock.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_line_id': self.id,
                'default_product_id': self.product_id.id,
                'default_contractor_id': self.contractor_id.id, 
            }
        }
