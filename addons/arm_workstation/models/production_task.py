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
        default="1",
        index=True,
        tracking=True,
    )
    planned_start = fields.Datetime("Planned Start")
    deadline = fields.Datetime("Deadline")
    qty = fields.Float("Qty", default=1.0)
    price = fields.Monetary("Price")
    amount = fields.Monetary("Amount", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id.id,
        readonly=True,
    )

    attachment_ids = fields.Many2many(
        "ir.attachment",
        "arm_task_attachment_rel",
        "task_id",
        "att_id",
        string="Files",
    )

    state = fields.Selection(
        [
            ("ready", "Готово к работе"),
            ("in_progress", "В работе"),
            ("done", "Готово"),
            ("defect", "Брак"),
            ("blocked", "Невозможно выполнить"),
        ],
        default="ready",
        tracking=True,
        index=True,
    )

    assigned_user_id = fields.Many2one("res.users", "Operator", tracking=True)
    start_time = fields.Datetime("Start Time", tracking=True)
    end_time = fields.Datetime("End Time", tracking=True)

    duration_minutes = fields.Integer(
        compute="_compute_duration", store=True, string="Duration (min)"
    )

    defect_reason = fields.Text("Defect reason")
    blocked_reason = fields.Text("Blocked reason")

    operators = fields.Many2many(
        comodel_name="res.users",
        string="Operators of WS",
        related="workstation_id.operator_ids",
        readonly=True,
    )

    @api.depends("qty", "price")
    def _compute_amount(self):
        for rec in self:
            rec.amount = (rec.qty or 0.0) * (rec.price or 0.0)

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                rec.duration_minutes = int(
                    (rec.end_time - rec.start_time).total_seconds() // 60
                )
            else:
                rec.duration_minutes = 0

    def _log_event(self, action, reason=None):
        for rec in self:
            msg = _("Action: %s") % action
            if reason:
                msg += _("<br/>Reason: %s") % reason
            rec.message_post(body=msg)

    def action_take_into_work(self):
        for rec in self:
            if rec.state not in ("ready", "blocked"):
                raise UserError(_("Task must be ready or blocked."))
            rec.write(
                {
                    "state": "in_progress",
                    "assigned_user_id": self.env.user.id,
                    "start_time": fields.Datetime.now(),
                    "blocked_reason": False,
                }
            )
        self._log_event("take_into_work")

    def action_mark_done(self):
        for rec in self:
            if rec.state != "in_progress":
                raise UserError(_("Task must be in progress"))
            rec.write({"state": "done", "end_time": fields.Datetime.now()})
        self._log_event("done")

    def action_mark_defect(self, reason=None):
        for rec in self:
            vals = {
                "state": "defect",
                "defect_reason": reason or _("No reason provided"),
                "end_time": fields.Datetime.now(),
            }
            if not rec.start_time:
                vals["start_time"] = fields.Datetime.now()
            rec.write(vals)
        self._log_event("defect", reason=reason)

    def action_mark_blocked(self, reason=None):
        for rec in self:
            if rec.state not in ("in_progress", "ready"):
                raise UserError(_("Only ready/in progress tasks can be blocked."))
            rec.write(
                {
                    "state": "blocked",
                    "blocked_reason": reason or _("No reason provided"),
                }
            )
        self._log_event("blocked", reason=reason)
