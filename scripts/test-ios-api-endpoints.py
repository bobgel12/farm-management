#!/usr/bin/env python3
"""
Smoke-test the backend API endpoints used by the iOS app.

The script logs in with username/password, discovers farms/houses/flocks/tasks,
then calls the same read endpoints used by RotemFarm-iOS. Mutating endpoints are
skipped by default and require explicit IDs plus --include-mutations.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any


DEFAULT_BASE_URL = "https://farm-management-production-54e4.up.railway.app"
DEFAULT_TIMEOUT_SECONDS = 30
SCRIPT_VERSION = "ios-live-rotem-v2"


@dataclass
class Result:
    name: str
    method: str
    path: str
    status: str
    http_status: int | None = None
    elapsed_ms: int | None = None
    note: str = ""


class API:
    def __init__(self, base_url: str, timeout: int, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verbose = verbose
        self.token: str | None = None

    def url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{normalized}"

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> tuple[int, Any, int]:
        body = None
        headers = {"Content-Type": "application/json"}
        if auth:
            if not self.token:
                raise RuntimeError("auth requested before login")
            headers["Authorization"] = f"Token {self.token}"
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.url(path),
            data=body,
            headers=headers,
            method=method.upper(),
        )
        full_url = self.url(path)
        if self.verbose:
            auth_label = "auth" if auth else "no-auth"
            payload_label = f" payload={redact_payload(payload)}" if payload else ""
            print(f"--> {method.upper():5} {full_url} [{auth_label}, timeout={self.timeout}s]{payload_label}", flush=True)
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read()
                elapsed_ms = int((time.monotonic() - started) * 1000)
                if self.verbose:
                    print(f"<-- {response.status} {method.upper():5} {full_url} {elapsed_ms}ms {len(raw)} bytes", flush=True)
                return response.status, self.decode(raw), elapsed_ms
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            elapsed_ms = int((time.monotonic() - started) * 1000)
            if self.verbose:
                print(f"<-- {exc.code} {method.upper():5} {full_url} {elapsed_ms}ms {len(raw)} bytes", flush=True)
            return exc.code, self.decode(raw), elapsed_ms
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - started) * 1000)
            if self.verbose:
                print(f"<!! {method.upper():5} {full_url} failed after {elapsed_ms}ms: {exc}", flush=True)
            raise

    @staticmethod
    def decode(raw: bytes) -> Any:
        if not raw:
            return None
        text = raw.decode("utf-8", errors="replace")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text


def collection(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return [item for item in payload["results"] if isinstance(item, dict)]
    return []


def endpoint(
    name: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    auth: bool = True,
    optional: bool = False,
) -> dict[str, Any]:
    return {
        "name": name,
        "method": method,
        "path": path,
        "payload": payload,
        "auth": auth,
        "optional": optional,
    }


def redact_payload(payload: dict[str, Any] | None) -> str:
    if not payload:
        return "{}"
    redacted = {}
    for key, value in payload.items():
        if key.lower() in {"password", "token", "authorization"}:
            redacted[key] = "***"
        else:
            redacted[key] = value
    return json.dumps(redacted, default=str)


def run_endpoint(api: API, spec: dict[str, Any]) -> tuple[Result, Any]:
    if api.verbose:
        print(f"\n=== {spec['name']} ===", flush=True)
    started = time.monotonic()
    try:
        status_code, payload, elapsed_ms = api.request(
            spec["method"],
            spec["path"],
            payload=spec.get("payload"),
            auth=spec.get("auth", True),
        )
        ok = 200 <= status_code < 300
        result = Result(
            name=spec["name"],
            method=spec["method"],
            path=spec["path"],
            status="PASS" if ok else ("WARN" if spec.get("optional") else "FAIL"),
            http_status=status_code,
            elapsed_ms=elapsed_ms,
            note=summarize_payload(payload) if ok else summarize_error(payload),
        )
        if api.verbose:
            print(f"Result: {result.status} {result.note}", flush=True)
            print(f"Response preview: {preview_payload(payload)}", flush=True)
        return result, payload
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic script
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if api.verbose:
            print(f"Result: {'WARN' if spec.get('optional') else 'FAIL'} {exc}", flush=True)
        return (
            Result(
                name=spec["name"],
                method=spec["method"],
                path=spec["path"],
                status="WARN" if spec.get("optional") else "FAIL",
                elapsed_ms=elapsed_ms,
                note=str(exc),
            ),
            None,
        )


def summarize_payload(payload: Any) -> str:
    if isinstance(payload, list):
        return f"{len(payload)} items"
    if isinstance(payload, dict):
        if "data" in payload and isinstance(payload.get("data"), dict):
            keys = ", ".join(list(payload["data"].keys())[:5])
            return f"data keys: {keys}"
        if "results" in payload and isinstance(payload["results"], list):
            return f"{len(payload['results'])} results"
        keys = ", ".join(list(payload.keys())[:5])
        return f"keys: {keys}"
    if payload is None:
        return "empty"
    return str(payload)[:80]


def summarize_error(payload: Any) -> str:
    if isinstance(payload, dict):
        return json.dumps(payload, default=str)[:240]
    if payload is None:
        return "empty error response"
    return str(payload)[:240]


def preview_payload(payload: Any, max_chars: int = 1200) -> str:
    if payload is None:
        return "<empty>"
    if isinstance(payload, (dict, list)):
        text = json.dumps(payload, indent=2, default=str)
    else:
        text = str(payload)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... <truncated>"


def print_result(result: Result) -> None:
    status_icon = {"PASS": "PASS", "WARN": "WARN", "SKIP": "SKIP"}.get(result.status, "FAIL")
    code = "" if result.http_status is None else f" {result.http_status}"
    elapsed = "" if result.elapsed_ms is None else f" {result.elapsed_ms}ms"
    print(f"{status_icon:4} {result.method:5} {result.path}{code}{elapsed} - {result.name}")
    if result.note:
        print(f"     {result.note}")


def first_id(items: list[dict[str, Any]]) -> int | None:
    for item in items:
        raw = item.get("id")
        if isinstance(raw, int):
            return raw
    return None


def api_root(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/api"):
        return normalized[:-4]
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test backend endpoints used by RotemFarm-iOS.",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend root URL, default: %(default)s")
    parser.add_argument("--username", default=os.environ.get("ROTEM_IOS_USERNAME"), help="Login username")
    parser.add_argument("--password", default=os.environ.get("ROTEM_IOS_PASSWORD"), help="Login password")
    parser.add_argument("--farm-id", type=int, help="Only test a specific farm ID")
    parser.add_argument("--house-id", type=int, help="Only test a specific house ID")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Request timeout seconds")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report")
    parser.add_argument("--include-refresh", action="store_true", help="Call refresh/scrape endpoints that hit Rotem")
    parser.add_argument("--include-mutations", action="store_true", help="Call mutating endpoints when IDs are provided")
    parser.add_argument("--task-id", type=int, help="Task ID for optional task status mutation")
    parser.add_argument("--alert-id", type=int, help="Water alert ID for optional alert mutations")
    parser.add_argument("--program-id", type=int, help="Program ID for optional program endpoints")
    parser.add_argument("--all-farms", action="store_true", help="Test every discovered farm instead of only the first one")
    parser.add_argument("--all-houses", action="store_true", help="Test every discovered house instead of only the first one")
    parser.add_argument("--all-flocks", action="store_true", help="Test every discovered flock instead of only the first one")
    parser.add_argument("--quiet", action="store_true", help="Only print the final report, not per-request progress logs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.username or not args.password:
        print("Missing credentials. Pass --username/--password or set ROTEM_IOS_USERNAME/ROTEM_IOS_PASSWORD.", file=sys.stderr)
        return 2

    api = API(api_root(args.base_url), timeout=args.timeout, verbose=not args.quiet and not args.json)
    results: list[Result] = []
    if api.verbose:
        print(f"iOS API endpoint smoke test ({SCRIPT_VERSION})", flush=True)
        print(f"Base URL: {api.base_url}", flush=True)
        print(f"Timeout: {args.timeout}s per request", flush=True)
        print("Monitoring mode: live Rotem endpoints only", flush=True)
        print("Mutations: " + ("enabled" if args.include_mutations else "skipped"), flush=True)
        print("Refresh calls: " + ("enabled" if args.include_refresh else "skipped"), flush=True)

    login_spec = endpoint(
        "Auth login",
        "POST",
        "/api/auth/login/",
        payload={"username": args.username, "password": args.password},
        auth=False,
    )
    login_result, login_payload = run_endpoint(api, login_spec)
    results.append(login_result)
    if login_result.status != "PASS" or not isinstance(login_payload, dict) or not login_payload.get("token"):
        emit(results, args.json)
        return 1
    api.token = str(login_payload["token"])

    core_specs = [
        endpoint("Current user", "GET", "/api/auth/user/"),
        endpoint("Farm list", "GET", "/api/farms/"),
        endpoint("Program list", "GET", "/api/programs/"),
    ]

    farms: list[dict[str, Any]] = []
    programs: list[dict[str, Any]] = []
    for spec in core_specs:
        result, payload = run_endpoint(api, spec)
        results.append(result)
        if spec["name"] == "Farm list" and result.status == "PASS":
            farms = collection(payload)
        if spec["name"] == "Program list" and result.status == "PASS":
            programs = collection(payload)

    if args.farm_id:
        farm_ids = [args.farm_id]
    else:
        farm_ids = [item["id"] for item in farms if isinstance(item.get("id"), int)]
        if not args.all_farms:
            farm_ids = farm_ids[:1]

    if not farm_ids:
        results.append(Result("Discovered farms", "GET", "/api/farms/", "SKIP", note="No farm IDs available"))

    discovered_house_ids: list[int] = []
    discovered_flock_ids: list[int] = []
    discovered_task_ids: list[int] = []

    for farm_id in farm_ids:
        farm_specs = [
            endpoint("Farm detail", "GET", f"/api/farms/{farm_id}/"),
            endpoint("Farm integration status", "GET", f"/api/farms/{farm_id}/integration_status/"),
            endpoint("Farm houses", "GET", f"/api/farms/{farm_id}/houses/"),
            endpoint("iOS farm snapshot (live)", "GET", f"/api/farms/{farm_id}/ios/snapshot/?mode=live"),
            endpoint("Farm monitoring dashboard (live)", "GET", f"/api/farms/{farm_id}/houses/monitoring/dashboard/?mode=live"),
            endpoint("Farm monitoring snapshot (live)", "GET", f"/api/farms/{farm_id}/houses/monitoring/snapshot/?mode=live"),
            endpoint("Flocks by farm", "GET", f"/api/flocks/?farm_id={farm_id}"),
            endpoint("Workers by farm", "GET", f"/api/workers/?farm_id={farm_id}"),
        ]
        if args.include_refresh:
            farm_specs.append(endpoint("Farm monitoring refresh", "POST", f"/api/farms/{farm_id}/houses/monitoring/refresh/", payload={}))

        for spec in farm_specs:
            result, payload = run_endpoint(api, spec)
            results.append(result)
            if spec["name"] == "Farm houses" and result.status == "PASS":
                for house in collection(payload):
                    if isinstance(house.get("id"), int):
                        discovered_house_ids.append(house["id"])
            if spec["name"] == "Flocks by farm" and result.status == "PASS":
                for flock in collection(payload):
                    if isinstance(flock.get("id"), int):
                        discovered_flock_ids.append(flock["id"])

    house_ids = [args.house_id] if args.house_id else sorted(set(discovered_house_ids))
    if not args.house_id and not args.all_houses:
        house_ids = house_ids[:1]
    if not house_ids:
        results.append(Result("Discovered houses", "GET", "/api/farms/{id}/houses/", "SKIP", note="No house IDs available"))

    for house_id in house_ids:
        house_specs = [
            endpoint("House monitoring latest (live)", "GET", f"/api/houses/{house_id}/monitoring/latest/?mode=live"),
            endpoint("House monitoring history (live)", "GET", f"/api/houses/{house_id}/monitoring/history/?mode=live&limit=24"),
            endpoint("House monitoring KPIs (live)", "GET", f"/api/houses/{house_id}/monitoring/kpis/?mode=live"),
            endpoint("House heater history (live)", "GET", f"/api/houses/{house_id}/heater-history/?mode=live"),
            endpoint("House water alerts", "GET", f"/api/houses/{house_id}/water/alerts/?include_resolved=true"),
            endpoint("House tasks", "GET", f"/api/houses/{house_id}/tasks/"),
            endpoint("Rotem water history", "GET", f"/api/rotem/daily-summaries/water-history/?house_id={house_id}&days=5", optional=True),
            endpoint("Rotem temperature history", "GET", f"/api/rotem/daily-summaries/temperature-history/?house_id={house_id}", optional=True),
            endpoint("Rotem feed history", "GET", f"/api/rotem/daily-summaries/feed-history/?house_id={house_id}&days=5", optional=True),
        ]
        for spec in house_specs:
            result, payload = run_endpoint(api, spec)
            results.append(result)
            if spec["name"] == "House tasks" and result.status == "PASS":
                for task in collection(payload):
                    if isinstance(task.get("id"), int):
                        discovered_task_ids.append(task["id"])

    flock_ids = sorted(set(discovered_flock_ids))
    if not args.all_flocks:
        flock_ids = flock_ids[:1]
    for flock_id in flock_ids:
        for spec in [
            endpoint("Flock detail", "GET", f"/api/flocks/{flock_id}/"),
            endpoint("Flock performance", "GET", f"/api/flocks/{flock_id}/performance/"),
        ]:
            result, _ = run_endpoint(api, spec)
            results.append(result)

    program_id = args.program_id or first_id(programs)
    if program_id:
        for spec in [
            endpoint("Program tasks", "GET", f"/api/programs/{program_id}/tasks/"),
            endpoint("Program tasks for day 0", "GET", f"/api/programs/{program_id}/tasks/day/0/"),
        ]:
            result, _ = run_endpoint(api, spec)
            results.append(result)
    else:
        results.append(Result("Program detail endpoints", "GET", "/api/programs/{id}/tasks/", "SKIP", note="No program ID available"))

    if args.include_mutations:
        mutation_specs: list[dict[str, Any]] = []
        task_id = args.task_id or first_int(discovered_task_ids)
        if task_id:
            mutation_specs.append(endpoint("Update task status", "POST", f"/api/tasks/{task_id}/status/", payload={"status": "pending"}))
        else:
            results.append(Result("Update task status", "POST", "/api/tasks/{id}/status/", "SKIP", note="No task ID available"))

        if args.alert_id:
            mutation_specs.extend(
                [
                    endpoint("Acknowledge water alert", "POST", f"/api/houses/water/alerts/{args.alert_id}/acknowledge/", payload={}),
                    endpoint("Snooze water alert", "POST", f"/api/houses/water/alerts/{args.alert_id}/snooze/", payload={"hours": 1}),
                    endpoint("Resolve water alert", "POST", f"/api/houses/water/alerts/{args.alert_id}/resolve/", payload={}),
                ]
            )
        else:
            results.append(Result("Water alert mutations", "POST", "/api/houses/water/alerts/{id}/...", "SKIP", note="Pass --alert-id to test"))

        for spec in mutation_specs:
            result, _ = run_endpoint(api, spec)
            results.append(result)
    else:
        results.append(Result("Mutating endpoints", "POST", "task/alert/program mutations", "SKIP", note="Pass --include-mutations to run"))

    emit(results, args.json)
    return 1 if any(result.status == "FAIL" for result in results) else 0


def first_int(values: list[int]) -> int | None:
    return values[0] if values else None


def emit(results: list[Result], json_output: bool) -> None:
    if json_output:
        print(json.dumps([asdict(result) for result in results], indent=2))
        return

    for result in results:
        print_result(result)

    passed = sum(1 for result in results if result.status == "PASS")
    warned = sum(1 for result in results if result.status == "WARN")
    skipped = sum(1 for result in results if result.status == "SKIP")
    failed = sum(1 for result in results if result.status == "FAIL")
    total = len(results)
    print()
    print(f"Summary: {passed} passed, {warned} warnings, {skipped} skipped, {failed} failed ({total} checks)")


if __name__ == "__main__":
    sys.exit(main())
