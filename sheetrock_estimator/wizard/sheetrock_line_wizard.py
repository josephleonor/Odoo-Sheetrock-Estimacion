from odoo import api, fields, models, _


class SheetrockLineWizard(models.TransientModel):
    _name = 'sheetrock.line.wizard'
    _description = 'Wizard de Captura Técnica Sheetrock'

    sale_line_id = fields.Many2one('sale.order.line', string='Línea de Venta', required=True)
    product_id = fields.Many2one('product.product', string='Servicio', readonly=True)

    default_faces = fields.Selection(
        [('1', '1 Cara'), ('2', '2 Caras')],
        default='1',
        string='Caras (Defecto)',
    )
    default_thickness = fields.Selection(
        [('1/2', '1/2 Pulgada'), ('5/8', '5/8 Pulgada'), ('1', '1 Pulgada')],
        default='1/2',
        string='Grosor (Defecto)',
    )
    default_gauge = fields.Selection(
        [('20', 'C-20'), ('22', 'C-22'), ('24', 'C-24'), ('26', 'C-26')],
        default='26',
        string='Calibre (Defecto)',
    )

    section_ids = fields.One2many(
        'sheetrock.line.wizard.section',
        'wizard_id',
        string='Muros',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        sale_line_id = res.get('sale_line_id') or self.env.context.get('default_sale_line_id')
        if sale_line_id:
            line = self.env['sale.order.line'].browse(sale_line_id)
            sections = []
            for section in line.sheetrock_section_ids:
                openings = [
                    (0, 0, {
                        'name': opening.name,
                        'opening_type': opening.opening_type,
                        'width': opening.width,
                        'height': opening.height,
                        'x_position': opening.x_position,
                        'sill_height': opening.sill_height,
                    })
                    for opening in section.opening_ids
                ]
                sections.append((0, 0, {
                    'name': section.name,
                    'length': section.length,
                    'height': section.height,
                    'faces': section.faces,
                    'layers': section.layers,
                    'waste_percent': section.waste_percent,
                    'stud_spacing': section.stud_spacing,
                    'structure_type': section.structure_type,
                    'board_thickness': section.board_thickness,
                    'structure_gauge': section.structure_gauge,
                    'add_reinforcement': section.add_reinforcement,
                    'opening_ids': openings,
                }))
            res['section_ids'] = sections
        return res

    def action_confirm(self):
        self.ensure_one()
        line = self.sale_line_id

        line.sheetrock_section_ids.unlink()

        new_sections = []
        total_sale_area = 0.0
        total_material_cost = 0.0
        total_labor_cost = 0.0
        details_list = []
        all_materials = {}

        labor_rule = self.env['sheetrock.labor.rate'].search([('active', '=', True)], limit=1)
        consumption_model = self.env['sheetrock.consumption.rule']

        for wall in self.section_ids:
            openings_vals = [
                (0, 0, {
                    'name': opening.name,
                    'opening_type': opening.opening_type,
                    'width': opening.width,
                    'height': opening.height,
                    'x_position': opening.x_position,
                    'sill_height': opening.sill_height,
                })
                for opening in wall.opening_ids
            ]
            new_sections.append({
                'name': wall.name,
                'length': wall.length,
                'height': wall.height,
                'faces': wall.faces,
                'layers': wall.layers,
                'waste_percent': wall.waste_percent,
                'stud_spacing': wall.stud_spacing,
                'structure_type': wall.structure_type,
                'board_thickness': wall.board_thickness,
                'structure_gauge': wall.structure_gauge,
                'add_reinforcement': wall.add_reinforcement,
                'opening_ids': openings_vals,
            })

            sale_area = wall.area
            material_area = wall.area_with_waste
            total_sale_area += sale_area
            details_list.append(
                f'{wall.name}: {wall.length:.2f}x{wall.height:.2f} m, '
                f'aberturas {wall.openings_area:.2f} m², neto {sale_area:.2f} m²'
            )

            rule = consumption_model.search([
                ('faces', '=', wall.faces),
                ('board_thickness', '=', wall.board_thickness),
                ('structure_gauge', '=', wall.structure_gauge),
            ], limit=1)

            if rule:
                for rule_line in rule.line_ids:
                    if rule_line.is_reinforcement and not wall.add_reinforcement:
                        continue
                    basis_area = sale_area if rule_line.component_type == 'other' else material_area
                    qty_needed = rule_line.quantity * basis_area
                    product = rule_line.product_id
                    all_materials[product.id] = all_materials.get(product.id, 0.0) + qty_needed

            if labor_rule:
                rate = labor_rule.get_price(wall.faces)
                total_labor_cost += sale_area * rate

        line.write({'sheetrock_section_ids': [(0, 0, values) for values in new_sections]})
        line.product_uom_qty = total_sale_area

        description = line.product_id.name
        if details_list:
            description += '\n' + '\n'.join(details_list)
        line.name = description

        for product_id, quantity in all_materials.items():
            product = self.env['product.product'].browse(product_id)
            total_material_cost += product.standard_price * quantity

        transport_cost = 0.0
        transport_rule = self.env['sheetrock.transport.rule'].search([
            ('min_m2', '<=', total_sale_area),
            ('max_m2', '>=', total_sale_area),
        ], limit=1, order='min_m2 desc')
        if transport_rule:
            transport_cost = transport_rule.fixed_price

        line.write({
            'estimated_material_cost': total_material_cost,
            'estimated_labor_cost': total_labor_cost,
            'estimated_transport_cost': transport_cost,
        })

        return {'type': 'ir.actions.act_window_close'}
