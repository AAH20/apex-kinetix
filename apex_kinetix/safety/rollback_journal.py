"""
Transactional LIFO Saga Rollback Journal.
Guarantees O(1) push/pop of compensating actions to safely restore OS and application state.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from typing import List, Optional
from apex_kinetix.core.types import ActionStatus, ActionTransaction


class RollbackJournal:
    """
    Saga rollback manager implementing a strict LIFO stack for inverse compensating operations.
    """

    def __init__(self):
        self._stack: List[ActionTransaction] = []
        self._history: List[ActionTransaction] = []

    def record_transaction(self, tx: ActionTransaction) -> None:
        """
        Pushes a new pending transaction onto the rollback journal in O(1).
        """
        self._stack.append(tx)

    def commit_transaction(self, tx_id: str) -> bool:
        """
        Marks transaction committed and archives it.
        """
        for i, tx in enumerate(self._stack):
            if tx.transaction_id == tx_id:
                tx.status = ActionStatus.COMMITTED
                self._history.append(self._stack.pop(i))
                return True
        return False

    def rollback_latest(self) -> bool:
        """
        Pops the latest uncommitted transaction and executes its compensating action in O(1).
        Returns True if rollback executed successfully.
        """
        if not self._stack:
            return False

        tx = self._stack.pop()
        tx.status = ActionStatus.ROLLED_BACK
        success = True
        if tx.rollback_handler:
            try:
                success = tx.rollback_handler()
            except Exception:
                success = False

        self._history.append(tx)
        return success

    def rollback_all(self) -> int:
        """
        Rolls back all pending transactions in reverse order (LIFO).
        Returns count of rolled back transactions.
        """
        count = 0
        while self._stack:
            if self.rollback_latest():
                count += 1
        return count

    def pending_count(self) -> int:
        return len(self._stack)

    def history_count(self) -> int:
        return len(self._history)
