"""Stdlib-only autosave server for recipie_maker - no fastapi/uvicorn.
Serves static files and autosaves store.json on POST /api/save"""
import http.server, json, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(DIR, "store.json")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)
    def do_POST(self):
        if self.path in ("/api/save", "/api/store", "/save", "/store"):
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length)
            try:
                obj = json.loads(data.decode() or "{}")
                # atomic write
                tmp = STORE + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(obj, f, indent=2)
                os.replace(tmp, STORE)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_error(404, "Not Found")
    def do_GET(self):
        if self.path in ("/api/store", "/api/load"):
            try:
                with open(STORE, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)
            except FileNotFoundError:
                self.send_error(404)
        else:
            return super().do_GET()
    def log_message(self, fmt, *a):
        sys.stdout.write(fmt % a + "\n")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = http.server.ThreadingHTTPServer(("", port), Handler)
    print(f"Serving {DIR} at http://localhost:{port} - POST /api/save autosaves store.json")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
