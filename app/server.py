# -*- coding: utf-8 -*-
"""本地静态 HTTP 服务。

PDF.js 需要通过 http(s) 协议加载 worker 与 wasm，file:// 会被 CORS 拦截，
所以这里起一个仅监听 127.0.0.1 的轻量服务来提供 PDF.js 静态资源和 PDF 文件内容。
"""
import json
import mimetypes
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

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

        # 动态功能块清单 (规格 §7.1): GET /api/blocks
        if route == "/api/blocks":
            from app.ops import get_blocks  # 延迟导入, 避免循环依赖
            body = json.dumps(get_blocks(), ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return

        # 读文件（打开）: GET /api/fs/read?path=<绝对路径> — 由前端原生对话框选出
        if route == "/api/fs/read":
            path = (parse_qs(parsed.query).get("path") or [""])[0]
            if not path or not os.path.isfile(path):
                self._send(400, b'{"error": "path invalid"}', "application/json; charset=utf-8")
                return
            try:
                with open(path, "rb") as f:
                    body = f.read()
            except OSError as e:
                err = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
                self._send(400, err, "application/json; charset=utf-8")
                return
            ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
            self._send(200, body, ctype)
            return

        root = self.server.routes.get(route)
        if root is None:
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return

        # root 形态: 路径 | (路径, 类型覆盖) | ("__bytes__", 数据, 类型)
        if isinstance(root, tuple) and root[0] == "__bytes__":
            self._send(200, root[1], root[2])
            return
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

    def do_POST(self):  # noqa: N802
        """功能块执行路由：POST /api/ops/<id>

        body = 原始 PDF 字节，query = 小参数（params），
        返回新文档字节；块内异常统一回 400 JSON（规格 §7.1 契约）。
        """
        parsed = urlparse(self.path)
        route = unquote(parsed.path)

        # 写文件（另存为）: POST /api/fs/write?path=<绝对路径>, body=原始字节
        if route == "/api/fs/write":
            path = (parse_qs(parsed.query).get("path") or [""])[0]
            if not path:
                self._send(400, b'{"error": "path invalid"}', "application/json; charset=utf-8")
                return
            length = int(self.headers.get("Content-Length") or 0)
            data = self.rfile.read(length) if length else b""
            try:
                with open(path, "wb") as f:
                    f.write(data)
            except OSError as e:
                err = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
                self._send(400, err, "application/json; charset=utf-8")
                return
            self._send(200, b'{"ok": true}', "application/json; charset=utf-8")
            return

        if not route.startswith("/api/ops/"):
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        op_id = route[len("/api/ops/"):]
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        length = int(self.headers.get("Content-Length") or 0)
        doc = self.rfile.read(length) if length else b""
        try:
            from app.ops import run_op  # 延迟导入, 避免循环依赖
            out = run_op(op_id, doc, params)
        except Exception as e:
            err = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
            self._send(400, err, "application/json; charset=utf-8")
            return
        self._send(200, out, "application/pdf")


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

    def add_bytes(self, route: str, data: bytes, ctype: str):
        """注册一段内存内容（如 Qt 资源里的 qwebchannel.js）。"""
        self._httpd.routes[route] = ("__bytes__", data, ctype)

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
