from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ArmProductionTask(models.Model):
    _name = "arm.production.task"
    _description = "Production Task"
    _order = "priority desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    order_number = fields.Char("Order #", required=True, tracking=True)
    name = fields.Char("Task Name", required=True, tracking=True)
    workstation_id = fields.Many2one("arm.workstation", required=True, tracking=True)
    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High")],
        default="1", index=True
    )
    attachment_ids = fields.Many2many(
        "ir.attachment", "arm_task_attachment_rel", "task_id", "att_id",
        string="Files"
    )

    state = fields.Selection(
        [
            ("ready", "Готово к работе"),
            ("in_progress", "В работе"),
            ("done", "Готово"),
            ("defect", "Брак"),
            ("blocked", "Невозможно выполнить"),
        ],
        default="ready", tracking=True
    )

    assigned_user_id = fields.Many2one("res.users", "Operator", tracking=True)
    start_time = fields.Datetime("Start Time", tracking=True)
    end_time = fields.Datetime("End Time", tracking=True)

    duration_minutes = fields.Integer(
        compute="_compute_duration", store=True, string="Duration (min)"
    )

    defect_reason = fields.Text("Defect reason")
    blocked_reason = fields.Text("Blocked reason")

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                rec.duration_minutes = int(
                    (rec.end_time - rec.start_time).total_seconds() // 60
                )
            else:
                rec.duration_minutes = 0

    def action_take_into_work(self):
        for rec in self:
            if rec.state != "ready":
                raise UserError(_("Task must be ready"))
            rec.write({
                "state": "in_progress",
                "assigned_user_id": self.env.user.id,
                "start_time": fields.Datetime.now(),
            })

    def action_mark_done(self):
        for rec in self:
            if rec.state != "in_progress":
                raise UserError(_("Task must be in progress"))
            rec.write({
                "state": "done",
                "end_time": fields.Datetime.now(),
            })

    def action_mark_defect(self, reason=None):
        for rec in self:
            rec.write({
                "state": "defect",
                "defect_reason": reason or _("No reason provided"),
                "end_time": fields.Datetime.now(),
            })
            if reason:
                rec.message_post(body=_("Marked as defect. Reason: %s") % reason)
