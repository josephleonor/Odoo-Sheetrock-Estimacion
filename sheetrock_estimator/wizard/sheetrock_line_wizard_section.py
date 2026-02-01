from odoo import models, fields

class SheetrockLineWizardSection(models.TransientModel):
    _name = 'sheetrock.line.wizard.section'
    _description = 'Sección del Wizard Sheetrock'
    
    wizard_id = fields.Many2one('sheetrock.line.wizard', string="Wizard", ondelete='cascade')
    name = fields.Char(string="Nombre Sección", required=True)
    length = fields.Float(string="Largo", required=True)
    height = fields.Float(string="Alto", required=True)
    faces = fields.Selection([('1', '1 Cara'), ('2', '2 Caras')], default='1', required=True)
    board_thickness = fields.Selection([('1/2', '1/2"'), ('5/8', '5/8"'), ('1', '1"')], default='1/2', required=True)
    structure_gauge = fields.Selection([('20', 'C-20'), ('22', 'C-22'), ('24', 'C-24'), ('26', 'C-26')], default='26', required=True)
    add_reinforcement = fields.Boolean(string="Refuerzos")
