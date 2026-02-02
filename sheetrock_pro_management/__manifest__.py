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
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sheetrock_configurator_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
