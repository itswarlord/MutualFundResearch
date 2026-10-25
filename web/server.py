"""
server.py - Lightweight zero-dependency HTTP server for Indian Mutual Fund Research platform.
Serves static frontend assets from web/ and provides direct file downloads from data/.
"""

import http.server
import socketserver
import os
import urllib.parse
import mimetypes

PORT = 8000
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(WEB_DIR), "data")

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx")


class MutualFundAppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Download Master Excel (.xlsx)
        if path == "/download/excel":
            excel_path = os.path.join(DATA_DIR, "Indian_Equity_Mutual_Funds_Master.xlsx")
            if os.path.exists(excel_path):
                self.send_file(
                    excel_path,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "Indian_Equity_Mutual_Funds_Master.xlsx"
                )
            else:
                self.send_error(404, "Master Excel workbook not found.")
            return

        # 2. Download Master CSV
        if path == "/download/csv/master":
            csv_path = os.path.join(DATA_DIR, "all_equity_summary.csv")
            if os.path.exists(csv_path):
                self.send_file(csv_path, "text/csv", "all_equity_summary.csv")
            else:
                self.send_error(404, "Master CSV not found.")
            return

        # 3. Download Category CSV (e.g. /download/csv/flexi_cap)
        if path.startswith("/download/csv/"):
            slug = path.replace("/download/csv/", "").strip("/")
            csv_path = os.path.join(DATA_DIR, f"{slug}_summary.csv")
            if os.path.exists(csv_path):
                self.send_file(csv_path, "text/csv", f"{slug}_summary.csv")
            else:
                self.send_error(404, f"Category CSV '{slug}_summary.csv' not found.")
            return

        # 4. Standard Static File Serving
        return super().do_GET()

    def send_file(self, filepath: str, content_type: str, download_filename: str):
        try:
            with open(filepath, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Content-Disposition", f'attachment; filename="{download_filename}"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error streaming file: {e}")

    def end_headers(self):
        # Disable aggressive caching in local development
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def start_server(port=PORT):
    with ReusableTCPServer(("", port), MutualFundAppHandler) as httpd:
        print(f"🚀 MF Research Web Server running at: http://localhost:{port}")
        print(f"📁 Serving static files from: {WEB_DIR}")
        print(f"📊 Serving downloads from   : {DATA_DIR}")
        print("Press Ctrl+C to terminate.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    start_server()
