from odoo import models, fields, api, _

class SheetrockLineWizard(models.TransientModel):
    _name = 'sheetrock.line.wizard'
    _description = 'Wizard de Captura Técnica Sheetrock'

    sale_line_id = fields.Many2one('sale.order.line', string="Línea de Venta", required=True)
    product_id = fields.Many2one('product.product', string="Servicio", readonly=True)
    
    default_faces = fields.Selection([('1', '1 Cara'), ('2', '2 Caras')], default='1', string="Caras (Defecto)")
    default_thickness = fields.Selection([('1/2', '1/2 Pulgada'), ('5/8', '5/8 Pulgada'), ('1', '1 Pulgada')], default='1/2', string="Grosor (Defecto)")
    default_gauge = fields.Selection([('20', 'C-20'), ('22', 'C-22'), ('24', 'C-24'), ('26', 'C-26')], default='26', string="Calibre (Defecto)")

    section_ids = fields.One2many('sheetrock.line.wizard.section', 'wizard_id', string="Secciones")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'sale_line_id' in res:
            line = self.env['sale.order.line'].browse(res['sale_line_id'])
            # res['contractor_id'] = line.contractor_id.id  <-- Removed
            sections = []
            for s in line.sheetrock_section_ids:
                sections.append((0, 0, {
                    'name': s.name,
                    'length': s.length,
                    'height': s.height,
                    'faces': s.faces,
                    'board_thickness': s.board_thickness,
                    'structure_gauge': s.structure_gauge,
                    'add_reinforcement': s.add_reinforcement,
                }))
            res['section_ids'] = sections
        return res

    def action_confirm(self):
        self.ensure_one()
        line = self.sale_line_id
        
        # Write Contractor - Removed as per requirement
        # line.contractor_id = self.contractor_id

        # 1. Clear old sections and recreate
        line.sheetrock_section_ids.unlink()
        
        new_sections = []
        total_area = 0.0
        details_list = []
        
        all_materials = {} 
        total_labor_cost = 0.0
        
        labor_rate_model = self.env['sheetrock.labor.rate']
        labor_rule = labor_rate_model.search([('active','=',True)], limit=1)
        
        consumption_model = self.env['sheetrock.consumption.rule']
        
        for ws in self.section_ids:
            sec_area = ws.length * ws.height * int(ws.faces)
            new_sections.append({
                'name': ws.name,
                'length': ws.length,
                'height': ws.height,
                'faces': ws.faces,
                'board_thickness': ws.board_thickness,
                'structure_gauge': ws.structure_gauge,
                'add_reinforcement': ws.add_reinforcement,
            })
            total_area += sec_area
            details_list.append(f"{ws.name}({ws.faces}) {ws.length}x{ws.height} = {sec_area:.2f}m2")
            
            # Cost Calc
            rule_domain = [('faces', '=', ws.faces),('board_thickness', '=', ws.board_thickness),('structure_gauge', '=', ws.structure_gauge)]
            rule = consumption_model.search(rule_domain, limit=1)
            
            if rule:
                for rline in rule.line_ids:
                    if rline.is_reinforcement and not ws.add_reinforcement: continue
                    qty_needed = rline.quantity * sec_area 
                    if rline.component_type != 'other': qty_needed *= 1.10
                    prod = rline.product_id
                    if prod.id not in all_materials: all_materials[prod.id] = 0.0
                    all_materials[prod.id] += qty_needed
            
            if labor_rule:
                rate = labor_rule.get_price(ws.faces)
                total_labor_cost += (sec_area * rate)

        line.write({'sheetrock_section_ids': [(0, 0, x) for x in new_sections]})
        line.product_uom_qty = total_area
        
        desc_header = line.product_id.name + "\n"
        desc_body = "\n".join(details_list)
        line.name = f"{desc_header}{desc_body}"

        total_material_cost = 0.0
        for pid, qty in all_materials.items():
            prod = self.env['product.product'].browse(pid)
            total_material_cost += (prod.standard_price * qty)
            
        transport_cost = 0.0
        trans_rule = self.env['sheetrock.transport.rule'].search([('min_m2', '<=', total_area),('max_m2', '>=', total_area)], limit=1, order='min_m2 desc')
        if trans_rule: transport_cost = trans_rule.fixed_price

        line.write({
            'estimated_material_cost': total_material_cost,
            'estimated_labor_cost': total_labor_cost,
            'estimated_transport_cost': transport_cost,
        })
        
        return {'type': 'ir.actions.act_window_close'}


