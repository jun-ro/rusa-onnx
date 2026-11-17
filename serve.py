#!/usr/bin/env python3
"""Tiny static server for the Rusa browser demo.

WebGPU / WASM both work over plain HTTP on localhost, but the multi-threaded
WASM backend needs the page to be cross-origin isolated, so we send the COOP
and COEP headers. .onnx and .onnx_data get sane MIME types.
"""
import argparse
import os
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".onnx": "application/octet-stream",
        ".onnx_data": "application/octet-stream",
        ".wasm": "application/wasm",
        ".mjs": "text/javascript",
        ".json": "application/json",
    }

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        self.send_header("Cache-Control", "public, max-age=3600")
        super().end_headers()

    def log_message(self, fmt, *args):
        # Keep the console quiet about the 300 MB blob, log everything else.
        if "model_q4.onnx_data" in (fmt % args):
            return
        super().log_message(fmt, *args)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8000)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        httpd = ThreadingHTTPServer((args.bind, args.port), Handler)
    except OSError as err:
        raise SystemExit(f"Could not bind {args.bind}:{args.port}: {err}")

    host = socket.gethostname()
    print(f"Rusa demo  ->  http://localhost:{args.port}/")
    print(f"               http://{host}:{args.port}/")
    print("Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
