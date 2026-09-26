from markupsafe import Markup, escape

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SheetrockSection(models.Model):
    _name = 'sheetrock.section'
    _description = 'Sección Técnica de Muro'
    _order = 'id'

    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Línea de Venta',
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(
        string='Nombre Sección',
        required=True,
        help='Ej. Baño Principal, Oficina Gerencia',
    )

    # Dimensiones
    length = fields.Float(string='Largo (m)', required=True)
    height = fields.Float(string='Alto (m)', required=True)
    gross_area = fields.Float(string='Área Bruta por Cara (m²)', compute='_compute_areas', store=True)
    openings_area = fields.Float(string='Área Aberturas (m²)', compute='_compute_areas', store=True)
    net_area = fields.Float(string='Área Neta por Cara (m²)', compute='_compute_areas', store=True)
    area = fields.Float(
        string='Área Neta Total (m²)',
        compute='_compute_areas',
        store=True,
        help='Área neta multiplicada por caras y capas. Se conserva como campo principal para compatibilidad.',
    )
    area_with_waste = fields.Float(string='Área Material con Desperdicio (m²)', compute='_compute_areas', store=True)

    # Especificaciones técnicas
    faces = fields.Selection(
        [('1', '1 Cara'), ('2', '2 Caras')],
        string='Caras',
        default='1',
        required=True,
    )
    layers = fields.Integer(string='Capas por Cara', default=1, required=True)
    waste_percent = fields.Float(string='Desperdicio (%)', default=10.0, required=True)
    stud_spacing = fields.Float(
        string='Separación Parales (m)',
        default=0.40,
        required=True,
        help='Separación típica entre ejes de parales.',
    )
    structure_type = fields.Selection(
        [('metal', 'Metal'), ('wood', 'Madera'), ('existing', 'Estructura Existente')],
        string='Tipo de Estructura',
        default='metal',
        required=True,
    )
    board_thickness = fields.Selection(
        [('1/2', '1/2 Pulgada'), ('5/8', '5/8 Pulgada'), ('1', '1 Pulgada')],
        string='Grosor',
        default='1/2',
        required=True,
    )
    structure_gauge = fields.Selection(
        [('20', 'C-20'), ('22', 'C-22'), ('24', 'C-24'), ('26', 'C-26')],
        string='Calibre',
        default='26',
        required=True,
    )
    add_reinforcement = fields.Boolean(string='Refuerzos', default=False)

    opening_ids = fields.One2many(
        'sheetrock.opening',
        'section_id',
        string='Puertas y Ventanas',
        copy=True,
    )
    elevation_html = fields.Html(
        string='Elevación 2D',
        compute='_compute_elevation_html',
        sanitize=False,
    )

    @api.depends(
        'length',
        'height',
        'faces',
        'layers',
        'waste_percent',
        'opening_ids.width',
        'opening_ids.height',
    )
    def _compute_areas(self):
        for rec in self:
            gross = max(rec.length, 0.0) * max(rec.height, 0.0)
            openings = sum(rec.opening_ids.mapped('area'))
            net = max(gross - openings, 0.0)
            faces = int(rec.faces or '1')
            layers = max(rec.layers or 1, 1)
            total = net * faces * layers
            rec.gross_area = gross
            rec.openings_area = openings
            rec.net_area = net
            rec.area = total
            rec.area_with_waste = total * (1.0 + max(rec.waste_percent, 0.0) / 100.0)

    @api.constrains('length', 'height', 'layers', 'waste_percent', 'stud_spacing')
    def _check_dimensions(self):
        for rec in self:
            if rec.length <= 0 or rec.height <= 0:
                raise ValidationError(_('El largo y el alto del muro deben ser mayores que cero.'))
            if rec.layers <= 0:
                raise ValidationError(_('Las capas por cara deben ser al menos 1.'))
            if rec.waste_percent < 0:
                raise ValidationError(_('El desperdicio no puede ser negativo.'))
            if rec.stud_spacing <= 0:
                raise ValidationError(_('La separación de parales debe ser mayor que cero.'))

    @api.depends(
        'name',
        'length',
        'height',
        'opening_ids.name',
        'opening_ids.opening_type',
        'opening_ids.width',
        'opening_ids.height',
        'opening_ids.x_position',
        'opening_ids.sill_height',
    )
    def _compute_elevation_html(self):
        for rec in self:
            rec.elevation_html = rec._build_elevation_svg()

    def _build_elevation_svg(self):
        self.ensure_one()
        if not self.length or not self.height:
            return Markup('<div class="text-muted">Indique largo y alto para generar la elevación.</div>')

        canvas_w = 900.0
        canvas_h = 460.0
        margin_x = 55.0
        margin_y = 55.0
        draw_w = canvas_w - (2 * margin_x)
        draw_h = canvas_h - (2 * margin_y)
        scale = min(draw_w / self.length, draw_h / self.height)
        wall_w = self.length * scale
        wall_h = self.height * scale
        x0 = margin_x
        y0 = margin_y + (draw_h - wall_h)

        wall_name = escape(self.name or 'Muro')

        parts = [
            f'<svg viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" '
            'style="width:100%;max-width:950px;border:1px solid #d8dadd;background:#fff">',
            f'<text x="{margin_x:.1f}" y="28" font-size="18" font-weight="600">{wall_name}</text>',
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{wall_w:.1f}" height="{wall_h:.1f}" '
            'fill="#f7f7f7" stroke="#222" stroke-width="2"/>',
        ]

        for opening in self.opening_ids.sorted(key=lambda o: (o.x_position, o.sill_height, o.id)):
            ox = x0 + opening.x_position * scale
            oy = y0 + wall_h - (opening.sill_height + opening.height) * scale
            ow = opening.width * scale
            oh = opening.height * scale
            label = 'Puerta' if opening.opening_type == 'door' else 'Ventana'
            parts.extend([
                f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{ow:.1f}" height="{oh:.1f}" '
                'fill="#ffffff" stroke="#555" stroke-width="2"/>',
                f'<text x="{ox + ow/2:.1f}" y="{oy + oh/2 - 5:.1f}" text-anchor="middle" font-size="13">{label}</text>',
                f'<text x="{ox + ow/2:.1f}" y="{oy + oh/2 + 13:.1f}" text-anchor="middle" font-size="12">'
                f'{opening.width:.2f} × {opening.height:.2f} m</text>',
            ])

        baseline = y0 + wall_h + 28
        parts.extend([
            f'<line x1="{x0:.1f}" y1="{baseline:.1f}" x2="{x0 + wall_w:.1f}" y2="{baseline:.1f}" stroke="#555"/>',
            f'<line x1="{x0:.1f}" y1="{baseline - 6:.1f}" x2="{x0:.1f}" y2="{baseline + 6:.1f}" stroke="#555"/>',
            f'<line x1="{x0 + wall_w:.1f}" y1="{baseline - 6:.1f}" x2="{x0 + wall_w:.1f}" y2="{baseline + 6:.1f}" stroke="#555"/>',
            f'<text x="{x0 + wall_w/2:.1f}" y="{baseline + 20:.1f}" text-anchor="middle" font-size="13">'
            f'{self.length:.2f} m</text>',
            f'<text x="{x0 - 12:.1f}" y="{y0 + wall_h/2:.1f}" text-anchor="middle" font-size="13" '
            f'transform="rotate(-90 {x0 - 12:.1f} {y0 + wall_h/2:.1f})">{self.height:.2f} m</text>',
            '</svg>',
        ])
        return Markup(''.join(parts))
