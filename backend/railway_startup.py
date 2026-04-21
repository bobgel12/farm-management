#!/usr/bin/env python3
"""
Railway startup helper for backend/.

Modes:
- web (default): start Gunicorn
- migrate: run migrations and exit
"""
import os
import sys
from pathlib import Path

import django
from django.core.management import execute_from_command_line

# Add the current directory to Python path (we're already in backend/)
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chicken_management.settings_prod")


def run_migrations():
    print("🔄 Running migrations...")
    execute_from_command_line(["manage.py", "migrate", "--noinput"])
    print("✅ Migrations completed successfully")


def start_gunicorn():
    port = os.getenv("PORT", "8000")
    workers = os.getenv("WEB_CONCURRENCY", "1")
    threads = os.getenv("GUNICORN_THREADS", "2")
    timeout = os.getenv("GUNICORN_TIMEOUT", "120")
    app_module = os.getenv("GUNICORN_APP_MODULE", "chicken_management.wsgi:application")

    cmd = [
        "gunicorn",
        app_module,
        "--bind",
        f"0.0.0.0:{port}",
        "--workers",
        workers,
        "--threads",
        threads,
        "--timeout",
        timeout,
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
    ]
    print(f"🚀 Starting Gunicorn on 0.0.0.0:{port}")
    print(f"👷 Workers={workers}, Threads={threads}, Timeout={timeout}s")
    os.execvp(cmd[0], cmd)


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("STARTUP_MODE", "web")).lower()
    print("🚀 Chicken House Management - Railway Startup")
    print(f"📋 Mode: {mode}")

    django.setup()

    if mode == "migrate":
        run_migrations()
        return
    if mode != "web":
        raise ValueError(f"Unsupported STARTUP_MODE: {mode}")

    start_gunicorn()


if __name__ == "__main__":
    main()
