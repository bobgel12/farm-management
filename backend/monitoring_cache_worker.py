#!/usr/bin/env python
"""Run Rotem monitoring cache refresh on a fixed interval.

This is intended for a Railway worker service when Railway cron is not firing
reliably. It runs once immediately, then repeats every
MONITORING_CACHE_INTERVAL_SECONDS seconds.
"""

import os
import signal
import sys
import time

import django
from django.core.management import call_command
from django.db import connections
from django.utils import timezone


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chicken_management.settings_prod")

running = True


def stop(*_args):
    global running
    running = False


def main():
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    django.setup()
    interval = int(os.getenv("MONITORING_CACHE_INTERVAL_SECONDS", "600"))

    while running:
        started = timezone.now()
        print(f"monitoring_cache_worker tick_start={started.isoformat()}", flush=True)
        try:
            call_command("upsert_monitoring_cache")
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
        for _ in range(sleep_for):
            if not running:
                break
            time.sleep(1)

    print("monitoring_cache_worker status=stopping", flush=True)
    connections.close_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())

