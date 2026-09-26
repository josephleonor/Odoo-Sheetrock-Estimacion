from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SheetrockLineWizardOpening(models.TransientModel):
    _name = 'sheetrock.line.wizard.opening'
    _description = 'Abertura Temporal del Wizard Sheetrock'
    _order = 'x_position, sill_height, id'

    section_id = fields.Many2one(
        'sheetrock.line.wizard.section',
        string='Muro',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(string='Referencia', required=True, default='Abertura')
    opening_type = fields.Selection(
        [('door', 'Puerta'), ('window', 'Ventana')],
        string='Tipo',
        required=True,
        default='door',
    )
    width = fields.Float(string='Ancho (m)', required=True)
    height = fields.Float(string='Alto (m)', required=True)
    x_position = fields.Float(string='Posición X (m)', required=True, default=0.0)
    sill_height = fields.Float(string='Altura desde piso (m)', required=True, default=0.0)
    area = fields.Float(string='Área (m²)', compute='_compute_area', store=True)

    @api.depends('width', 'height')
    def _compute_area(self):
        for rec in self:
            rec.area = max(rec.width, 0.0) * max(rec.height, 0.0)

    @api.constrains('section_id', 'width', 'height', 'x_position', 'sill_height')
    def _check_geometry(self):
        epsilon = 1e-6
        for rec in self:
            if rec.width <= 0 or rec.height <= 0:
                raise ValidationError(_('El ancho y el alto de la abertura deben ser mayores que cero.'))
            if rec.x_position < 0 or rec.sill_height < 0:
                raise ValidationError(_('La posición X y la altura desde piso no pueden ser negativas.'))

            section = rec.section_id
            if not section:
                continue
            if rec.x_position + rec.width > section.length + epsilon:
                raise ValidationError(_('La abertura "%s" excede el largo del muro.') % rec.name)
            if rec.sill_height + rec.height > section.height + epsilon:
                raise ValidationError(_('La abertura "%s" excede la altura del muro.') % rec.name)

            for other in section.opening_ids:
                if other == rec:
                    continue
                horizontal = (
                    max(rec.x_position, other.x_position)
                    < min(rec.x_position + rec.width, other.x_position + other.width) - epsilon
                )
                vertical = (
                    max(rec.sill_height, other.sill_height)
                    < min(rec.sill_height + rec.height, other.sill_height + other.height) - epsilon
                )
                if horizontal and vertical:
                    raise ValidationError(
                        _('Las aberturas "%s" y "%s" se solapan.') % (rec.name, other.name)
                    )
