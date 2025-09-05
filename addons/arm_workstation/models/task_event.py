from odoo import fields, models

class ArmTaskEvent(models.Model):
    _name = "arm.task.event"
    _description = "Task Events"
    _order = "create_date desc"

    task_id = fields.Many2one("arm.production.task", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", required=True)
    action = fields.Selection([("take","TAKE"),("done","DONE"),("defect","DEFECT"),("blocked","BLOCKED")], required=True)
    reason = fields.Char()
    create_date = fields.Datetime(readonly=True)
