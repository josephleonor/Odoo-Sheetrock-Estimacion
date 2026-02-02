from odoo import models, fields, api

class SheetrockSectionLine(models.Model):
    _name = 'sheetrock.section.line'
    _description = 'Línea de Sección Sheetrock'

    name = fields.Char(string="Sección", required=True, help="Nombre de la sección (ej. Oficina Principal)")
    length = fields.Float(string="Largo (m)", required=True, default=1.0)
    height = fields.Float(string="Alto (m)", required=True, default=2.44)
    faces = fields.Selection([
        ('1', '1 Cara'),
        ('2', '2 Caras')
    ], string="Caras", required=True, default='1')
    
    finish_level = fields.Selection([
        ('n1', 'Nivel 1 (Cintado)'),
        ('n2', 'Nivel 2 (Capa Base)'),
        ('n3', 'Nivel 3 (Intermedio)'),
        ('n4', 'Nivel 4 (Liso)'),
        ('n5', 'Nivel 5 (Premium)')
    ], string="Nivel de Acabado", default='n3')
    
    gauge = fields.Selection([
        ('20', 'Calibre 20 (Estructural)'),
        ('26', 'Calibre 26 (Liviano)')
    ], string="Calibre Estructura", default='26')
    
    separation = fields.Selection([
        ('16', '16 Pulgadas'),
        ('24', '24 Pulgadas')
    ], string="Separación Parales", default='24')
    
    board_type_id = fields.Many2one('product.product', string="Tipo de Plancha (4x8)", 
                                    domain="[('name', 'ilike', '4x8')]", 
                                    help="Seleccione la plancha base de 4x8 pies")

    # Calculated Fields
    area_m2 = fields.Float(string="Área Total (m2)", compute="_compute_calculations", store=True)
    qty_planchas = fields.Float(string="Cant. Planchas (4x8)", compute="_compute_calculations", store=True)
    needs_scaffold = fields.Boolean(string="Requiere Andamio", compute="_compute_calculations", store=True)
    labor_surcharge_percent = fields.Float(string="Recargo MO (%)", compute="_compute_calculations", store=True)

    # Link to Wizard (if needed directly here, or handled via One2many in wizard)
    # config_id = fields.Many2one('sheetrock.configurator', string="Configurador") 

    @api.depends('length', 'height', 'faces')
    def _compute_calculations(self):
        for line in self:
            # 1. Área
            # m2 = largo * alto * caras
            # Ensure proper conversion if faces are stored as strings
            faces_int = int(line.faces) if line.faces else 1
            area = line.length * line.height * faces_int
            
            line.area_m2 = area

            # 2. Cantidad de Planchas
            # Base: m2 / 2.98
            raw_qty = area / 2.98 if area > 0 else 0
            
            # Desperdicio si alto > 2.44
            if line.height > 2.44:
                # Añade 10% de desperdicio extra (a la cantidad de material)
                raw_qty *= 1.10
            
            line.qty_planchas = raw_qty

            # 3. Andamios y Recargo
            if line.height > 3.00:
                line.needs_scaffold = True
                line.labor_surcharge_percent = 20.0
            else:
                line.needs_scaffold = False
                line.labor_surcharge_percent = 0.0
