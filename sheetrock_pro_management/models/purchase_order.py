from odoo import models, fields, api
from math import radians, cos, sin, asin, sqrt

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Link to Project Task (for Supervisor RFQ creation)
    task_id = fields.Many2one('project.task', string="Tarea de Origen", help="Tarea desde la cual se generó esta RFQ")
    project_id = fields.Many2one('project.project', string="Proyecto", related='task_id.project_id', store=True, readonly=False)

    # Supplier Logistics Score
    logistics_score = fields.Float(string="Puntaje Logístico", compute="_compute_supplier_score", store=True)

    @api.depends('partner_id', 'project_id')
    def _compute_supplier_score(self):
        for po in self:
            score = 0.0
            if po.partner_id and po.project_id.partner_id:
                # 1. Distance (40%) - Inverse relationship: Closer is better
                project_loc = po.project_id.partner_id
                supplier_loc = po.partner_id
                
                dist_km = self._haversine(project_loc.partner_latitude, project_loc.partner_longitude,
                                          supplier_loc.partner_latitude, supplier_loc.partner_longitude)
                
                # Simple normalization: < 5km = 100%, > 50km = 0%
                dist_score = max(0, 100 - (dist_km * 2)) 
                score += (dist_score * 0.40)

                # 2. Historical Price (40%) - Mock logic: if rank > 0 is better
                # Real implementation needs checking historic PO lines.
                # Here we assume supplier_rank > 0 means they are verified suppliers
                price_score = 100 if po.partner_id.supplier_rank > 0 else 50
                score += (price_score * 0.40)

                # 3. Credit (20%) - Mock: credit_limit > 0
                credit_score = 100 if po.partner_id.credit_limit > 0 else 0
                score += (credit_score * 0.20)
            
            po.logistics_score = score

    def _haversine(self, lat1, lon1, lat2, lon2):
        if not lat1 or not lon1 or not lat2 or not lon2:
            return 999.0 # Max distance if coords missing
            
        # Convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # Haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers
        return c * r
