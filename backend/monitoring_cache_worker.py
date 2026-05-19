#!/usr/bin/env python
"""Run Rotem monitoring cache refresh on a fixed interval.

This is intended for a Railway worker service when Railway cron is not firing
reliably. It runs once immediately, then repeats every
MONITORING_CACHE_INTERVAL_SECONDS seconds.
"""

import os
from pathlib import Path
import signal
import sys
import time

import django
from django.db import connections
from django.utils import timezone


BASE_DIR = Path(__file__).resolve().parent
for candidate in (BASE_DIR, BASE_DIR / "backend", BASE_DIR.parent, BASE_DIR.parent / "backend"):
    if candidate.exists():
        sys.path.insert(0, str(candidate))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chicken_management.settings_prod")

running = True


def stop(*_args):
    global running
    running = False


def main():
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    print(
        "monitoring_cache_worker boot "
        f"cwd={Path.cwd()} script_dir={BASE_DIR} pythonpath={sys.path[:4]}",
        flush=True,
    )
    django.setup()
    from houses.services.monitoring_cache_run_service import (
        claim_next_queued_manual_run,
        create_scheduled_refresh_run,
        execute_refresh_run,
    )

    interval = int(os.getenv("MONITORING_CACHE_INTERVAL_SECONDS", "600"))
    manual_poll_seconds = max(1, int(os.getenv("MONITORING_CACHE_MANUAL_POLL_SECONDS", "5")))

    def process_queued_manual_runs():
        while running:
            manual_run = claim_next_queued_manual_run()
            if not manual_run:
                return
            print(
                f"monitoring_cache_worker manual_run_start run_id={manual_run.run_id}",
                flush=True,
            )
            execute_refresh_run(manual_run)
            print(
                f"monitoring_cache_worker manual_run_finish run_id={manual_run.run_id} status={manual_run.status}",
                flush=True,
            )

    while running:
        started = timezone.now()
        print(f"monitoring_cache_worker tick_start={started.isoformat()}", flush=True)
        try:
            execute_refresh_run(create_scheduled_refresh_run())
        except Exception as exc:
            print(f"monitoring_cache_worker status=error error={exc}", flush=True)
        finally:
            connections.close_all()

        finished = timezone.now()
        elapsed = int((finished - started).total_seconds())
        print(
            f"monitoring_cache_worker tick_finish={finished.isoformat()} elapsed_seconds={elapsed}",
            flush=True,
        )

        sleep_for = max(interval - elapsed, 1)
        slept = 0
        while slept < sleep_for:
            if not running:
                break
            process_queued_manual_runs()
            chunk = min(manual_poll_seconds, sleep_for - slept)
            time.sleep(chunk)
            slept += chunk

    print("monitoring_cache_worker status=stopping", flush=True)
    connections.close_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
