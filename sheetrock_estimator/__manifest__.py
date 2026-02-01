{
    'name': 'Sistema de Cotización Técnica Muro Sheetrock',
    'version': '18.0.2.0.0',
    'category': 'Construction/Sales',
    'summary': 'Cotización técnica y ejecución de muros de Sheetrock',
    'description': """
        Sistema técnico-profesional para cotizar muros Sheetrock como servicio.
        
        Características:
        - Wizard de captura técnica por línea de venta.
        - Modelo de secciones con dimensiones (Largo, Alto, Caras, etc).
        - Matriz configurable de consumo de materiales por m2.
        - Tarifario de mano de obra.
        - Generación automática de Presupuesto Interno (Materiales + MO + Transporte).
        - Generación automática de RFQ/OC y Tareas de Proyecto.
    """,
    'author': 'Antigravity',
    'depends': ['sale', 'sale_management', 'project', 'purchase', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/project_stages_data.xml',
        'wizard/sheetrock_line_wizard_views.xml',
        'views/sheetrock_master_data_views.xml',
        'views/sale_order_views.xml',
        'views/project_task_views.xml',
        'report/sheetrock_internal_report.xml',
        'report/sheetrock_internal_report_template.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
