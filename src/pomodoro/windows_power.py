import ctypes
import time
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter

WM_POWERBROADCAST = 0x0218
PBT_APMSUSPEND = 0x0004
PBT_APMRESUMEAUTOMATIC = 0x0012


class WindowsClock:
    def __init__(self):
        self.query_awake = ctypes.WinDLL("kernel32", use_last_error=True).QueryUnbiasedInterruptTime
        self.query_awake.argtypes = [ctypes.POINTER(ctypes.c_ulonglong)]
        self.query_awake.restype = wintypes.BOOL

    def __call__(self):
        awake = ctypes.c_ulonglong()
        if not self.query_awake(ctypes.byref(awake)):
            raise ctypes.WinError(ctypes.get_last_error())
        return awake.value * 100, time.monotonic_ns()


class PowerEvents(QAbstractNativeEventFilter):
    def __init__(self, window_handle, handle_power):
        super().__init__()
        self.window_handle = window_handle
        self.handle_power = handle_power

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            event = wintypes.MSG.from_address(int(message))
            if event.hWnd == self.window_handle and event.message == WM_POWERBROADCAST:
                if event.wParam == PBT_APMSUSPEND:
                    self.handle_power(True)
                elif event.wParam == PBT_APMRESUMEAUTOMATIC:
                    self.handle_power(False)
        return False, 0
