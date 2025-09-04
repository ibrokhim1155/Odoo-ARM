from odoo import fields, models

class ArmWorkstation(models.Model):
    _name = "arm.workstation"
    _description = "ARM Workstation"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    operator_ids = fields.Many2many("res.users", string="Operators")
