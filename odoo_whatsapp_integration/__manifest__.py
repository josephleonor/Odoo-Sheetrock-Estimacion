{
    'name': 'WhatsApp Integration',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'WhatsApp Integration for Sales, Purchase, Project, and Accounting',
    'description': """
        Integrate generic WhatsApp API with Odoo v18.
        Features:
        - Send messages from Sales Order, Purchase Order, Invoices, and Tasks.
        - Templates for automated messages.
        - Chat history in the unexpected chattel.
    """,
    'author': 'Antigravity',
    'depends': ['base', 'sale', 'purchase', 'account', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
