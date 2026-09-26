from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SheetrockOpening(models.Model):
    _name = 'sheetrock.opening'
    _description = 'Abertura de Muro Sheetrock'
    _order = 'x_position, sill_height, id'

    section_id = fields.Many2one(
        'sheetrock.section',
        string='Muro',
        required=True,
        ondelete='cascade',
        index=True,
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
    x_position = fields.Float(
        string='Posición X (m)',
        required=True,
        default=0.0,
        help='Distancia desde el extremo izquierdo del muro.',
    )
    sill_height = fields.Float(
        string='Altura desde piso (m)',
        required=True,
        default=0.0,
        help='Para puertas normalmente es 0. Para ventanas corresponde al antepecho.',
    )
    area = fields.Float(string='Área (m²)', compute='_compute_area', store=True)

    @api.depends('width', 'height')
    def _compute_area(self):
        for rec in self:
            rec.area = max(rec.width, 0.0) * max(rec.height, 0.0)

    @api.constrains(
        'section_id',
        'width',
        'height',
        'x_position',
        'sill_height',
        'opening_type',
    )
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
                raise ValidationError(
                    _('La abertura "%s" excede el largo del muro.') % rec.name
                )
            if rec.sill_height + rec.height > section.height + epsilon:
                raise ValidationError(
                    _('La abertura "%s" excede la altura del muro.') % rec.name
                )

            for other in section.opening_ids:
                if other == rec:
                    continue
                if self._rectangles_overlap(rec, other, epsilon):
                    raise ValidationError(
                        _('Las aberturas "%s" y "%s" se solapan.') % (rec.name, other.name)
                    )

    @staticmethod
    def _rectangles_overlap(first, second, epsilon=1e-6):
        horizontal = (
            max(first.x_position, second.x_position)
            < min(first.x_position + first.width, second.x_position + second.width) - epsilon
        )
        vertical = (
            max(first.sill_height, second.sill_height)
            < min(first.sill_height + first.height, second.sill_height + second.height) - epsilon
        )
        return horizontal and vertical
