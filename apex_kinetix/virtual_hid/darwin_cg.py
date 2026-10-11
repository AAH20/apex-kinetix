"""
macOS CoreGraphics Native Virtual HID Driver.
Posts hardware mouse and keyboard events directly to kCGHIDEventTap.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import ctypes
from typing import Optional
from apex_kinetix.core.types import PlatformType
from apex_kinetix.virtual_hid.base import VirtualHIDDriver


class DarwinCoreGraphicsDriver(VirtualHIDDriver):
    """
    macOS CoreGraphics event tap injector.
    """

    def __init__(self):
        self._cg = None
        try:
            self._cg = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
            )
        except Exception:
            try:
                self._cg = ctypes.cdll.LoadLibrary(
                    "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
                )
            except Exception:
                self._cg = None

    @property
    def platform(self) -> PlatformType:
        return PlatformType.DARWIN

    def move_to(self, x: float, y: float) -> bool:
        if not self._cg:
            return False
        try:
            # CGPoint is (double x, double y)
            class CGPoint(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

            point = CGPoint(x=float(x), y=float(y))
            # kCGEventMouseMoved = 5, kCGMouseButtonLeft = 0, kCGHIDEventTap = 0
            event = self._cg.CGEventCreateMouseEvent(None, 5, point, 0)
            if event:
                self._cg.CGEventPost(0, event)
                self._cg.CFRelease(event)
                return True
        except Exception:
            return False
        return False

    def mouse_down(self, button: int = 1) -> bool:
        if not self._cg:
            return False
        try:
            # kCGEventLeftMouseDown = 1
            event_type = 1 if button == 1 else 3
            # Use current cursor position or 0,0
            class CGPoint(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

            point = CGPoint(x=0.0, y=0.0)
            event = self._cg.CGEventCreateMouseEvent(None, event_type, point, button - 1)
            if event:
                self._cg.CGEventPost(0, event)
                self._cg.CFRelease(event)
                return True
        except Exception:
            return False
        return False

    def mouse_up(self, button: int = 1) -> bool:
        if not self._cg:
            return False
        try:
            # kCGEventLeftMouseUp = 2
            event_type = 2 if button == 1 else 4
            class CGPoint(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

            point = CGPoint(x=0.0, y=0.0)
            event = self._cg.CGEventCreateMouseEvent(None, event_type, point, button - 1)
            if event:
                self._cg.CGEventPost(0, event)
                self._cg.CFRelease(event)
                return True
        except Exception:
            return False
        return False

    def send_key(self, key_code: int, is_down: bool) -> bool:
        if not self._cg:
            return False
        try:
            event = self._cg.CGEventCreateKeyboardEvent(None, ctypes.c_uint16(key_code), ctypes.c_bool(is_down))
            if event:
                self._cg.CGEventPost(0, event)
                self._cg.CFRelease(event)
                return True
        except Exception:
            return False
        return False
