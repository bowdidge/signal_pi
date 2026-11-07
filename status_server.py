#!/usr/bin/env python
#
# HTTP status server for model railroad signal controller.
#
# Robert Bowdidge, October 2026

import json
import threading

try:
    import http.server as http_server
except ImportError:
    import BaseHTTPServer as http_server

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver

class ThreadingServerClass(socketserver.ThreadingMixIn, http_server.HTTPServer):
    """HTTP server that handles each request in its own thread.

    ThreadingHTTPServer exists only in Python 3, so this works on both.
    """

    daemon_threads = True

    def server_bind(self):
        # HTTPServer.server_bind() calls socket.getfqdn() on the bind address.
        # Python 2's getfqdn() can block for tens of seconds when reverse DNS
        # is slow, and the name is only used in log messages, so use the
        # address as-is instead.
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host
        self.server_port = port


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Vasona Branch - Signal Controller</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <noscript><meta http-equiv="refresh" content="2"></noscript>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; background: #18181b; color: #f4f4f5; margin: 0; padding: 20px; }
    h1 { margin-top: 0; font-size: 1.4rem; color: #38bdf8; border-bottom: 1px solid #27272a; padding-bottom: 10px; }
    h2 { font-size: 1.1rem; color: #a1a1aa; margin-top: 0; }
    .layout { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
    .card { background: #27272a; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
    .items { display: flex; flex-wrap: wrap; gap: 8px; }
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
    .badge-off { background: #3f3f46; color: #a1a1aa; }
    .badge-red { background: #dc2626; color: #fff; box-shadow: 0 0 8px rgba(220,38,38,0.6); }
    .badge-green { background: #16a34a; color: #fff; box-shadow: 0 0 8px rgba(22,163,74,0.6); }
    .badge-in-active { background: #eab308; color: #000; box-shadow: 0 0 8px rgba(234,179,8,0.6); }
    .table-wrap { overflow-x: auto; max-height: 380px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }
    th, td { padding: 6px 8px; border-bottom: 1px solid #3f3f46; }
    th { color: #71717a; font-weight: 500; position: sticky; top: 0; background: #27272a; }
  </style>
</head>
<body>
  <h1>Vasona Branch &mdash; Signal Controller</h1>
  <div class="layout">
    <div class="card">
      <h2>Signal Outputs</h2>
      <div id="outputs" class="items">Loading...</div>
    </div>
    <div class="card">
      <h2>Track Inputs &amp; Switches</h2>
      <div id="inputs" class="items">Loading...</div>
    </div>
    <div class="card" style="grid-column: 1 / -1;">
      <h2>Recent Changes</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Time</th><th>Line / Signal</th><th>Type</th><th>State</th></tr>
          </thead>
          <tbody id="events">
            <tr><td colspan="4">Loading events...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    function renderBadge(name, val, isInput) {
      let cls = 'badge-off';
      if (val) {
        if (isInput) cls = 'badge-in-active';
        else if (name.endsWith('R')) cls = 'badge-red';
        else if (name.endsWith('G')) cls = 'badge-green';
        else cls = 'badge-green';
      }
      return `<span class="badge ${cls}">${name}: ${val ? 'ON' : 'OFF'}</span>`;
    }

    async function refreshStatus() {
      try {
        const resp = await fetch('/api/status');
        if (!resp.ok) return;
        const data = await resp.json();

        // Render Outputs
        const outDiv = document.getElementById('outputs');
        outDiv.innerHTML = Object.keys(data.outputs).sort().map(k => renderBadge(k, data.outputs[k], false)).join('') || 'None';

        // Render Inputs
        const inDiv = document.getElementById('inputs');
        inDiv.innerHTML = Object.keys(data.inputs).sort().map(k => renderBadge(k, data.inputs[k], true)).join('') || 'None';

        // Render Events
        const tbody = document.getElementById('events');
        if (data.recent_changes && data.recent_changes.length > 0) {
          tbody.innerHTML = data.recent_changes.map(ev => `
            <tr>
              <td>${ev.time}</td>
              <td><strong>${ev.name}</strong></td>
              <td>${ev.type}</td>
              <td>${ev.value ? 'ON' : 'OFF'}</td>
            </tr>
          `).join('');
        } else {
          tbody.innerHTML = '<tr><td colspan="4" style="color:#71717a;">No events logged yet.</td></tr>';
        }
      } catch (err) {}
    }
    refreshStatus();
    setInterval(refreshStatus, 1000);
  </script>
</body>
</html>"""


def make_status_handler(tracker):
    """Return an HTTP request handler configured to read from tracker."""

    class StatusHandler(http_server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/api/status':
                snapshot = tracker.get_snapshot()
                body = json.dumps(snapshot, indent=2).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Connection', 'close')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path == '/' or self.path == '/index.html':
                body = HTML_PAGE.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(body)
                return

            self.send_response(404)
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(b'Not Found')

        def log_message(self, format, *args):
            # Suppress normal per-request access logging to keep console output clean.
            pass

    return StatusHandler


def start_status_server(tracker, host='0.0.0.0', port=8080):
    """Start the HTTP status server in a daemon thread.

    Returns:
        (server_instance, server_thread)
    """
    handler_class = make_status_handler(tracker)
    server = ThreadingServerClass((host, port), handler_class)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server, thread


def stop_status_server(server):
    """Shut down the HTTP status server."""
    if server:
        server.shutdown()
        server.server_close()
