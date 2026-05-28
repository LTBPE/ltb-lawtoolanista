"""
Convert a Versionista CSV export to the format expected by import_urls.py.

Usage:
    python convert_versionista.py --input urls.csv --output courts.csv

Only rows where "Page status" == "monitored" are included.
"""

import argparse
import csv
import sys

STATE_MAP = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}


def infer_court_type(url: str, site_name: str) -> str:
    url_l = url.lower()
    name_l = site_name.lower()

    if any(x in url_l for x in ["cacb.", "casb.", "canb.", "caeb.", "nynb.", "nyeb.",
                                  "nywb.", "nysb.", "bankruptcy"]):
        return "bankruptcy"

    appellate_signals = ["appellate", "appeals", "circuit", "supremecourt",
                         "cafc.", "ca1.", "ca2.", "ca3.", "ca4.", "ca5.", "ca6.",
                         "ca7.", "ca8.", "ca9.", "ca10.", "ca11.", "cadc."]
    if any(x in url_l for x in appellate_signals):
        return "appellate"
    if any(x in name_l for x in ["appellate", "court of appeals", "supreme court",
                                   "appeals court"]):
        return "appellate"

    if "uscourts.gov" in url_l:
        return "federal"
    if any(x in name_l for x in ["usdc", "u.s. district", "federal court",
                                   "u.s. court"]):
        return "federal"

    return "state"


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Versionista CSV export")
    parser.add_argument("--input", required=True, help="Versionista CSV file")
    parser.add_argument("--output", required=True, help="Output CSV for import_urls.py")
    args = parser.parse_args()

    skipped = 0
    written = 0

    with open(args.input, newline="", encoding="utf-8-sig") as fin, \
         open(args.output, "w", newline="", encoding="utf-8") as fout:

        reader = csv.DictReader(fin)
        writer = csv.DictWriter(
            fout,
            fieldnames=["name", "url", "state", "court_type", "category", "notes"],
        )
        writer.writeheader()

        for i, row in enumerate(reader, start=2):
            page_url = row.get("Page URL", "").strip()
            page_status = row.get("Page status", "").strip().lower()

            if page_status != "monitored":
                skipped += 1
                continue

            if not page_url.startswith(("http://", "https://")):
                skipped += 1
                continue

            custom_title = row.get("Custom title", "").strip()
            title = row.get("Title", "").strip()
            name = custom_title or title or page_url

            site_folder = row.get("Site folder", "").strip()
            state = STATE_MAP.get(site_folder, "")

            site_name = row.get("Site custom name", "").strip()
            court_type = infer_court_type(page_url, site_name)

            notes_parts = []
            if row.get("Page notes", "").strip():
                notes_parts.append(row["Page notes"].strip())
            if site_name:
                notes_parts.append(f"Group: {site_name}")
            notes = " | ".join(notes_parts)

            writer.writerow({
                "name": name,
                "url": page_url,
                "state": state,
                "court_type": court_type,
                "category": "all",
                "notes": notes,
            })
            written += 1

    print(f"Done: {written} rows written, {skipped} skipped (paused or invalid).")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
