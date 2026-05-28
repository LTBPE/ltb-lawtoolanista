"""
Bulk CSV import of court URLs into the court monitor system.

Usage:
    python import_urls.py --file courts.csv --api-url https://<func>.azurewebsites.net/api --key <function-key>

CSV format (header row required):
    name,url,state,court_type,category,notes

court_type values: state, federal, bankruptcy, appellate, other
category values:   civil, criminal, family, probate, all
state:             2-letter abbreviation (TX, CA, etc.)
"""

import argparse
import csv
import sys
import time

import requests

VALID_COURT_TYPES = {"state", "federal", "bankruptcy", "appellate", "other"}
VALID_CATEGORIES = {"civil", "criminal", "family", "probate", "all"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk import court URLs")
    parser.add_argument("--file", required=True, help="Path to the CSV file")
    parser.add_argument(
        "--api-url",
        required=True,
        help="Base API URL, e.g. https://<func>.azurewebsites.net/api",
    )
    parser.add_argument("--key", default="", help="Azure Functions host key")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV without sending any requests",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Seconds to wait between requests (default: 0.2)",
    )
    return parser.parse_args()


def validate_row(row: dict, line_num: int) -> list[str]:
    """Return a list of validation errors for a CSV row."""
    errors = []
    if not row.get("name", "").strip():
        errors.append(f"Line {line_num}: 'name' is required")
    if not row.get("url", "").strip():
        errors.append(f"Line {line_num}: 'url' is required")
    elif not row["url"].startswith(("http://", "https://")):
        errors.append(f"Line {line_num}: 'url' must start with http:// or https://")

    court_type = row.get("court_type", "other").strip().lower()
    if court_type not in VALID_COURT_TYPES:
        errors.append(
            f"Line {line_num}: court_type '{court_type}' not in {VALID_COURT_TYPES}"
        )

    category = row.get("category", "all").strip().lower()
    if category not in VALID_CATEGORIES:
        errors.append(
            f"Line {line_num}: category '{category}' not in {VALID_CATEGORIES}"
        )

    state = row.get("state", "").strip().upper()
    if state and len(state) != 2:
        errors.append(f"Line {line_num}: state '{state}' must be 2 characters")

    return errors


def main() -> None:
    args = parse_args()

    # Read and validate CSV
    rows = []
    all_errors = []
    try:
        with open(args.file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required_fields = {"name", "url"}
            if not required_fields.issubset(set(reader.fieldnames or [])):
                print(
                    f"ERROR: CSV must have at minimum these columns: {required_fields}"
                )
                sys.exit(1)

            for i, row in enumerate(reader, start=2):
                errors = validate_row(row, i)
                all_errors.extend(errors)
                rows.append(row)

    except FileNotFoundError:
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)

    if all_errors:
        print("Validation errors found:")
        for err in all_errors:
            print(f"  {err}")
        sys.exit(1)

    print(f"Validated {len(rows)} rows successfully.")

    if args.dry_run:
        print("Dry-run mode: no requests will be sent.")
        return

    # Import rows
    api_url = args.api_url.rstrip("/")
    courts_url = f"{api_url}/courts"
    session = requests.Session()
    if args.key:
        session.params = {"code": args.key}  # type: ignore

    created = 0
    skipped = 0
    errors = 0

    for i, row in enumerate(rows, start=1):
        payload = {
            "name": row["name"].strip(),
            "url": row["url"].strip(),
            "court_type": row.get("court_type", "other").strip().lower() or "other",
            "state": (row.get("state", "").strip().upper() or None),
            "category": row.get("category", "all").strip().lower() or "all",
            "notes": row.get("notes", "").strip() or None,
            "active": True,
            "js_required": False,
        }

        try:
            resp = session.post(courts_url, json=payload, timeout=30)
            if resp.status_code == 201:
                print(f"[{i}/{len(rows)}] Created: {payload['name']}")
                created += 1
            elif resp.status_code == 409:
                print(f"[{i}/{len(rows)}] Skipped (duplicate): {payload['url']}")
                skipped += 1
            else:
                print(
                    f"[{i}/{len(rows)}] ERROR {resp.status_code}: "
                    f"{payload['name']} - {resp.text[:200]}"
                )
                errors += 1
        except requests.RequestException as exc:
            print(f"[{i}/{len(rows)}] REQUEST ERROR: {payload['name']} - {exc}")
            errors += 1

        if args.delay > 0:
            time.sleep(args.delay)

    print(
        f"\nImport complete: {created} created, {skipped} skipped (duplicates), "
        f"{errors} errors"
    )
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
