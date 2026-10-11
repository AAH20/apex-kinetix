"""
Action Transaction and Pre/Post Invariant Verification.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import time
import uuid
from typing import Callable, Optional
from apex_kinetix.core.types import (
    ActionStatus,
    ActionTransaction,
    Point2D,
    TargetBounds,
)


class TransactionManager:
    """
    Manages atomic action transactions with pre- and post-condition invariants.
    """

    @staticmethod
    def create_transaction(
        target: TargetBounds,
        rollback_handler: Optional[Callable[[], bool]] = None,
    ) -> ActionTransaction:
        tx_id = f"tx_{uuid.uuid4().hex[:12]}"
        return ActionTransaction(
            transaction_id=tx_id,
            target=target,
            timestamp=time.time(),
            status=ActionStatus.PENDING,
            rollback_handler=rollback_handler,
        )

    @staticmethod
    def verify_precondition(
        current_pos: Point2D,
        target: TargetBounds,
        screen_width: float = 3840.0,
        screen_height: float = 2160.0,
    ) -> bool:
        """
        Validates that current position and target are within valid screen geometry.
        """
        if not (0.0 <= current_pos.x <= screen_width and 0.0 <= current_pos.y <= screen_height):
            return False
        if not (0.0 <= target.center.x <= screen_width and 0.0 <= target.center.y <= screen_height):
            return False
        if target.width <= 0.0 or target.height <= 0.0:
            return False
        return True

    @staticmethod
    def verify_postcondition(
        final_pos: Point2D,
        target: TargetBounds,
    ) -> bool:
        """
        Validates that the final trajectory point arrived inside the target bounds.
        """
        return target.contains(final_pos)
