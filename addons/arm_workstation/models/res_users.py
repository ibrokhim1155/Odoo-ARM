from odoo import fields, models

class ResUsers(models.Model):
    _inherit = "res.users"
    arm_workstation_id = fields.Many2one("arm.workstation", string="Default Workstation")
