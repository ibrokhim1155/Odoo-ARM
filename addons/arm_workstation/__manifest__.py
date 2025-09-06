{
    "name": "ARM Workstation",
    "version": "1.0.0",
    "category": "Manufacturing",
    "summary": "Operator AРМ: take → work → done/defect",
    "depends": ["base", "web", "mail", "website"],
    "data": [
        "security/arm_security.xml",
        "security/ir.model.access.csv",

        "views/task_views.xml",
        "views/workstation_views.xml",
        "views/maintenance_views.xml",
        "views/menu.xml",
        "views/portal_templates.xml",

        "data/demo.xml",
    ],
    "application": True,
    "installable": True,
    "license": "LGPL-3",
}
