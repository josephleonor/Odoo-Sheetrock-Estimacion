from odoo import models, fields, api

class SheetrockConfigurator(models.TransientModel):
    _name = 'sheetrock.configurator'
    _description = 'Configurador de Proyectos Sheetrock'

    name = fields.Char(string="Descripción del Proyecto", default="Nueva Estimación")
    
    # We use a TransientModel for the lines inside the wizard context usually, 
    # but the prompt asked for "sheetrock.section.line" model. 
    # Usually we link to that. If sheetrock.section.line is a logic model (persistent), we link via one2many.
    # If it is transient, users typically create a separate transient model.
    # Given the requirement "define un modelo sheetrock.section.line", I made it a Model (persistent) or I can make it Transient.
    # Since it's a "Wizard" capturing lines, I will make the lines accessible via a One2many relation.
    # BUT: A persistent model One2many from a TransientModel is tricky (orphan records). 
    # Best practice: The lines should probably be Transient too if they only live in the Wizard, or linked to a parent object.
    # For this exercise, I will use a Transient wrapper or assume lines are created transiently.
    # Let's adjust sheetrock.section.line to be Transient for the Wizard purpose OR link it properly.
    # However, to satisfy "Wizard... capture these lines", I'll create a link.
    
    line_ids = fields.One2many('sheetrock.configurator.line', 'wizard_id', string="Líneas de Sección")

    def action_generate_estimation(self):
        # Placeholder for future logic (e.g. create SO lines)
        return {'type': 'ir.actions.act_window_close'}


class SheetrockConfiguratorLine(models.TransientModel):
    _name = 'sheetrock.configurator.line'
    _description = 'Línea de Configuración'
    # Mirrors the sheetrock.section.line logic but strictly for the Wizard input
    
    wizard_id = fields.Many2one('sheetrock.configurator', string="Wizard")
    
    name = fields.Char(string="Sección", required=True)
    length = fields.Float(string="Largo (m)", default=0.0)
    height = fields.Float(string="Alto (m)", default=2.44)
    faces = fields.Selection([('1', '1 Cara'), ('2', '2 Caras')], default='1', required=True)
    
    finish_level = fields.Selection([
        ('n1', 'N1'), ('n2', 'N2'), ('n3', 'N3'), ('n4', 'N4'), ('n5', 'N5')
    ], default='n3', string="Acabado")
    
    gauge = fields.Selection([('20', '20'), ('26', '26')], default='26', string="Calibre")
    separation = fields.Selection([('16', '16"'), ('24', '24"')], default='24', string="Separación")
    
    board_id = fields.Many2one('product.product', string="Plancha 4x8")

    # Computes
    area = fields.Float(string="m2", compute='_compute_values')
    qty_planchas = fields.Float(string="Cant. Planchas", compute='_compute_values')
    needs_scaffold = fields.Boolean(string="Andamio", compute='_compute_values')
    labor_surcharge = fields.Float(string="Recargo MO %", compute='_compute_values')

    @api.depends('length', 'height', 'faces')
    def _compute_values(self):
        for rec in self:
            # 1. Area
            f = int(rec.faces) if rec.faces else 1
            m2 = rec.length * rec.height * f
            rec.area = m2
            
            # 2. Planchas
            # Base logic: m2 / 2.98
            q = m2 / 2.98 if m2 else 0.0
            
            # 3. High wall logic
            if rec.height > 2.44:
                q *= 1.10 # +10% waste
            
            rec.qty_planchas = q
            
            # 4. Scaffold
            if rec.height > 3.00:
                rec.needs_scaffold = True
                rec.labor_surcharge = 20.0
            else:
                rec.needs_scaffold = False
                rec.labor_surcharge = 0.0
