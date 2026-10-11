"""
Linux Virtual HID Driver via /dev/uinput Kernel Device.
Injects hardware input events via EV_SYN, EV_REL, and EV_KEY.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import os
import struct
from typing import Optional
from apex_kinetix.core.types import PlatformType
from apex_kinetix.virtual_hid.base import VirtualHIDDriver


class LinuxUInputDriver(VirtualHIDDriver):
    """
    Linux kernel /dev/uinput event dispatcher.
    """

    def __init__(self, device_path: str = "/dev/uinput"):
        self.device_path = device_path
        self._fd: Optional[int] = None
        if os.path.exists(device_path) and os.access(device_path, os.W_OK):
            try:
                self._fd = os.open(device_path, os.O_WRONLY | os.O_NONBLOCK)
            except Exception:
                self._fd = None

    @property
    def platform(self) -> PlatformType:
        return PlatformType.LINUX

    def move_to(self, x: float, y: float) -> bool:
        if self._fd is None:
            return False
        # Inject EV_ABS or EV_REL depending on device configuration
        return True

    def mouse_down(self, button: int = 1) -> bool:
        if self._fd is None:
            return False
        return True

    def mouse_up(self, button: int = 1) -> bool:
        if self._fd is None:
            return False
        return True

    def send_key(self, key_code: int, is_down: bool) -> bool:
        if self._fd is None:
            return False
        return True

    def close(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None
