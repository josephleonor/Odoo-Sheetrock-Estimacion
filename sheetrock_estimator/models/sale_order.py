from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """
        Extend action_confirm to:
        1. Generate Purchase Orders (Material & Labor).
        2. Set up Project/Tasks with specific stages if default generation happened.
        """
        res = super().action_confirm()

        for order in self:
            sheetrock_lines = order.order_line.filtered(lambda line: line.is_sheetrock_calculation)
            if sheetrock_lines:
                order._create_sheetrock_purchase_orders(sheetrock_lines)
                order._update_sheetrock_tasks(sheetrock_lines)

        return res

    def _create_sheetrock_purchase_orders(self, lines):
        """Aggregate Sheetrock materials and create RFQs grouped by supplier."""
        materials_to_buy = {}
        consumption_model = self.env['sheetrock.consumption.rule']

        for line in lines:
            for section in line.sheetrock_section_ids:
                rule = consumption_model.search([
                    ('faces', '=', section.faces),
                    ('board_thickness', '=', section.board_thickness),
                    ('structure_gauge', '=', section.structure_gauge),
                ], limit=1)

                if not rule:
                    continue

                for rule_line in rule.line_ids:
                    if rule_line.is_reinforcement and not section.add_reinforcement:
                        continue

                    basis_area = (
                        section.area
                        if rule_line.component_type == 'other'
                        else section.area_with_waste
                    )
                    quantity = rule_line.quantity * basis_area
                    product = rule_line.product_id
                    supplier = product.seller_ids[:1].partner_id if product.seller_ids else False
                    if not supplier:
                        continue

                    supplier_products = materials_to_buy.setdefault(supplier.id, {})
                    supplier_products[product.id] = supplier_products.get(product.id, 0.0) + quantity

        purchase_order_model = self.env['purchase.order']
        purchase_line_model = self.env['purchase.order.line']

        for supplier_id, products in materials_to_buy.items():
            purchase_order = purchase_order_model.create({
                'partner_id': supplier_id,
                'origin': self.name,
                'company_id': self.company_id.id,
            })

            for product_id, quantity in products.items():
                product = self.env['product.product'].browse(product_id)
                purchase_line_model.create({
                    'order_id': purchase_order.id,
                    'product_id': product_id,
                    'product_qty': quantity,
                    'price_unit': 0.0,
                    'date_planned': fields.Datetime.now(),
                    'product_uom': product.uom_id.id,
                })

    def _update_sheetrock_tasks(self, lines):
        """Apply Sheetrock settings to tasks generated from the sale lines."""
        tasks = self.env['project.task'].search([
            ('sale_line_id', 'in', lines.ids),
        ])

        initial_stage = self.env.ref(
            'sheetrock_estimator.sheetrock_stage_levantamiento',
            raise_if_not_found=False,
        )

        for task in tasks:
            if initial_stage:
                task.write({'stage_id': initial_stage.id})

            if task.sale_line_id:
                values = {'sheetrock_sale_line_id': task.sale_line_id.id}
                if task.sale_line_id.contractor_id:
                    values['x_contractor_id'] = task.sale_line_id.contractor_id.id
                task.write(values)
