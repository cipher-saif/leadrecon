"""
report.py — turn a list of ScoredLead objects into CSV and HTML reports.
"""

import csv
import datetime


def write_csv_report(scored_leads, path):
    fieldnames = [
        "company_name", "domain", "score", "tier", "employee_count",
        "industry", "detected_tech", "top_reason",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in sorted(scored_leads, key=lambda x: x.score, reverse=True):
            writer.writerow({
                "company_name": lead.company_name,
                "domain": lead.domain,
                "score": lead.score,
                "tier": lead.tier,
                "employee_count": lead.employee_count or "",
                "industry": lead.industry or "",
                "detected_tech": "; ".join(lead.detected_tech),
                "top_reason": lead.reasons[0] if lead.reasons else "",
            })


def write_html_report(scored_leads, path):
    sorted_leads = sorted(scored_leads, key=lambda x: x.score, reverse=True)
    tier_colors = {"Hot": "#dc2626", "Warm": "#d97706", "Cold": "#2563eb", "Unreachable": "#6b7280"}

    rows_html = ""
    for lead in sorted_leads:
        color = tier_colors.get(lead.tier, "#374151")
        reasons_html = "".join(f"<li>{r}</li>" for r in lead.reasons)
        tech_html = ", ".join(lead.detected_tech) if lead.detected_tech else "—"
        rows_html += f"""
        <tr>
          <td>{lead.company_name}</td>
          <td><a href="https://{lead.domain}" target="_blank">{lead.domain}</a></td>
          <td><span class="score">{lead.score}</span></td>
          <td><span class="tier" style="background:{color}">{lead.tier}</span></td>
          <td>{lead.employee_count or "—"}</td>
          <td>{lead.industry or "—"}</td>
          <td>{tech_html}</td>
          <td><ul class="reasons">{reasons_html}</ul></td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>LeadRecon Report</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; background:#f8fafc; margin:0; padding:32px; color:#111827; }}
  h1 {{ font-size:22px; margin-bottom:4px; }}
  .subtitle {{ color:#6b7280; font-size:13px; margin-bottom:24px; }}
  table {{ border-collapse:collapse; width:100%; background:white; border-radius:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
  th {{ background:#111827; color:white; text-align:left; padding:10px 12px; font-size:12px; text-transform:uppercase; letter-spacing:0.05em; }}
  td {{ padding:10px 12px; border-bottom:1px solid #e5e7eb; font-size:13px; vertical-align:top; }}
  .score {{ font-weight:700; font-size:15px; }}
  .tier {{ color:white; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600; }}
  .reasons {{ margin:0; padding-left:16px; font-size:12px; color:#4b5563; }}
  .reasons li {{ margin-bottom:2px; }}
</style>
</head>
<body>
  <h1>LeadRecon — Scored Lead Report</h1>
  <div class="subtitle">Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} · {len(sorted_leads)} leads scored</div>
  <table>
    <thead>
      <tr>
        <th>Company</th><th>Domain</th><th>Score</th><th>Tier</th>
        <th>Employees</th><th>Industry</th><th>Detected Tech</th><th>Why This Score</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
