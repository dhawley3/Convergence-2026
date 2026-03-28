#!/usr/bin/env python3
"""Localhost dashboard to display HVAC test case results."""

from __future__ import annotations

import argparse
import html
import io
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer


class CollectingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.successes = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(test)


def run_test_suite():
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")

    stream = io.StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        resultclass=CollectingResult,
    )
    result = runner.run(suite)

    rows = []

    for test in result.successes:
        rows.append(("PASS", str(test), ""))

    for test, traceback in result.failures:
        rows.append(("FAIL", str(test), traceback.splitlines()[-1] if traceback else "Assertion failed"))

    for test, traceback in result.errors:
        rows.append(("ERROR", str(test), traceback.splitlines()[-1] if traceback else "Error"))

    for test, reason in result.skipped:
        rows.append(("SKIP", str(test), reason))

    status_priority = {"ERROR": 0, "FAIL": 1, "PASS": 2, "SKIP": 3}
    rows.sort(key=lambda row: (status_priority.get(row[0], 9), row[1]))

    summary = {
        "run": result.testsRun,
        "passed": len(result.successes),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
    }

    grouped_rows = {
        "academic": [],
        "residence": [],
        "other": [],
    }

    for row in rows:
        _, name, _ = row
        if "test_residence_hvac_integration" in name:
            grouped_rows["residence"].append(row)
        elif "test_schedule_hvac_integration" in name:
            grouped_rows["academic"].append(row)
        else:
            grouped_rows["other"].append(row)

    return summary, grouped_rows


def _table_rows_markup(rows):
    if not rows:
        return "<tr><td colspan='3'>No tests in this group.</td></tr>"

    return "\n".join(
        f"<tr><td class='status {status.lower()}'>{status}</td><td>{html.escape(name)}</td><td>{html.escape(detail)}</td></tr>"
        for status, name, detail in rows
    )


def page_html(summary, grouped_rows):
    badge = "ok" if (summary["failed"] == 0 and summary["errors"] == 0) else "bad"
    academic_rows = _table_rows_markup(grouped_rows["academic"])
    residence_rows = _table_rows_markup(grouped_rows["residence"])
    other_rows = _table_rows_markup(grouped_rows["other"])

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>HVAC Test Dashboard</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 32px; background: #f6f8fa; color: #111827; }}
    h1 {{ margin: 0 0 8px; }}
    .summary {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 14px 0 18px; }}
    .pill {{ background: #fff; border: 1px solid #d1d5db; border-radius: 999px; padding: 6px 12px; }}
    .badge.ok {{ color: #065f46; background: #d1fae5; border-color: #6ee7b7; }}
    .badge.bad {{ color: #991b1b; background: #fee2e2; border-color: #fca5a5; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d1d5db; margin-bottom: 18px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; text-align: left; padding: 10px; vertical-align: top; }}
    th {{ background: #f9fafb; }}
    .status {{ font-weight: 700; }}
    .status.pass {{ color: #065f46; }}
    .status.fail {{ color: #991b1b; }}
    .status.error {{ color: #7c2d12; }}
    .status.skip {{ color: #6b7280; }}
    .hint {{ margin-top: 14px; color: #4b5563; }}
        h2 {{ margin: 18px 0 8px; font-size: 1.05rem; }}
  </style>
</head>
<body>
    <h1>HVAC Test Dashboard</h1>
  <p>Refresh the page to rerun test cases.</p>

  <div class=\"summary\">
    <span class=\"pill badge {badge}\">{summary['passed']} passed / {summary['failed']} failed / {summary['errors']} errors</span>
    <span class=\"pill\">Total: {summary['run']}</span>
    <span class=\"pill\">Skipped: {summary['skipped']}</span>
  </div>

    <h2>Academic Building Tests</h2>
    <table>
    <thead>
      <tr><th>Status</th><th>Test Case</th><th>Detail</th></tr>
    </thead>
    <tbody>
            {academic_rows}
        </tbody>
    </table>

    <h2>Residence Hall Tests</h2>
    <table>
        <thead>
            <tr><th>Status</th><th>Test Case</th><th>Detail</th></tr>
        </thead>
        <tbody>
            {residence_rows}
        </tbody>
    </table>

    <h2>Other Tests</h2>
    <table>
        <thead>
            <tr><th>Status</th><th>Test Case</th><th>Detail</th></tr>
        </thead>
        <tbody>
            {other_rows}
    </tbody>
  </table>

  <p class=\"hint\">Server endpoint: <code>/</code> on localhost.</p>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        summary, grouped_rows = run_test_suite()
        body = page_html(summary, grouped_rows).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_, *args):
        return


def parse_args():
    parser = argparse.ArgumentParser(description="Serve HVAC unit test results on localhost")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8080, help="Localhost port")
    return parser.parse_args()


def main():
    args = parse_args()
    server = HTTPServer((args.host, args.port), DashboardHandler)
    print(f"Serving test dashboard at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")
    server.serve_forever()


if __name__ == "__main__":
    main()
