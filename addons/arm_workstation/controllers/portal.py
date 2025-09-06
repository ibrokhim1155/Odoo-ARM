from odoo import http
from odoo.http import request
from odoo.exceptions import UserError

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
        tasks = (request.env["arm.production.task"].sudo()
                 .search(domain, order="priority desc, id desc", limit=100))
        workstations = request.env["arm.workstation"].sudo().search([])
        return request.render(
            "arm_workstation.arm_operator_page_main",
            {"tasks": tasks, "workstations": workstations, "current_ws": current_ws},
        )

    @http.route("/arm/action", type="http", auth="user", methods=["POST"], csrf=True, website=True)
    def arm_action(self, **post):
        ws = post.get("ws") or ""
        def _redirect():
            return request.redirect("/arm" + (f"?ws={ws}" if ws else ""))
        try:
            task_id = int(post.get("task_id", "0"))
        except Exception:
            return _redirect()

        Task = request.env["arm.production.task"].sudo()
        task = Task.browse(task_id)
        if not task or not task.exists():
            return _redirect()

        action = (post.get("action") or "").strip()
        reason = (post.get("reason") or "").strip() or None

        try:
            if action == "take":
                task.action_take_into_work()
            elif action == "done":
                task.action_mark_done()
            elif action == "defect":
                task.action_mark_defect(reason=reason)
            elif action == "blocked":
                task.action_mark_blocked(reason=reason)
            elif action == "join":
                task.action_join_worker()
            elif action == "leave":
                task.action_leave_worker()
        except UserError:
            pass

        return _redirect()

    @http.route("/arm/scan", type="http", auth="user", website=True, methods=["GET"])
    def arm_scan_page(self, **kw):
        return request.render("arm_workstation.arm_scan_page", {})

    @http.route("/arm/scan", type="http", auth="user", website=True, methods=["POST"], csrf=True)
    def arm_scan_submit(self, **post):
        code = (post.get("code") or "").strip()
        ws = post.get("ws") or ""
        Task = request.env["arm.production.task"].sudo()

        task = False
        if code.isdigit():
            rec = Task.browse(int(code))
            if rec.exists():
                task = rec
        if not task:
            task = Task.search([("order_number", "=", code)], limit=1)

        if task:
            try:
                task.action_take_into_work()
            except UserError:
                pass

        return request.redirect("/arm" + (f"?ws={ws}" if ws else ""))
