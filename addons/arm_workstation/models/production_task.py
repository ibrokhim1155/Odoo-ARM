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
    worker_ids = fields.Many2many("res.users", string="Workers")
    workers_count = fields.Integer(compute="_compute_workers_count", string="Workers #")

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
                rec.duration_minutes = int((rec.end_time - rec.start_time).total_seconds() // 60)
            else:
                rec.duration_minutes = 0

    @api.depends("worker_ids")
    def _compute_workers_count(self):
        for rec in self:
            rec.workers_count = len(rec.worker_ids)

    def _safe_message_post(self, body):
        try:
            self.message_post(body=body)
        except Exception:
            pass

    def _log_event(self, action, reason=None):
        for rec in self:
            self.env["arm.task.event"].sudo().create({
                "task_id": rec.id,
                "user_id": self.env.user.id,
                "action": action,
                "reason": reason or False,
            })
            msg = _("Action: %s") % action
            if reason:
                msg += _("<br/>Reason: %s") % reason
            rec._safe_message_post(msg)

    def _ensure_current_user_is_worker(self):
        for rec in self:
            if self.env.is_superuser() or self.env.user == rec.assigned_user_id:
                continue
            if self.env.user not in rec.worker_ids:
                raise UserError(_("You must join the task to perform this action."))

    def action_join_current(self):
        for rec in self:
            rec.sudo().write({"worker_ids": [(4, self.env.user.id)]})
        self._log_event("join")

    def action_leave_current(self):
        for rec in self:
            rec.sudo().write({"worker_ids": [(3, self.env.user.id)]})
        self._log_event("leave")

    def action_take_into_work(self):
        for rec in self:
            if rec.state not in ("ready", "blocked"):
                raise UserError(_("Task must be ready or blocked."))
            rec.write({
                "state": "in_progress",
                "assigned_user_id": self.env.user.id,
                "start_time": fields.Datetime.now(),
                "blocked_reason": False,
            })
            rec.sudo().write({"worker_ids": [(4, self.env.user.id)]})
        self._log_event("take")

    def action_mark_done(self):
        self._ensure_current_user_is_worker()
        for rec in self:
            if rec.state != "in_progress":
                raise UserError(_("Task must be in progress"))
            rec.write({"state": "done", "end_time": fields.Datetime.now()})
        self._log_event("done")

    def action_mark_defect(self, reason=None):
        self._ensure_current_user_is_worker()
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
        self._ensure_current_user_is_worker()
        for rec in self:
            if rec.state not in ("in_progress", "ready"):
                raise UserError(_("Only ready/in progress tasks can be blocked."))
            rec.write({
                "state": "blocked",
                "blocked_reason": reason or _("No reason provided"),
            })
        self._log_event("blocked", reason=reason)
