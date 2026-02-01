from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_sheetrock_service = fields.Boolean(
        string="Es Servicio Sheetrock", 
        help="Marcar para habilitar el wizard de cálculo sheetrock en ventas."
    )
