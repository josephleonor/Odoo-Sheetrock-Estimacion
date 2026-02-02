from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    purchase_ids = fields.One2many('purchase.order', 'task_id', string="Pedidos de Compra")
    
    def action_create_rfq(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        action['context'] = {
            'default_task_id': self.id,
            'default_project_id': self.project_id.id,
            'default_origin': self.name,
        }
        action['views'] = [(False, 'form')]
        return action
