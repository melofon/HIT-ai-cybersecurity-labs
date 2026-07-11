from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

OUTPUT_PATH = Path("/output/findings.json")
LOG_PATH = Path("/data/security.log")


def load_snapshot() -> dict:
    try:
        data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {
        "generated_at": "No detector output yet",
        "finding_count": 0,
        "mitre_knowledge": {
            "status": "Unknown",
            "source_file": None,
            "technique_count": 0,
            "loaded_at": None,
        },
        "findings": [],
    }


def load_log() -> str:
    try:
        return LOG_PATH.read_text(encoding="utf-8")
    except Exception:
        return "Raw log is not available."


def escape(value: object) -> str:
    return html.escape("" if value is None else str(value))


def render_page() -> str:
    snapshot = load_snapshot()
    findings = snapshot.get("findings", [])
    knowledge = snapshot.get("mitre_knowledge", {})
    raw_log = load_log()

    rows = []
    for index, item in enumerate(findings, start=1):
        technique = str(item.get("mitre_technique", ""))
        url = item.get("mitre_url") or (
            f"https://attack.mitre.org/techniques/{technique}/"
            if technique else "#"
        )
        tactics = item.get("mitre_tactics", [])
        if isinstance(tactics, list):
            tactic_text = ", ".join(str(x) for x in tactics)
        else:
            tactic_text = str(tactics)

        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{escape(item.get('finding'))}</td>"
            f"<td>{escape(item.get('source_ip'))}</td>"
            f'<td><a href="{escape(url)}" target="_blank">'
            f"{escape(technique)} - {escape(item.get('mitre_name'))}"
            "</a></td>"
            f"<td>{escape(tactic_text)}</td>"
            f"<td>{escape(item.get('severity'))}</td>"
            f"<td>{escape(item.get('mitre_lookup_status'))}</td>"
            f"<td>{escape(item.get('evidence'))}</td>"
            "</tr>"
        )

    total = len(findings)
    high = sum(1 for x in findings if x.get("severity") == "High")
    medium = sum(
        1 for x in findings if x.get("severity") == "Medium"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="3">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lab 1a SOC Dashboard</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; background: #f4f6f8; color: #1f2937; }}
h1 {{ margin-bottom: 6px; }}
.subtitle {{ color: #4b5563; margin-bottom: 8px; }}
.status {{ margin-bottom: 20px; }}
.cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
.card {{ background: white; padding: 18px; border-radius: 10px; min-width: 180px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
.card strong {{ font-size: 25px; display: block; margin-top: 6px; }}
table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
th, td {{ border: 1px solid #d1d5db; padding: 9px; text-align: left; vertical-align: top; }}
th {{ background: #e5e7eb; }}
pre {{ background: #111827; color: #f9fafb; padding: 16px; border-radius: 10px; overflow-x: auto; }}
a {{ color: #1d4ed8; }}
</style>
</head>
<body>
<h1>Lab 1a SOC Dashboard</h1>
<div class="subtitle">Cyclic detection with periodic MITRE ATT&CK STIX refresh</div>
<div class="status">
<strong>Last detector scan:</strong> {escape(snapshot.get("generated_at"))}<br>
<strong>STIX status:</strong> {escape(knowledge.get("status"))}<br>
<strong>STIX source:</strong> {escape(knowledge.get("source_file") or "None")}<br>
<strong>Techniques loaded:</strong> {escape(knowledge.get("technique_count", 0))}<br>
<strong>STIX loaded at:</strong> {escape(knowledge.get("loaded_at") or "Not loaded")}
</div>

<div class="cards">
  <div class="card">Total findings<strong>{total}</strong></div>
  <div class="card">High severity<strong>{high}</strong></div>
  <div class="card">Medium severity<strong>{medium}</strong></div>
</div>

<h2>Detection Findings</h2>
<table>
<thead>
<tr>
<th>#</th><th>Activity</th><th>Source IP</th><th>MITRE ATT&CK</th>
<th>Tactic</th><th>Severity</th><th>STIX lookup</th><th>Evidence</th>
</tr>
</thead>
<tbody>
{''.join(rows) if rows else '<tr><td colspan="8">No findings detected.</td></tr>'}
</tbody>
</table>

<h2>Raw Security Log</h2>
<pre>{escape(raw_log)}</pre>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if urlparse(self.path).path not in ("/", "/index.html"):
            self.send_error(404)
            return

        body = render_page().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(format % args)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("Dashboard running on http://0.0.0.0:8000", flush=True)
    server.serve_forever()
