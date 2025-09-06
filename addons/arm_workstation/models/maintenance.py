from odoo import fields, models

class ArmWorkstationMaintenance(models.Model):
    _name = "arm.workstation.maintenance"
    _description = "Workstation Maintenance"
    _order = "date_start desc, id desc"

    name = fields.Char(required=True)
    workstation_id = fields.Many2one("arm.workstation", required=True, index=True, ondelete="cascade")
    type = fields.Selection([("planned", "Planned"), ("breakdown", "Breakdown")], default="planned", required=True)
    state = fields.Selection([("open", "Open"), ("done", "Done")], default="open", required=True, index=True)
    date_start = fields.Datetime(default=fields.Datetime.now, required=True)
    duration_minutes = fields.Integer()
    notes = fields.Text()
    attachment_ids = fields.Many2many("ir.attachment", "arm_ws_maint_attachment_rel", "maint_id", "att_id", string="Files")
