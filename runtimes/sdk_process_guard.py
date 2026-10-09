"""Owned Windows process containment; no PID-tree guesses or global kills."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from time import monotonic, sleep


class _Limits(ctypes.Structure):
    _fields_ = [("user_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                ("flags", wintypes.DWORD), ("minimum", ctypes.c_size_t), ("maximum", ctypes.c_size_t),
                ("active_limit", wintypes.DWORD), ("affinity", ctypes.c_size_t),
                ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", _Limits), ("io", ctypes.c_ulonglong * 6),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]


class _Accounting(ctypes.Structure):
    _fields_ = [("times", ctypes.c_longlong * 4), ("faults", wintypes.DWORD),
                ("total", wintypes.DWORD), ("active", wintypes.DWORD), ("terminated", wintypes.DWORD)]


class SDKProcessGuard:
    """Contain an already launched, authorization-gated SDK worker.

    Ordinary descendants inherit the job; no breakaway flags are enabled.
    Unsupported platforms fail before the worker is authorized to run the SDK.
    """

    def __init__(self, process):
        if os.name != "nt":
            raise RuntimeError("confirmed SDK process containment currently requires Windows")
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        for name, args, result in (
            ("CreateJobObjectW", [ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            ("SetInformationJobObject", [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            ("AssignProcessToJobObject", [wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            ("QueryInformationJobObject", [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL),
            ("TerminateJobObject", [wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            ("CloseHandle", [wintypes.HANDLE], wintypes.BOOL),
        ):
            function = getattr(api, name)
            function.argtypes, function.restype = args, result
        self.api = api
        self.handle = api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self.parent_pid = process.pid
        self.forced = False
        self._last = None
        try:
            limits = _ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            self._check(api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
            self._check(api.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(process._handle))))
        except Exception:
            api.CloseHandle(self.handle)
            self.handle = None
            raise

    @staticmethod
    def _check(value):
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())

    def observe(self) -> dict:
        if self.handle is None:
            if self._last is None:
                raise RuntimeError("job closed without a termination observation")
            return dict(self._last)
        info = _Accounting()
        self._check(self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None))
        self._last = {
            "mechanism": "windows_job_object", "contained": True,
            "parent_pid": self.parent_pid, "active_process_count": int(info.active),
            "total_process_count": int(info.total), "forced_cleanup": self.forced,
            "termination_confirmed": info.active == 0,
        }
        return dict(self._last)

    def wait_empty(self, timeout_s: float) -> bool:
        deadline = monotonic() + timeout_s
        while True:
            if self.observe()["termination_confirmed"]:
                return True
            if monotonic() >= deadline:
                return False
            sleep(0.02)

    def terminate(self) -> None:
        if self.handle is not None:
            self._check(self.api.TerminateJobObject(self.handle, 125))
            self.forced = True

    def close_if_empty(self) -> bool:
        if not self.observe()["termination_confirmed"]:
            return False
        if self.handle is not None:
            self._check(self.api.CloseHandle(self.handle))
            self.handle = None
        return True
