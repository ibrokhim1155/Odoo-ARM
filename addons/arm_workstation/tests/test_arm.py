from odoo.tests.common import TransactionCase

class TestArm(TransactionCase):
    def setUp(self):
        super().setUp()
        ws = self.env["arm.workstation"].create({"name": "Test WS", "code": "WS1"})
        self.task = self.env["arm.production.task"].create({
            "order_number": "T-1",
            "name": "Test Task",
            "workstation_id": ws.id,
        })

    def test_flow(self):
        self.assertEqual(self.task.state, "ready")
        self.task.action_take_into_work()
        self.assertEqual(self.task.state, "in_progress")
        self.task.action_mark_done()
        self.assertEqual(self.task.state, "done")
