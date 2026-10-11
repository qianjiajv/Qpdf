# -*- coding: utf-8 -*-
"""Qpdf 入口：起本地 HTTP 服务 + pywebview 窗口（规格 §6.1 阶段0）。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.api import Api            # noqa: E402
from app.server import PdfToolServer  # noqa: E402

FE_DIR = os.path.join(ROOT, "app", "frontend")
PDFJS_DIR = os.path.join(ROOT, "resources", "pdfjs")


def main():
    server = PdfToolServer()
    server.add_file("/", os.path.join(FE_DIR, "index.html"), "text/html; charset=utf-8")
    server.add_tree("/frontend", FE_DIR)
    server.add_tree("/pdfjs", PDFJS_DIR)
    server.start()

    api = Api(server)
    import webview
    webview.create_window(
        "Qpdf",
        server.base_url + "/",
        js_api=api,
        width=1280,
        height=800,
        min_size=(900, 600),
    )
    try:
        webview.start()
    finally:
        server.stop()


if __name__ == "__main__":
    main()
