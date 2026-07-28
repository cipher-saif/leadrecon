"""
main.py — LeadRecon CLI entry point.

Usage:
    python main.py --input data/input_leads.csv --output data/output_scored

Input CSV columns expected:
    company_name, domain, employee_count (optional), industry (optional)
"""

import argparse
import csv
import sys

from leadrecon.fingerprint import fingerprint_site
from leadrecon.enrich import enrich_from_row
from leadrecon.scorer import score_lead
from leadrecon.report import write_csv_report, write_html_report


def load_leads(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run(input_path, output_prefix):
    rows = load_leads(input_path)
    scored_leads = []

    print(f"Loaded {len(rows)} leads from {input_path}\n")

    for i, row in enumerate(rows, start=1):
        company_name = row.get("company_name", "").strip()
        domain = row.get("domain", "").strip()

        if not domain:
            print(f"[{i}/{len(rows)}] Skipping '{company_name}' — no domain provided")
            continue

        print(f"[{i}/{len(rows)}] Scanning {company_name} ({domain})...")

        fp_result = fingerprint_site(domain)
        enrich_result = enrich_from_row(row)
        scored = score_lead(company_name, domain, fp_result, enrich_result)
        scored_leads.append(scored)

        print(f"    -> Score: {scored.score}  Tier: {scored.tier}")

    csv_path = f"{output_prefix}.csv"
    html_path = f"{output_prefix}.html"
    write_csv_report(scored_leads, csv_path)
    write_html_report(scored_leads, html_path)

    print(f"\nDone. {len(scored_leads)} leads scored.")
    print(f"CSV report:  {csv_path}")
    print(f"HTML report: {html_path}")

    hot = [l for l in scored_leads if l.tier == "Hot"]
    if hot:
        print(f"\n🔥 {len(hot)} Hot lead(s):")
        for lead in sorted(hot, key=lambda x: x.score, reverse=True):
            print(f"   - {lead.company_name} ({lead.domain}) — score {lead.score}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LeadRecon — tech-stack recon and ICP lead scoring.")
    parser.add_argument("--input", default="data/input_leads.csv", help="Path to input leads CSV")
    parser.add_argument("--output", default="data/output_scored", help="Output file prefix (no extension)")
    args = parser.parse_args()

    try:
        run(args.input, args.output)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
