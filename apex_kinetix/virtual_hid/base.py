"""
Virtual HID Abstract Platform Contract.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from apex_kinetix.core.types import PlatformType


class VirtualHIDDriver(ABC):
    """
    Abstract interface for low-level OS kernel hardware event injection.
    """

    @property
    @abstractmethod
    def platform(self) -> PlatformType:
        pass

    @abstractmethod
    def move_to(self, x: float, y: float) -> bool:
        """Injects a hardware mouse move event."""
        pass

    @abstractmethod
    def mouse_down(self, button: int = 1) -> bool:
        """Injects a hardware mouse button down event."""
        pass

    @abstractmethod
    def mouse_up(self, button: int = 1) -> bool:
        """Injects a hardware mouse button up event."""
        pass

    @abstractmethod
    def send_key(self, key_code: int, is_down: bool) -> bool:
        """Injects a hardware keyboard scan-code event."""
        pass
