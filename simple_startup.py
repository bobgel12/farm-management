#!/usr/bin/env python
"""
Startup script for Railway deployment.

Modes:
- web (default): start Gunicorn only (no migrations on web boot)
- migrate: run Django migrations and exit
"""

import os
import sys
import django
from django.core.management import execute_from_command_line


def configure_settings():
    """Select Django settings based on deployment context."""
    if os.getenv("DATABASE_URL") or os.getenv("RAILWAY_ENVIRONMENT"):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chicken_management.settings_prod")
        print("📋 Using production settings")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chicken_management.settings")
        print("📋 Using development settings")


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
    print("🚀 Starting Gunicorn web server...")
    print(f"🌐 Bind: 0.0.0.0:{port}")
    print(f"👷 Workers: {workers}, Threads: {threads}, Timeout: {timeout}s")
    print(f"🔗 Health check: http://0.0.0.0:{port}/api/health/")
    os.execvp(cmd[0], cmd)


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("STARTUP_MODE", "web")).lower()
    print(f"🐔 Startup mode: {mode}")

    configure_settings()
    django.setup()

    if mode == "migrate":
        run_migrations()
        return

    if mode != "web":
        raise ValueError(f"Unsupported STARTUP_MODE: {mode}")

    start_gunicorn()


if __name__ == "__main__":
    main()
