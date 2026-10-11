# -*- coding: utf-8 -*-
"""Qpdf 入口：起本地 HTTP 服务 + 系统 Edge 应用窗口（规格 §2/§4 外壳）。

外壳选型说明（m00547 架构定论）：pywebview 在 Windows 依赖 pythonnet，
本机 netfx/coreclr 双路均死（详见规格 §9），故改用系统 Edge 的应用窗口
模式 msedge --app=URL：离线可用、免管理员、零 pythonnet、便于 PyInstaller
打包成 exe。窗口关闭即进程退出 → 服务收尾。
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.server import PdfToolServer  # noqa: E402

FE_DIR = os.path.join(ROOT, "app", "frontend")
PDFJS_DIR = os.path.join(ROOT, "resources", "pdfjs")
PROFILE_DIR = os.path.join(ROOT, "data", "edge-profile")  # 专属 profile, 独立于日常浏览器

EDGE_CANDIDATES = [
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
]


def find_edge():
    """按常见安装位置找 msedge.exe，找不到返回 None。"""
    for p in EDGE_CANDIDATES:
        if p and os.path.isfile(p):
            return p
    return None


def main():
    edge = find_edge()
    if not edge:
        print("未找到 Microsoft Edge，无法启动应用窗口。")
        print("请安装 Edge（或保留系统默认浏览器组件）后重试。")
        return 1

    server = PdfToolServer()
    server.add_file("/", os.path.join(FE_DIR, "index.html"), "text/html; charset=utf-8")
    server.add_tree("/frontend", FE_DIR)
    server.add_tree("/pdfjs", PDFJS_DIR)
    server.start()

    os.makedirs(PROFILE_DIR, exist_ok=True)
    url = server.base_url + "/"
    cmd = [
        edge,
        f"--app={url}",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        "--window-size=1280,800",
    ]
    try:
        proc = subprocess.Popen(cmd)
    except OSError as e:
        print(f"启动 Edge 失败: {e}")
        server.stop()
        return 1

    # 窗口关闭 → 专属 profile 的全部 Edge 进程退出 → wait 返回 → 收尾
    try:
        while proc.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
