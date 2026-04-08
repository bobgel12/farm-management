#!/usr/bin/env python3
import argparse
import json
import requests

DEFAULT_BASE_URL = "http://localhost:8002/api"


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {"raw_text": response.text[:500]}


def get_token(base_url, username, password):
    resp = requests.post(
        f"{base_url}/auth/login/",
        json={"username": username, "password": password},
        timeout=15,
    )
    data = safe_json(resp)
    if resp.status_code != 200:
        print(f"❌ Login failed ({resp.status_code}): {json.dumps(data, indent=2)}")
        return None
    return data.get("token")


def api_get(base_url, token, path):
    resp = requests.get(
        f"{base_url}{path}",
        headers={"Authorization": f"Token {token}"},
        timeout=20,
    )
    return resp.status_code, safe_json(resp)


def api_post(base_url, token, path, payload):
    resp = requests.post(
        f"{base_url}{path}",
        headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    return resp.status_code, safe_json(resp)


def count_items(payload):
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return len(payload["results"])
    return 0


def run_for_farm(base_url, token, farm_identifier):
    out = {"farm_identifier": farm_identifier}

    s, p = api_get(base_url, token, f"/rotem/farms/{farm_identifier}/")
    out["farm_detail_status"] = s
    out["farm_detail_ok"] = s == 200
    out["farm_detail"] = p

    s, p = api_get(base_url, token, f"/rotem/data/by_farm/?farm_id={farm_identifier}")
    out["data_by_farm_status"] = s
    out["data_by_farm_ok"] = s == 200
    out["data_by_farm_count"] = count_items(p)

    s, p = api_get(base_url, token, f"/rotem/daily-summaries/by_farm/?farm_id={farm_identifier}")
    out["daily_summary_status"] = s
    out["daily_summary_ok"] = s == 200
    out["daily_summary_count"] = count_items(p)

    s, p = api_post(base_url, token, "/rotem/scraper/scrape_farm/", {"farm_id": farm_identifier})
    out["scrape_status"] = s
    out["scrape_ok"] = s == 200
    out["scrape_payload"] = p

    # Re-check after scrape so output reflects current state, not only pre-scrape state.
    s, p = api_get(base_url, token, f"/rotem/data/by_farm/?farm_id={farm_identifier}")
    out["post_scrape_data_status"] = s
    out["post_scrape_data_count"] = count_items(p)
    out["post_scrape_data_ok"] = s == 200

    s, p = api_get(base_url, token, f"/rotem/daily-summaries/by_farm/?farm_id={farm_identifier}")
    out["post_scrape_summary_status"] = s
    out["post_scrape_summary_count"] = count_items(p)
    out["post_scrape_summary_ok"] = s == 200
    return out


def print_result(res):
    print("\n" + "=" * 70)
    print(f"Farm {res['farm_identifier']}")
    print("=" * 70)
    print(f"farm detail:      {'OK' if res['farm_detail_ok'] else 'FAIL'} ({res['farm_detail_status']})")
    print(f"data by farm:     {'OK' if res['data_by_farm_ok'] else 'FAIL'} ({res['data_by_farm_status']}), count={res['data_by_farm_count']}")
    print(f"daily summaries:  {'OK' if res['daily_summary_ok'] else 'FAIL'} ({res['daily_summary_status']}), count={res['daily_summary_count']}")
    print(f"scrape trigger:   {'OK' if res['scrape_ok'] else 'FAIL'} ({res['scrape_status']})")
    print(f"post-scrape data: {'OK' if res['post_scrape_data_ok'] else 'FAIL'} ({res['post_scrape_data_status']}), count={res['post_scrape_data_count']}")
    print(f"post-scrape sum.: {'OK' if res['post_scrape_summary_ok'] else 'FAIL'} ({res['post_scrape_summary_status']}), count={res['post_scrape_summary_count']}")
    print("scrape payload:")
    print(json.dumps(res["scrape_payload"], indent=2)[:1000])


def main():
    parser = argparse.ArgumentParser(description="Debug Rotem data for two farms.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--token")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--farm-id-1", required=True)
    parser.add_argument("--farm-id-2", required=True)
    args = parser.parse_args()

    token = args.token
    if not token:
        if not args.username or not args.password:
            print("❌ Provide --token OR both --username and --password")
            return 2
        token = get_token(args.base_url, args.username, args.password)
        if not token:
            print("❌ Could not obtain auth token")
            return 1
        print("✅ Logged in")

    print(f"Using API: {args.base_url}")
    first = run_for_farm(args.base_url, token, str(args.farm_id_1))
    second = run_for_farm(args.base_url, token, str(args.farm_id_2))

    print_result(first)
    print_result(second)

    print("\n" + "=" * 70)
    print("Comparison")
    print("=" * 70)
    print(f"Farm1 datapoints: {first['data_by_farm_count']}")
    print(f"Farm2 datapoints: {second['data_by_farm_count']}")
    print(f"Farm1 summaries:  {first['daily_summary_count']}")
    print(f"Farm2 summaries:  {second['daily_summary_count']}")

    if first["data_by_farm_count"] > 0 and second["data_by_farm_count"] == 0:
        print("⚠️ Farm #2 lookup works but has no data. Next check credentials and scrape logs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
