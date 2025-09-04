from odoo import http
from odoo.http import request

class ArmPortal(http.Controller):

    @http.route("/arm", type="http", auth="user", website=True)
    def arm_home(self, **kw):
        tasks = request.env["arm.production.task"].sudo().search([], limit=50)
        return request.render("arm_workstation.arm_operator_page_main", {"tasks": tasks})

    @http.route("/arm/action", type="http", auth="user", methods=["POST"], csrf=True, website=True)
    def arm_action(self, **post):
        task = request.env["arm.production.task"].sudo().browse(int(post.get("task_id")))
        action = post.get("action")
        if task:
            if action == "take":
                task.action_take_into_work()
            elif action == "done":
                task.action_mark_done()
            elif action == "defect":
                task.action_mark_defect(reason=post.get("reason"))
        return request.redirect("/arm")
