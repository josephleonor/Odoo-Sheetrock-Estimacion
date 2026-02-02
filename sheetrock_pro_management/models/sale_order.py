from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta Analítica de Proyecto", copy=False)

    def action_confirm(self):
        # Create Analytic Account automatically on confirmation
        for order in self:
            if not order.analytic_account_id:
                analytic = self.env['account.analytic.account'].create({
                    'name': f"{order.name} - {order.partner_id.name}",
                    'partner_id': order.partner_id.id,
                    'plan_id': self.env['account.analytic.plan'].search([('default_applicability', '!=', False)], limit=1).id or False
                })
                order.analytic_account_id = analytic.id
        
        return super(SaleOrder, self).action_confirm()

    def create_invoice(self):
        # Validate Project Status and Photos before allowing payment request (invoice)
        for order in self:
            # Check related tasks
            # Assuming link via 'sale_order_id' field on tasks (standard Odoo) or our custom link
            tasks = self.env['project.task'].search([('sale_order_id', '=', order.id)])
            
            for task in tasks:
                 if task.stage_id.name == 'Verificado por Supervisor': # Ensuring generic match or specific ID match
                     # Check attachments
                     if not self._check_task_has_photos(task):
                         raise UserError(_("La tarea '%s' está verificada pero no tiene fotos adjuntas. Se requiere evidencia fotográfica para procesar pagos.") % task.name)
        
        return super(SaleOrder, self)._create_invoices() # Standard method name is _create_invoices or create_invoices, typically action_create_invoice calls _create_invoices

    def _check_task_has_photos(self, task):
        # Check attachment count on the task model
        count = self.env['ir.attachment'].search_count([
            ('res_model', '=', 'project.task'),
            ('res_id', '=', task.id),
            ('mimetype', 'like', 'image/')
        ])
        return count > 0

    # Margin Reporting Fields
    theoretical_margin = fields.Float(string="Margen Teórico", compute="_compute_margins")
    real_margin = fields.Float(string="Margen Real", compute="_compute_margins")
    
    @api.depends('order_line.margin', 'analytic_account_id')
    def _compute_margins(self):
        for order in self:
            # Theoretical: Standard Odoo Margin 
            order.theoretical_margin = sum(order.order_line.mapped('margin'))
            
            # Real: Sales - Real Costs (from Analytic Lines)
            if order.analytic_account_id:
                 # Fetch analytic lines: Costs are typically negative in analytic lines
                 # But we must be careful with sign convention in Odoo versions.
                 # Usually balance = credit - debit. Costs are debits (negative balance).
                 # Revenue are credits (positive balance).
                 # Real Margin = Total Balance of the account
                 
                 # Simplification: We assume all costs (Purchase, Expenses) are hit there
                 # and Invoices (Revenue) are hit there.
                 # If only costs are tracked, Real Margin = Theoretical Revenue - Real Costs header.
                 
                 # Let's assume full P&L on analytic
                 order.real_margin = order.analytic_account_id.balance
            else:
                order.real_margin = 0.0
