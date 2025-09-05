from odoo import http
from odoo.http import request

class ArmPortal(http.Controller):
    @http.route("/arm", type="http", auth="user", website=True)
    def arm_home(self, **kw):
        current_ws = kw.get("ws")
        domain = []
        if current_ws:
            try:
                domain = [("workstation_id", "=", int(current_ws))]
            except Exception:
                domain = []

        tasks = (
            request.env["arm.production.task"]
            .sudo()
            .search(domain, order="priority desc, id desc", limit=100)
        )
        workstations = request.env["arm.workstation"].sudo().search([])
        return request.render(
            "arm_workstation.arm_operator_page_main",
            {"tasks": tasks, "workstations": workstations, "current_ws": current_ws},
        )

    @http.route(
        "/arm/action", type="http", auth="user", methods=["POST"], csrf=True, website=True
    )
    def arm_action(self, **post):
        task = (
            request.env["arm.production.task"]
            .sudo()
            .browse(int(post.get("task_id", 0)))
        )
        action = post.get("action")
        if task and task.exists():
            if action == "take":
                task.action_take_into_work()
            elif action == "done":
                task.action_mark_done()
            elif action == "defect":
                task.action_mark_defect(reason=post.get("reason"))
            elif action == "blocked":
                task.action_mark_blocked(reason=post.get("reason"))
        return request.redirect("/arm")
