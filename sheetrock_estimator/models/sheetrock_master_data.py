from odoo import models, fields, api

class SheetrockConsumptionRule(models.Model):
    _name = 'sheetrock.consumption.rule'
    _description = 'Matriz de Consumo Sheetrock (m2)'
    _rec_name = 'name'

    name = fields.Char(string='Nombre de la Regla', required=True, help="Ej: Muro W111-Standard")
    
    # Technical Parameters for matching
    faces = fields.Selection([
        ('1', '1 Cara'),
        ('2', '2 Caras')
    ], string="Caras", required=True, default='1')
    
    board_thickness = fields.Selection([
        ('1/2', '1/2 Pulgada'),
        ('5/8', '5/8 Pulgada'), 
        ('1', '1 Pulgada')
    ], string="Grosor Plancha", required=True, default='1/2')
    
    structure_gauge = fields.Selection([
        ('20', 'Calibre 20'),
        ('22', 'Calibre 22'),
        ('24', 'Calibre 24'),
        ('26', 'Calibre 26')
    ], string="Calibre Estructura", required=True, default='26')
    
    active = fields.Boolean(default=True)
    
    line_ids = fields.One2many('sheetrock.consumption.rule.line', 'rule_id', string="Materiales por m2")

class SheetrockConsumptionRuleLine(models.Model):
    _name = 'sheetrock.consumption.rule.line'
    _description = 'Línea de Consumo de Material'

    rule_id = fields.Many2one('sheetrock.consumption.rule', string="Regla", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Material", required=True, domain="[('type','=','product')]")
    quantity = fields.Float(string="Cantidad por m2", required=True, digits=(10,4))
    
    component_type = fields.Selection([
        ('board', 'Plancha'),
        ('profile', 'Perfilería'),
        ('fixing', 'Fijación/Tornillos'),
        ('finish', 'Acabados/Masilla/Cinta'),
        ('other', 'Otros')
    ], string="Tipo de Componente", required=True, default='other')
    
    is_reinforcement = fields.Boolean(string="Es Refuerzo", default=False, help="Solo se añade si se marca 'Refuerzos' en la sección")


class SheetrockLaborRate(models.Model):
    _name = 'sheetrock.labor.rate'
    _description = 'Tarifario de Mano de Obra (PA)'
    
    name = fields.Char(string="Descripción", required=True, default="Tarifa Estándar")
    base_rate = fields.Float(string="Tarifa Base (1 Cara)", required=True, help="Precio por m2 para 1 cara")
    two_faces_multiplier = fields.Float(string="Multiplicador 2 Caras", default=1.8, help="Factor para calcular precio 2 caras")
    
    active = fields.Boolean(default=True)

    def get_price(self, faces):
        self.ensure_one()
        if faces == '2':
            return self.base_rate * self.two_faces_multiplier
        return self.base_rate


class SheetrockTransportRule(models.Model):
    _name = 'sheetrock.transport.rule'
    _description = 'Regla de Transporte'
    
    name = fields.Char(string="Rango/Zona", required=True)
    min_m2 = fields.Float(string="Mínimo m2", default=0.0)
    max_m2 = fields.Float(string="Máximo m2", default=9999.0)
    fixed_price = fields.Float(string="Costo Transporte", required=True)
