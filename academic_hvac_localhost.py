import argparse
import datetime
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from schedule_hvac_integration import BuildingAutomationSystem, RegistrarSystem


def compute_hvac_status_for_now(building_id, registrar, now=None):
    """Return ON/OFF based on whether now is in any scheduled occupancy window."""
    now = now or datetime.datetime.now()
    schedule = registrar.get_today_schedule(building_id)
    occupied = any(start <= now <= end for start, end in schedule)
    return "ON" if occupied else "OFF"


def check_and_update_building(building_id, registrar, bas, now=None):
    """Compute expected HVAC status and persist it in BAS."""
    previous = bas.get_status(building_id)
    new_status = compute_hvac_status_for_now(building_id, registrar, now=now)
    bas.set_hvac(building_id, new_status)
    return {
        "building_id": building_id,
        "previous_status": previous,
        "status": new_status,
        "updated": previous != new_status,
        "checked_at": (now or datetime.datetime.now()).isoformat(timespec="seconds"),
    }

def set_building_status(building_id, status, bas, now=None):
    """Manually set a building HVAC status to ON or OFF."""
    normalized = str(status).upper()
    if normalized not in {"ON", "OFF"}:
        raise ValueError("status must be ON or OFF")

    previous = bas.get_status(building_id)
    bas.set_hvac(building_id, normalized)
    return {
        "building_id": building_id,
        "previous_status": previous,
        "status": normalized,
        "updated": previous != normalized,
        "checked_at": (now or datetime.datetime.now()).isoformat(timespec="seconds"),
        "mode": "manual",
    }


def _json_response(handler, status_code, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler):
    content_length = int(handler.headers.get("Content-Length", "0"))
    if content_length == 0:
        return {}
    raw = handler.rfile.read(content_length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _html_page():
    return """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Academic HVAC Localhost</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 28px; background: #f6f8fa; color: #0f172a; }
    h1 { margin-bottom: 8px; }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
    button { border: 1px solid #0f766e; background: #0d9488; color: #fff; border-radius: 8px; padding: 8px 12px; cursor: pointer; }
    button.secondary { border-color: #334155; background: #475569; }
    table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #cbd5e1; }
    th, td { text-align: left; padding: 10px; border-bottom: 1px solid #e2e8f0; }
    th { background: #f8fafc; }
    .on { color: #065f46; font-weight: 700; }
    .off { color: #991b1b; font-weight: 700; }
    .unknown { color: #475569; font-weight: 700; }
    .hint { margin-top: 14px; color: #334155; }
  </style>
</head>
<body>
  <h1>Academic Building HVAC Status</h1>
  <p>Use this localhost page to check and update ON/OFF status by schedule.</p>

  <div class=\"actions\">
    <button onclick=\"checkAll()\">Check + Update All Buildings</button>
    <button class=\"secondary\" onclick=\"loadStatus()\">Refresh Status</button>
  </div>

  <table>
    <thead>
      <tr><th>Building</th><th>Status</th></tr>
    </thead>
    <tbody id=\"rows\"></tbody>
  </table>

    <p class=\"hint\">API: <code>GET /api/status</code>, <code>POST /api/check-update</code>, <code>POST /api/check-update-all</code>, <code>POST /api/set-status</code></p>

  <script>
    function escapeHtml(value) {
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function rowsMarkup(statuses) {
      return Object.entries(statuses).map(([building, status]) => {
        const cls = (status || 'unknown').toLowerCase();
        return `<tr><td>${escapeHtml(building)}</td><td class=\"${cls}\">${escapeHtml(status || 'unknown')}</td></tr>`;
      }).join('');
    }

    async function loadStatus() {
      const res = await fetch('/api/status');
      const data = await res.json();
      document.getElementById('rows').innerHTML = rowsMarkup(data.statuses || {});
    }

    async function checkAll() {
      await fetch('/api/check-update-all', { method: 'POST' });
      await loadStatus();
    }

    loadStatus();
  </script>
</body>
</html>
"""


class AcademicHVACHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            body = _html_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/status":
            query = parse_qs(parsed.query)
            building_id = query.get("building_id", [None])[0]

            if building_id:
                status = self.server.bas.get_status(building_id)
                _json_response(self, 200, {"building_id": building_id, "status": status})
                return

            _json_response(self, 200, {"statuses": self.server.bas.building_status})
            return

        _json_response(self, 404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/check-update":
            try:
                payload = _read_json(self)
            except json.JSONDecodeError:
                _json_response(self, 400, {"error": "Invalid JSON body"})
                return

            building_id = payload.get("building_id")
            if not building_id:
                _json_response(self, 400, {"error": "building_id is required"})
                return

            result = check_and_update_building(
                building_id,
                registrar=self.server.registrar,
                bas=self.server.bas,
            )
            _json_response(self, 200, result)
            return

        if parsed.path == "/api/check-update-all":
            results = []
            for building_id in self.server.buildings:
                results.append(
                    check_and_update_building(
                        building_id,
                        registrar=self.server.registrar,
                        bas=self.server.bas,
                    )
                )
            _json_response(self, 200, {"updated": results})
            return

        if parsed.path == "/api/set-status":
            try:
                payload = _read_json(self)
            except json.JSONDecodeError:
                _json_response(self, 400, {"error": "Invalid JSON body"})
                return

            building_id = payload.get("building_id")
            status = payload.get("status")
            if not building_id:
                _json_response(self, 400, {"error": "building_id is required"})
                return
            if status is None:
                _json_response(self, 400, {"error": "status is required"})
                return

            try:
                result = set_building_status(
                    building_id,
                    status,
                    bas=self.server.bas,
                )
            except ValueError as exc:
                _json_response(self, 400, {"error": str(exc)})
                return

            _json_response(self, 200, result)
            return

        _json_response(self, 404, {"error": "Not found"})

    def log_message(self, format_, *args):
        return


class AcademicHVACServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, registrar, bas, buildings):
        super().__init__(server_address, RequestHandlerClass)
        self.registrar = registrar
        self.bas = bas
        self.buildings = buildings


def parse_args():
    parser = argparse.ArgumentParser(description="Serve academic building HVAC status on localhost")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8090, help="Localhost port")
    return parser.parse_args()


def main():
    args = parse_args()

    registrar = RegistrarSystem()
    bas = BuildingAutomationSystem()
    buildings = sorted(registrar.schedule.keys())

    for building_id in buildings:
        bas.set_hvac(building_id, "unknown")

    server = AcademicHVACServer(
        (args.host, args.port),
        AcademicHVACHandler,
        registrar=registrar,
        bas=bas,
        buildings=buildings,
    )

    print(f"Serving academic HVAC localhost at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")
    server.serve_forever()


if __name__ == "__main__":
    main()
