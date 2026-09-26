{
    'name': 'Sistema de Cotización Técnica Muro Sheetrock',
    'version': '18.0.3.0.0',
    'category': 'Construction/Sales',
    'summary': 'Levantamiento, elevación 2D y cotización técnica de muros Sheetrock',
    'description': """
        Sistema técnico-profesional para levantar y cotizar muros Sheetrock como servicio.

        Características:
        - Captura técnica por muro.
        - Puertas y ventanas con posición y dimensiones.
        - Área bruta, área de aberturas, área neta y desperdicio configurable.
        - Elevación 2D automática de cada muro.
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
