{
    'name': 'Sheetrock Pro Management',
    'version': '18.0.1.0.0',
    'category': 'Construction',
    'summary': 'Advanced Sheetrock Estimation and Management',
    'description': """
        Módulo profesional para la gestión y cotización de proyectos de Sheetrock.
        Incluye configurador dinámico, cálculos de ingeniería (m2, desperdicios, andamios)
        y gestión de niveles de acabado.
    """,
    'author': 'Antigravity',
    'depends': ['base', 'product', 'purchase', 'project', 'base_geolocalize', 'sale_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sheetrock_configurator_views.xml',
        'views/purchase_order_views.xml',
        'views/project_task_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
