"""
Local Web Server and Compiler API for the Pseudocode to C Compiler.
Built entirely with Python standard library (no external pip dependencies needed).
Serves the modern online IDE and provides REST endpoints for compilation.
"""

import sys
import os
import json
import shutil
import subprocess
import tempfile
import webbrowser

# Ensure Windows terminal supports UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from lexer import Lexer
from parser import Parser
from code_generator import CodeGenerator
from errors import CompilerError
from examples import EXAMPLES


PORT = 5000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


class CompilerRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # REST API: GET /api/examples
        if path == "/api/examples":
            self.send_json_response(200, {"examples": EXAMPLES})
            return

        # Serve static web files
        if path == "/" or path == "":
            file_path = os.path.join(WEB_DIR, "index.html")
        else:
            clean_path = path.lstrip("/")
            file_path = os.path.join(WEB_DIR, clean_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.serve_file(file_path)
        else:
            self.send_error(404, f"File not found: {path}")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            self.send_json_response(400, {"success": False, "message": "Invalid JSON payload."})
            return

        # REST API: POST /api/compile
        if path == "/api/compile":
            code = payload.get("code", "")
            self.handle_compile(code)
            return

        # REST API: POST /api/run_c
        if path == "/api/run_c":
            c_code = payload.get("code", "")
            self.handle_run_c(c_code)
            return

        self.send_error(404, "Endpoint not found.")

    def handle_compile(self, code):
        try:
            lexer = Lexer()
            tokens = lexer.tokenize(code)

            parser = Parser(tokens)
            tree = parser.parse()

            gen = CodeGenerator()
            result = gen.generate_with_metadata(tree)

            # Format symbol table for UI
            symbols_meta = {}
            for name, sym in tree.get("symbols", {}).items():
                symbols_meta[name] = sym.to_dict()

            response_data = {
                "success": True,
                "c_code": result["c_code"],
                "explanation": result["explanation"],
                "headers": result["headers"],
                "warnings": result["warnings"],
                "symbols": symbols_meta
            }
            self.send_json_response(200, response_data)

        except CompilerError as err:
            self.send_json_response(400, {
                "success": False,
                "error": err.to_dict()
            })
        except Exception as err:
            self.send_json_response(500, {
                "success": False,
                "error": {
                    "type": "Internal Error",
                    "message": str(err),
                    "suggestion": "Please check pseudocode syntax or review compiler logs."
                }
            })

    def handle_run_c(self, c_code):
        """Check for GCC and compile safely without simulating."""
        gcc_path = shutil.which("gcc") or shutil.which("clang")
        if not gcc_path:
            self.send_json_response(200, {
                "gcc_available": False,
                "message": "Neither GCC nor Clang was found in your system PATH."
            })
            return

        # Temporary compilation
        temp_dir = tempfile.mkdtemp(prefix="compiler_run_")
        c_file = os.path.join(temp_dir, "test.c")
        exe_file = os.path.join(temp_dir, "test.exe" if os.name == "nt" else "test")

        try:
            with open(c_file, "w", encoding="utf-8") as f:
                f.write(c_code)

            # Compile
            comp_res = subprocess.run(
                [gcc_path, "-Wall", c_file, "-o", exe_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            if comp_res.returncode != 0:
                self.send_json_response(200, {
                    "gcc_available": True,
                    "compiled": False,
                    "output": comp_res.stderr or "GCC Compilation Failed."
                })
                return

            # Check if interactive inputs are needed
            # Run with short timeout
            run_res = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                timeout=3
            )

            self.send_json_response(200, {
                "gcc_available": True,
                "compiled": True,
                "output": run_res.stdout or "(Program executed with return code 0)"
            })

        except subprocess.TimeoutExpired:
            self.send_json_response(200, {
                "gcc_available": True,
                "compiled": True,
                "output": "[Program ran or waited for interactive input (scanf) and timed out after 3 seconds.]"
            })
        except Exception as err:
            self.send_json_response(200, {
                "gcc_available": True,
                "compiled": False,
                "output": f"Execution error: {str(err)}"
            })
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

    def serve_file(self, file_path):
        content_type = "text/plain"
        if file_path.endswith(".html"):
            content_type = "text/html; charset=utf-8"
        elif file_path.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif file_path.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"
        elif file_path.endswith(".json"):
            content_type = "application/json; charset=utf-8"
        elif file_path.endswith(".png"):
            content_type = "image/png"
        elif file_path.endswith(".ico"):
            content_type = "image/x-icon"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")

    def send_json_response(self, status_code, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Clean terminal output
        sys.stderr.write(f"[Server] {self.address_string()} - {format % args}\n")


def start_server(port=PORT, host="127.0.0.1", open_browser=True):
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, CompilerRequestHandler)
    url = f"http://{host}:{port}"
    print("=" * 60)
    print(f"🚀 Pseudocode to C Compiler - Modern IDE Server Running")
    print(f"📍 Local URL: {url}")
    print(f"📁 Web Root:  {WEB_DIR}")
    print("=" * 60)

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    should_open = "--no-open" not in sys.argv
    port_arg = PORT
    for idx, arg in enumerate(sys.argv):
        if arg == "--port" and idx + 1 < len(sys.argv):
            port_arg = int(sys.argv[idx + 1])
    start_server(port=port_arg, open_browser=should_open)
