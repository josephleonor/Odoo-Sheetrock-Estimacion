from odoo import models, fields, api

class SheetrockSection(models.Model):
    _name = 'sheetrock.section'
    _description = 'Sección Técnica de Muro'

    sale_line_id = fields.Many2one('sale.order.line', string="Línea de Venta", ondelete='cascade')
    name = fields.Char(string="Nombre Sección", required=True, help="Ej. Baño Principal, Oficina Gerencia")
    
    # Dimensions
    length = fields.Float(string="Largo (m)", required=True)
    height = fields.Float(string="Alto (m)", required=True)
    area = fields.Float(string="Área (m2)", compute='_compute_area', store=True)
    
    # Technical Specs (Snapshot from Wizard/Defaults)
    faces = fields.Selection([
        ('1', '1 Cara'),
        ('2', '2 Caras')
    ], string="Caras", default='1', required=True)
    
    board_thickness = fields.Selection([
        ('1/2', '1/2 Pulgada'),
        ('5/8', '5/8 Pulgada'),
        ('1', '1 Pulgada')
    ], string="Grosor", default='1/2', required=True)
    
    structure_gauge = fields.Selection([
        ('20', 'C-20'),
        ('22', 'C-22'),
        ('24', 'C-24'),
        ('26', 'C-26')
    ], string="Calibre", default='26', required=True)
    
    add_reinforcement = fields.Boolean(string="Refuerzos", default=False)
    
    @api.depends('length', 'height', 'faces')
    def _compute_area(self):
        for rec in self:
            # Formula: L * H * Caras (Requirement 6.1: m2 section = L * H * Caras)
            # Ensure faces is int
            f = int(rec.faces) if rec.faces else 1
            rec.area = rec.length * rec.height * f
