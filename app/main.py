# -*- coding: utf-8 -*-
"""Qpdf 入口：起本地 HTTP 服务 + 便携 Chromium 应用窗口（规格 §2/§4 外壳）。

外壳选型（2026-10-11 重新规划）：原方案依赖系统预装 Edge，无法满足
"换一台没装 / 被精简 Edge 的电脑也能用"的便携需求。改为**随包自带
便携 Chromium**（engine/chromium/chrome.exe，BSD 开源、可再分发）：
离线可用、免安装、免管理员、不依赖系统浏览器。启动参数与 Edge 一致
（chrome.exe --app=URL）。窗口关闭即进程退出 → 服务收尾。

回退链：包内 Chromium → 系统 Edge → 系统 Chrome/Chromium，确保开发机
与任意目标机都能起窗口。
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
ENGINE_DIR = os.path.join(ROOT, "engine")
PROFILE_DIR = os.path.join(ROOT, "data", "profile")  # 专属 profile, 独立于日常浏览器

# 1) 包内自带的便携 Chromium（优先，保证换电脑无系统浏览器也能用）
BUNDLED_CHROMIUM = [
    os.path.join(ENGINE_DIR, "chromium", "chrome.exe"),
    os.path.join(ENGINE_DIR, "chromium", "chrome-win32", "chrome.exe"),
    os.path.join(ENGINE_DIR, "chromium", "chrome-win", "chrome.exe"),
    os.path.join(ENGINE_DIR, "chromium", "chromium.exe"),
]
# 2) 系统浏览器（开发机兜底）
SYSTEM_CANDIDATES = [
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
]


def find_browser():
    """优先包内 Chromium，回退系统 Edge/Chrome；返回 (路径, 来源) 或 (None, None)。"""
    for p in BUNDLED_CHROMIUM:
        if os.path.isfile(p):
            return p, "bundled-chromium"
    for p in SYSTEM_CANDIDATES:
        if p and os.path.isfile(p):
            return p, "system"
    return None, None


def main():
    browser, src = find_browser()
    if not browser:
        print("未找到可用浏览器内核。请确认：")
        print("  1) engine/chromium/chrome.exe 已随包自带（推荐，详见 docs/开发规格.md §6.2），或")
        print("  2) 系统已安装 Edge / Chrome。")
        return 1

    server = PdfToolServer()
    server.add_file("/", os.path.join(FE_DIR, "index.html"), "text/html; charset=utf-8")
    server.add_tree("/frontend", FE_DIR)
    server.add_tree("/pdfjs", PDFJS_DIR)
    server.start()

    os.makedirs(PROFILE_DIR, exist_ok=True)
    url = server.base_url + "/"
    # --app 模式 + 离线加固：禁止后台网络/更新/回传，确保 100% 离线
    cmd = [
        browser,
        f"--app={url}",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        "--disable-component-update",
        "--disable-background-networking",
        "--no-pings",
        "--disable-domain-reliability",
        "--metrics-recording-only",
        "--window-size=1280,800",
    ]
    tag = "包内 Chromium" if src == "bundled-chromium" else "系统浏览器"
    print(f"已用[{tag}]启动应用窗口：{browser}")
    try:
        proc = subprocess.Popen(cmd)
    except OSError as e:
        print(f"启动浏览器失败: {e}")
        server.stop()
        return 1

    # 窗口关闭 → 专属 profile 的全部进程退出 → wait 返回 → 收尾
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
