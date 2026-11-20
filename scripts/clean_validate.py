#!/usr/bin/env python3
"""Clean and validate the supplied financial complaint analytics CSV.

Usage:
    python scripts/clean_validate.py
    python scripts/clean_validate.py --input data/raw/lecture-file.csv \
        --output data/processed/complaints_cleaned.csv --as-of-date 2026-11-20

Requires pandas. Exact duplicate complaint IDs are removed only after verifying
that duplicate-ID groups have identical source rows. No missing geography is
imputed and open-case response blanks are retained as status-related blanks.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

TEXT_COLUMNS = [
    "financial_product", "issue_category", "issue_detail", "company_name",
    "submission_channel", "company_response", "response_status",
    "timely_response", "short_complaint_summary",
]
DATE_COLUMNS = ["date_received", "response_due_date", "date_company_responded"]
EXPECTED_COLUMNS = [
    "complaint_id", "date_received", "financial_product", "issue_category",
    "issue_detail", "company_name", "state", "submission_channel",
    "response_due_date", "date_company_responded", "response_status",
    "company_response", "timely_response", "short_complaint_summary",
]


def clean_text(series: pd.Series) -> pd.Series:
    out = series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    return out.replace("", pd.NA)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/lecture-file.csv")
    parser.add_argument("--output", default="data/processed/complaints_cleaned.csv")
    parser.add_argument("--as-of-date", default="2026-11-20")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    as_of = pd.Timestamp(args.as_of_date)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    raw = pd.read_csv(input_path, dtype="string")
    missing_columns = sorted(set(EXPECTED_COLUMNS) - set(raw.columns))
    if missing_columns:
        raise SystemExit(f"Required columns missing: {missing_columns}")

    raw_rows = len(raw)
    raw["complaint_id"] = clean_text(raw["complaint_id"])
    if raw["complaint_id"].isna().any():
        raise SystemExit("Blank complaint_id values found; cannot safely de-duplicate")

    # Verify that duplicate IDs do not contain conflicting records.
    duplicate_rows = raw[raw.duplicated("complaint_id", keep=False)]
    conflicting_ids: list[str] = []
    for complaint_id, group in duplicate_rows.groupby("complaint_id", dropna=False):
        if len(group.drop_duplicates()) > 1:
            conflicting_ids.append(str(complaint_id))
    if conflicting_ids:
        raise SystemExit(
            "Conflicting duplicate complaint IDs require manual review: "
            + ", ".join(conflicting_ids[:20])
        )

    clean = raw.drop_duplicates(subset=["complaint_id"], keep="first").copy()

    for col in TEXT_COLUMNS:
        clean[col] = clean_text(clean[col])
        clean[col] = clean[col].str.lower()

    # Canonical display labels; no category or record is discarded.
    for col in ["financial_product", "issue_category", "issue_detail", "company_response"]:
        clean[col] = clean[col].str.title()
    clean["financial_product"] = clean["financial_product"].replace({
        "Buy Now, Pay Later": "Buy Now, Pay Later",
        "Checking Or Savings Account": "Checking or Savings Account",
        "Credit Card": "Credit Card",
        "Credit Reporting": "Credit Reporting",
        "Personal Loan": "Personal Loan",
        "Mortgage": "Mortgage",
    })
    clean["company_name"] = clean["company_name"].replace({
        "Bluepeak Bank": "BluePeak Bank",
        "Oakbridge Services": "OakBridge Services",
    })
    clean["submission_channel"] = clean["submission_channel"].str.title()
    clean["response_status"] = clean["response_status"].map({"open": "Open", "closed": "Closed"})
    clean["timely_response"] = clean["timely_response"].map({"yes": "Yes", "no": "No"})
    clean["state"] = clean["state"].astype("string").str.strip().str.upper().replace("", pd.NA)

    for col in DATE_COLUMNS:
        clean[col] = pd.to_datetime(clean[col], errors="coerce")
    if clean["date_received"].isna().any() or clean["response_due_date"].isna().any():
        raise SystemExit("Required received/due date contains unparseable values")

    # Validation rules derived from the supplied project data.
    if clean["complaint_id"].duplicated().any():
        raise SystemExit("Duplicate complaint_id remains after de-duplication")
    if not set(clean["response_status"].dropna().unique()).issubset({"Open", "Closed"}):
        raise SystemExit("Unexpected response_status label found")
    open_cases = clean[clean["response_status"].eq("Open")]
    closed_cases = clean[clean["response_status"].eq("Closed")]
    if not open_cases["date_company_responded"].isna().all():
        raise SystemExit("Open records unexpectedly contain response dates; inspect before accepting")
    if not open_cases["timely_response"].isna().all():
        raise SystemExit("Open records unexpectedly contain timely_response flags; inspect before accepting")

    due_interval = (clean["response_due_date"] - clean["date_received"]).dt.days
    due_interval_15 = int(due_interval.eq(15).sum())
    date_based_timely = closed_cases["date_company_responded"].le(closed_cases["response_due_date"])
    recorded_timely = closed_cases["timely_response"].eq("Yes")
    timely_mismatches = int((date_based_timely != recorded_timely).sum())

    open_due_age = (as_of - open_cases["response_due_date"]).dt.days
    open_count = int(len(open_cases))
    closed_count = int(len(closed_cases))
    total_unique = int(len(clean))
    on_time = int(closed_cases["timely_response"].eq("Yes").sum())
    late = int(closed_cases["timely_response"].eq("No").sum())

    metrics = {
        "source_file": str(input_path),
        "as_of_date": as_of.date().isoformat(),
        "raw_rows": raw_rows,
        "exact_duplicate_rows_removed": raw_rows - total_unique,
        "unique_complaints": total_unique,
        "open_complaints": open_count,
        "closed_complaints": closed_count,
        "open_complaint_rate_pct": round(open_count / total_unique * 100, 2),
        "on_time_closed_responses": on_time,
        "late_closed_responses": late,
        "on_time_response_rate_pct": round(on_time / closed_count * 100, 2),
        "late_response_rate_pct": round(late / closed_count * 100, 2),
        "open_cases_at_least_90_days_overdue": int(open_due_age.ge(90).sum()),
        "open_cases_overdue_days_mean": round(float(open_due_age.mean()), 1),
        "open_cases_overdue_days_median": round(float(open_due_age.median()), 1),
        "maximum_open_case_overdue_days": int(open_due_age.max()),
        "average_closed_response_days": round(float((closed_cases["date_company_responded"] - closed_cases["date_received"]).dt.days.mean()), 2),
        "median_closed_response_days": float((closed_cases["date_company_responded"] - closed_cases["date_received"]).dt.days.median()),
        "missing_state_values": int(clean["state"].isna().sum()),
        "reported_state_codes": int(clean["state"].nunique(dropna=True)),
        "distinct_products": int(clean["financial_product"].nunique(dropna=True)),
        "distinct_issue_categories": int(clean["issue_category"].nunique(dropna=True)),
        "distinct_companies": int(clean["company_name"].nunique(dropna=True)),
        "distinct_channels": int(clean["submission_channel"].nunique(dropna=True)),
        "rows_with_15_day_due_interval": due_interval_15,
        "closed_timeliness_flag_mismatches": timely_mismatches,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    export = clean.copy()
    for col in DATE_COLUMNS:
        export[col] = export[col].dt.strftime("%Y-%m-%d")
    export.to_csv(output_path, index=False)

    metrics_path = output_path.with_name("validation_summary.json")
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(json.dumps(metrics, indent=2))
    if total_unique != 4975 or open_count != 310 or closed_count != 4665 or on_time != 4202 or late != 463:
        raise SystemExit("Core KPI reconciliation failed; inspect the source or cleaning rules")
    if timely_mismatches != 0 or due_interval_15 != total_unique:
        raise SystemExit("Date-rule validation failed; inspect records before using results")
    print(f"\nCleaned data written to: {output_path}")
    print(f"Validation summary written to: {metrics_path}")


if __name__ == "__main__":
    main()
