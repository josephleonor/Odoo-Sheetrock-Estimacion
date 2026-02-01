from odoo import models, api, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """
        Extend action_confirm to:
        1. Generate Purchase Orders (Material & Labor).
        2. Set up Project/Tasks with specific stages if default generation happened.
        """
        res = super(SaleOrder, self).action_confirm()
        
        for order in self:
            sheetrock_lines = order.order_line.filtered(lambda l: l.is_sheetrock_calculation)
            if sheetrock_lines:
                order._create_sheetrock_purchase_orders(sheetrock_lines)
                order._update_sheetrock_tasks(sheetrock_lines)
                
        return res

    def _create_sheetrock_purchase_orders(self, lines):
        """
        Aggregates materials from all lines and creates RFQs grouped by supplier.
        """
        # 1. Aggregate Materials
        # structure: { supplier_id: { product_id: qty } }
        materials_to_buy = {}
        
        consumption_model = self.env['sheetrock.consumption.rule']
        
        for line in lines:
            # We need to recalculate or rely on what wizard did. 
            # Re-calculating ensures data integrity.
            for section in line.sheetrock_section_ids:
                # Find rule
                rule = consumption_model.search([
                    ('faces', '=', section.faces),
                    ('board_thickness', '=', section.board_thickness),
                    ('structure_gauge', '=', section.structure_gauge),
                ], limit=1)
                
                if rule:
                    area = section.area
                    for rline in rule.line_ids:
                        if rline.is_reinforcement and not section.add_reinforcement:
                            continue
                        
                        qty = rline.quantity * area
                        # Waste 10% for materials
                        if rline.component_type != 'other':
                            qty *= 1.10
                        
                        prod = rline.product_id
                        supplier = prod.seller_ids[:1].partner_id if prod.seller_ids else False
                        
                        if not supplier:
                             # Fallback or skip?
                             # Let's group under No Supplier or handle later. For now, skip to avoid error.
                             continue
                             
                        if supplier.id not in materials_to_buy:
                            materials_to_buy[supplier.id] = {}
                        
                        if prod.id not in materials_to_buy[supplier.id]:
                            materials_to_buy[supplier.id][prod.id] = 0.0
                            
                        materials_to_buy[supplier.id][prod.id] += qty

        # 2. Create RFQs
        PurchaseOrder = self.env['purchase.order']
        PurchaseLine = self.env['purchase.order.line']
        
        for supplier_id, products in materials_to_buy.items():
            po = PurchaseOrder.create({
                'partner_id': supplier_id,
                'origin': self.name,
                'company_id': self.company_id.id,
            })
            
            for pid, qty in products.items():
                PurchaseLine.create({
                    'order_id': po.id,
                    'product_id': pid,
                    'product_qty': qty,
                    'price_unit': 0.0, # Will trigger standard price or supplier price logic
                    'date_planned': fields.Datetime.now(),
                    'product_uom': self.env['product.product'].browse(pid).uom_id.id,
                })

    def _update_sheetrock_tasks(self, lines):
        """
        Finds tasks created by these lines and applies Sheetrock settings (Contractor, Stages).
        """
        # The standard flow usually links task to sale_line_id
        tasks = self.env['project.task'].search([
            ('sale_line_id', 'in', lines.ids)
        ])
        
        # Get our custom stages ids
        stage_map = {
            'Levantamiento': self.env.ref('sheetrock_estimator.sheetrock_stage_levantamiento', raise_if_not_found=False),
        }
        initial_stage = stage_map.get('Levantamiento')
        
        for task in tasks:
            # Update specific fields if needed
            if initial_stage:
                task.write({'stage_id': initial_stage.id})

            # Assign contractor and link back to specific line for reference
            if task.sale_line_id:
                vals = {}
                if task.sale_line_id.contractor_id:
                    vals['x_contractor_id'] = task.sale_line_id.contractor_id.id
                
                # Also fill our custom link field if desired
                vals['sheetrock_sale_line_id'] = task.sale_line_id.id
                
                if vals:
                    task.write(vals)
