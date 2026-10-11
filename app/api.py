# -*- coding: utf-8 -*-
"""pywebview JS 桥接 API（规格 §3/§6.1）。

文件对话框必须走 pywebview：浏览器内 input[type=file] 拿不到真实路径。
文件字节不走这里的 JSON 桥（大字节序列化慢），走本地 HTTP（server.py）。
"""
import base64
import os

import webview

from app.ops import get_blocks


class Api:
    def __init__(self, server):
        self._server = server
        self._current_path = None

    # ---------- 文件 ----------
    def pick_pdf(self):
        """打开文件对话框，注册为 HTTP 路由后返回 {url,path,name}。"""
        w = webview.active_window()
        if w is None:
            return None
        sel = w.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("PDF 文档 (*.pdf)",),
            allow_multiple=False,
        )
        if not sel:
            return None
        return self.open_path(sel[0])

    def open_path(self, path: str):
        if not os.path.isfile(path):
            return None
        self._current_path = path
        self._server.add_file("/pdf/current", path)
        return {
            "url": self._server.base_url + "/pdf/current",
            "path": path,
            "name": os.path.basename(path),
        }

    def save_as(self, data_b64: str, default_name: str = "output.pdf"):
        """另存为：另存对话框 + base64 写文件。"""
        w = webview.active_window()
        if w is None:
            return None
        path = w.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_name or "output.pdf",
        )
        if not path:
            return None
        try:
            with open(path, "wb") as f:
                f.write(base64.b64decode(data_b64))
        except (OSError, ValueError) as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "path": path, "name": os.path.basename(path)}

    # ---------- 功能块 ----------
    def get_blocks(self):
        return get_blocks()
