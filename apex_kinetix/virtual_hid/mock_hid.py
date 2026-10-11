"""
Mock Virtual HID Driver for Deterministic Testing and Verification.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import time
from typing import List, Tuple
from apex_kinetix.core.types import PlatformType
from apex_kinetix.virtual_hid.base import VirtualHIDDriver


class MockVirtualHIDDriver(VirtualHIDDriver):
    """
    In-memory mock virtual HID driver. Records all events for verification.
    """

    def __init__(self):
        self.events: List[Tuple[str, float, float, float]] = []
        self.current_x: float = 0.0
        self.current_y: float = 0.0
        self.is_mouse_down: bool = False
        self.pressed_keys: List[int] = []

    @property
    def platform(self) -> PlatformType:
        return PlatformType.MOCK

    def move_to(self, x: float, y: float) -> bool:
        t = time.time()
        self.current_x = x
        self.current_y = y
        self.events.append(("move", x, y, t))
        return True

    def mouse_down(self, button: int = 1) -> bool:
        t = time.time()
        self.is_mouse_down = True
        self.events.append(("mouse_down", float(button), 0.0, t))
        return True

    def mouse_up(self, button: int = 1) -> bool:
        t = time.time()
        self.is_mouse_down = False
        self.events.append(("mouse_up", float(button), 0.0, t))
        return True

    def send_key(self, key_code: int, is_down: bool) -> bool:
        t = time.time()
        action = "key_down" if is_down else "key_up"
        if is_down:
            self.pressed_keys.append(key_code)
        else:
            if key_code in self.pressed_keys:
                self.pressed_keys.remove(key_code)
        self.events.append((action, float(key_code), 0.0, t))
        return True

    def clear(self) -> None:
        self.events.clear()
        self.pressed_keys.clear()
        self.is_mouse_down = False
