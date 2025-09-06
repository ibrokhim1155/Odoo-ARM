import unittest
from odoo.tests.common import TransactionCase

class TestArmWorkflow(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ws = self.env["arm.workstation"].create({"name": "WS", "code": "WS1"})
        self.task = self.env["arm.production.task"].create({
            "order_number": "T-1",
            "name": "Test Task",
            "workstation_id": self.ws.id,
            "qty": 3.0,
            "price": 5.0,
        })

    def test_take_done_amount_duration(self):
        self.assertEqual(self.task.state, "ready")
        self.task.action_take_into_work()
        self.task.action_join_current()
        if self.env.user not in self.task.worker_ids:
            self.task.write({"worker_ids": [(4, self.env.user.id)]})

        self.assertEqual(self.task.state, "in_progress")
        self.assertTrue(self.task.start_time)

        self.task.action_mark_done()
        self.assertEqual(self.task.state, "done")
        self.assertTrue(self.task.end_time)
        self.assertEqual(self.task.amount, 15.0)
        self.assertGreaterEqual(self.task.duration_minutes, 0)
