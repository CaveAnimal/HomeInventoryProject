"""In-process nightly scheduler for the deep-scan reprocessing pass.

The admin page lets an operator "arm" a one-shot deep scan instead of
requiring OS-level cron/Task Scheduler setup. A lightweight background
thread wakes up periodically, and once armed + the configured nightly hour
arrives, triggers app.nightly_reprocess.run() exactly once, then disarms
itself automatically (see repository.get_setting/set_setting, keys
ARMED_KEY/LAST_RUN_KEY). Arming again is required for the next scan.

Never started under pytest -- guarded by checking whether the ``pytest``
module is loaded, which is true from the moment pytest starts (including
during test collection/import, before any PYTEST_CURRENT_TEST would be set)
so test runs never spawn a real clock-watching thread.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from datetime import date, datetime

from . import nightly_reprocess
from .database import connect
from .repository import get_setting, set_setting

CHECK_INTERVAL_SECONDS = int(os.environ.get("DEEP_SCAN_CHECK_INTERVAL_SECONDS", "300"))
DEEP_SCAN_HOUR = int(os.environ.get("DEEP_SCAN_HOUR", "2"))  # 24h local time, e.g. 2 = 2:00-2:59am
ARMED_KEY = "deep_scan_armed"
LAST_RUN_KEY = "deep_scan_last_run_date"

_thread: threading.Thread | None = None


def _tick() -> None:
    """Run once per check interval; triggers the deep scan at most once per armed click."""
    conn = connect()
    try:
        if get_setting(conn, ARMED_KEY, "false") != "true":
            return
        if datetime.now().hour != DEEP_SCAN_HOUR:
            return
        today = date.today().isoformat()
        if get_setting(conn, LAST_RUN_KEY, "") == today:
            return
        set_setting(conn, LAST_RUN_KEY, today)
        set_setting(conn, ARMED_KEY, "false")
        conn.commit()
    finally:
        conn.close()
    nightly_reprocess.run()


def _loop() -> None:
    while True:
        try:
            _tick()
        except Exception as exc:  # pragma: no cover - defensive, keep the loop alive
            print(f"[deep-scan scheduler] tick failed: {exc}")
        time.sleep(CHECK_INTERVAL_SECONDS)


def start() -> None:
    global _thread
    if _thread is not None or "pytest" in sys.modules:
        return
    _thread = threading.Thread(target=_loop, daemon=True, name="deep-scan-scheduler")
    _thread.start()
