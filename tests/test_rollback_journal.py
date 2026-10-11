"""
Unit tests for Transactional Rollback Journal and Safety Invariants.
Governed by Apex Growth Systems LLC.
"""

import unittest
from apex_kinetix.core.types import ActionStatus, Point2D, TargetBounds
from apex_kinetix.safety.transaction import TransactionManager
from apex_kinetix.safety.rollback_journal import RollbackJournal


class TestRollbackJournal(unittest.TestCase):
    def setUp(self):
        self.journal = RollbackJournal()
        self.target = TargetBounds(center=Point2D(500.0, 300.0), width=60.0, height=30.0)

    def test_record_and_commit(self):
        tx = TransactionManager.create_transaction(self.target)
        self.journal.record_transaction(tx)
        self.assertEqual(self.journal.pending_count(), 1)

        committed = self.journal.commit_transaction(tx.transaction_id)
        self.assertTrue(committed)
        self.assertEqual(self.journal.pending_count(), 0)
        self.assertEqual(self.journal.history_count(), 1)

    def test_lifo_rollback_execution(self):
        executed_rollbacks = []

        def rollback1():
            executed_rollbacks.append("rb1")
            return True

        def rollback2():
            executed_rollbacks.append("rb2")
            return True

        tx1 = TransactionManager.create_transaction(self.target, rollback_handler=rollback1)
        tx2 = TransactionManager.create_transaction(self.target, rollback_handler=rollback2)

        self.journal.record_transaction(tx1)
        self.journal.record_transaction(tx2)
        self.assertEqual(self.journal.pending_count(), 2)

        # Rollback all must execute in LIFO order (tx2 first, then tx1)
        count = self.journal.rollback_all()
        self.assertEqual(count, 2)
        self.assertEqual(executed_rollbacks, ["rb2", "rb1"])
        self.assertEqual(self.journal.pending_count(), 0)


if __name__ == "__main__":
    unittest.main()
