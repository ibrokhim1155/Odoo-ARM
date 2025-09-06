from odoo import fields, models

class ArmWorkstation(models.Model):
    _name = "arm.workstation"
    _description = "ARM Workstation"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    operator_ids = fields.Many2many("res.users", string="Operators")
    maintenance_note = fields.Text()
    last_service_date = fields.Date()

    def action_open_maintenance(self):
        self.ensure_one()
        action = self.env.ref("arm_workstation.action_arm_maintenance").read()[0]
        ctx = dict(self.env.context or {})
        ctx.update({
            "search_default_workstation_id": self.id,
            "default_workstation_id": self.id,
        })
        action["context"] = ctx
        return action
