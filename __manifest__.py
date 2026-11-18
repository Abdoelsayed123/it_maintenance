# -*- coding: utf-8 -*-
{
    'name': "IT Maintenance",
    'summary': "Manage customer devices, repair requests, spare parts and technician job cards.",
    'description': """
IT Maintenance
==============
A complete workflow for an IT maintenance / repair company:

* Device registry per customer, with warranty tracking and maintenance history
* Maintenance requests with automatic references (REQ/2026/00001)
* Workflow: New > In Progress > Waiting for Parts > Done / Cancelled
* Spare parts lines, labor cost and automatic totals
* Technician / Manager security groups with record rules
* Kanban, list, calendar, pivot and graph views
* Printable job card (PDF)
    """,
    'author': "Your Name",
    'website': "https://github.com/your-username/it_maintenance",
    'license': 'LGPL-3',
    'category': 'Services/Maintenance',
    'version': '16.0.1.0.0',

    'depends': ['base', 'mail'],

    'data': [
        'security/it_maintenance_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'report/it_request_report.xml',
        'views/it_device_views.xml',
        'views/it_request_views.xml',
        'views/it_maintenance_menus.xml',
    ],
    'demo': [
        'demo/it_maintenance_demo.xml',
    ],
    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True,
}
