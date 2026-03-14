# -*- coding: utf-8 -*-
"""Local HTTP server for animated treemap HTML and dynamic data.json updates."""

import json
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

HOST = "127.0.0.1"
PORT = 8765
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN_DIR = os.path.join(PROJECT_ROOT, "bin")
DATA_PATH = os.path.join(BIN_DIR, "data.json")

DEFAULT_DATA = [
    {"name": "Living", "parent": "Indoor", "value": 222},
    {"name": "Kitchen", "parent": "Indoor", "value": 150},
    {"name": "Bedroom", "parent": "Terrace", "value": 250},
    {"name": "Deck", "parent": "Outdoor", "value": 200},
    {"name": "Garden", "parent": "Outdoor", "value": 150},
    {"name": "Pool", "parent": "Outdoor", "value": 15},
]


def ensure_data_file():
    """Create bin/data.json if missing so treemap has initial content."""
    if not os.path.isdir(BIN_DIR):
        os.makedirs(BIN_DIR)
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=2)


def write_json_atomic(path, payload):
    """Write JSON atomically to avoid partial reads from the browser."""
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)


def normalize_payload(payload):
    """Accept common GH payload shapes and return list[dict]."""
    # If GH sends already-correct list of row dicts.
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload

    # If GH sends ["<json string>"] (double-encoded list).
    if (
        isinstance(payload, list)
        and len(payload) == 1
        and isinstance(payload[0], str)
        and payload[0].strip()
    ):
        decoded = json.loads(payload[0])
        if isinstance(decoded, list) and all(isinstance(item, dict) for item in decoded):
            return decoded

    # If GH sends raw JSON string.
    if isinstance(payload, str) and payload.strip():
        decoded = json.loads(payload)
        if isinstance(decoded, list) and all(isinstance(item, dict) for item in decoded):
            return decoded

    # If GH sends object wrapper like {"data":[...]}.
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        rows = payload["data"]
        if all(isinstance(item, dict) for item in rows):
            return rows

    raise ValueError(
        "Expected list of objects with name/parent/value. "
        "Also supported: stringified list, ['stringified list'], or {'data':[...]}."
    )


class TreemapRequestHandler(SimpleHTTPRequestHandler):
    """Serve project files and receive GH updates via POST /update."""

    def __init__(self, *args, **kwargs):
        super(TreemapRequestHandler, self).__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def do_POST(self):
        if self.path != "/update":
            self.send_error(404, "Only /update is supported for POST.")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body.decode("utf-8"))
            rows = normalize_payload(payload)
            write_json_atomic(DATA_PATH, rows)
        except Exception as exc:
            message = {"ok": False, "error": str(exc)}
            raw = json.dumps(message).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        message = {"ok": True}
        raw = json.dumps(message).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def end_headers(self):
        # Disable caching so WebView always sees latest data.json values.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super(TreemapRequestHandler, self).end_headers()


def main():
    ensure_data_file()
    server = ThreadingHTTPServer((HOST, PORT), TreemapRequestHandler)
    print("Serving datacharts at http://{0}:{1}".format(HOST, PORT))
    print("Treemap page: http://{0}:{1}/bin/animated_treemap.html".format(HOST, PORT))
    print("Update endpoint: POST http://{0}:{1}/update".format(HOST, PORT))
    server.serve_forever()


if __name__ == "__main__":
    main()
