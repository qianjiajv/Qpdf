# -*- coding: utf-8 -*-
"""本地静态 HTTP 服务。

PDF.js 需要通过 http(s) 协议加载 worker 与 wasm，file:// 会被 CORS 拦截，
所以这里起一个仅监听 127.0.0.1 的轻量服务来提供 PDF.js 静态资源和 PDF 文件内容。
"""
import mimetypes
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

# 让 .mjs 被识别为 JS 模块
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("application/wasm", ".wasm")


class StaticHandler(BaseHTTPRequestHandler):
    """根据注册的路由表返回文件内容。路由表由 PdfToolServer 维护。"""

    server_version = "PdfToolBox/0.1"

    def log_message(self, fmt, *args):  # 静默日志
        pass

    def _send(self, code, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # 本地服务，禁用缓存以便开发期即时更新
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        route = unquote(parsed.path)
        root = self.server.routes.get(route)
        if root is None:
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return

        # root 为元组 (文件路径, 内容类型覆盖)
        if isinstance(root, tuple):
            fpath, ctype_override = root
        else:
            fpath, ctype_override = root, None

        if not os.path.isfile(fpath):
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return

        try:
            with open(fpath, "rb") as f:
                body = f.read()
        except OSError:
            self._send(500, b"read error", "text/plain; charset=utf-8")
            return

        ctype = ctype_override or mimetypes.guess_type(fpath)[0] or "application/octet-stream"
        self._send(200, body, ctype)


class PdfToolServer:
    """管理一个本地 HTTP 服务，注册路由后返回可访问的 URL。"""

    def __init__(self, host="127.0.0.1", port=0):
        self._httpd = ThreadingHTTPServer((host, port), StaticHandler)
        self._httpd.routes = {}
        self.host, self.port = self._httpd.server_address[:2]
        self._thread = None

    @property
    def base_url(self):
        return f"http://{self.host}:{self.port}"

    def add_file(self, route: str, fpath: str, ctype: str = None):
        self._httpd.routes[route] = (fpath, ctype) if ctype else fpath

    def add_tree(self, route_prefix: str, dir_path: str):
        """把一个目录挂载到某个前缀下（递归注册）。"""
        route_prefix = route_prefix.rstrip("/")
        for root, _dirs, files in os.walk(dir_path):
            for name in files:
                fpath = os.path.join(root, name)
                rel = os.path.relpath(fpath, dir_path).replace(os.sep, "/")
                self.add_file(f"{route_prefix}/{rel}", fpath)

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(
                target=self._httpd.serve_forever, daemon=True, name="pdf-tool-http"
            )
            self._thread.start()

    def stop(self):
        try:
            self._httpd.shutdown()
            self._httpd.server_close()
        except Exception:
            pass
