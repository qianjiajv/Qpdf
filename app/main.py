# -*- coding: utf-8 -*-
"""Qpdf 入口：起本地 HTTP 服务 + 系统 Edge 应用窗口（规格 §2/§4 外壳）。

外壳选型说明（m00547 架构定论）：pywebview 在 Windows 依赖 pythonnet，
本机 netfx/coreclr 双路均死（详见规格 §9），故改用系统 Edge 的应用窗口
模式 msedge --app=URL：离线可用、免管理员、零 pythonnet、便于 PyInstaller
打包成 exe。窗口关闭即进程退出 → 服务收尾。
"""
import ctypes
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
LOCK_PATH = os.path.join(ROOT, "data", "qpdf.lock")  # 单实例锁 (记录宿主 PID)

EDGE_CANDIDATES = [
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
]


def _pid_alive(pid):
    """Windows 下探测进程存活（不能用 os.kill——它在 Windows 上会真杀进程）。"""
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return False
    try:
        code = ctypes.c_ulong(0)
        if not k32.GetExitCodeProcess(h, ctypes.byref(code)):
            return False
        return code.value == STILL_ACTIVE
    finally:
        k32.CloseHandle(h)


def acquire_instance_lock():
    """已有存活实例 → 返回 False（避免双开抢 profile 导致空白窗口）。"""
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    if os.path.exists(LOCK_PATH):
        try:
            with open(LOCK_PATH, "r") as f:
                old = int(f.read().strip() or "0")
        except (ValueError, OSError):
            old = 0
        if old and old != os.getpid() and _pid_alive(old):
            return False
    with open(LOCK_PATH, "w") as f:
        f.write(str(os.getpid()))
    return True


def release_instance_lock():
    """只释放自己写入的锁（防止误删后启实例的锁）。

    删除失败时重试几次（Windows 杀软/索引服务可能瞬时占用文件）；
    仍失败也不阻塞退出——下次启动时 _pid_alive 探测到死进程会覆盖陈旧锁。
    """
    try:
        with open(LOCK_PATH, "r") as f:
            if f.read().strip() != str(os.getpid()):
                return  # 不是自己的锁，不碰
    except OSError:
        return
    for i in range(5):
        try:
            os.remove(LOCK_PATH)
            return
        except OSError:
            time.sleep(0.2 * (i + 1))
    print(f"警告: 无法删除锁文件 {LOCK_PATH}（不影响下次启动，会自动覆盖）。")


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

    if not acquire_instance_lock():
        print("Qpdf 已在运行。请切换到已打开的窗口；若窗口不见了，重启电脑或删除 data\\qpdf.lock 后重试。")
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
    print(f"服务已启动: {url}")
    try:
        proc = subprocess.Popen(cmd)
    except OSError as e:
        print(f"启动 Edge 失败: {e}")
        server.stop()
        release_instance_lock()
        return 1

    try:
        # 启动自检: Edge 进程秒退 = profile 被占用/导航被委托给别的实例 → 明确报错
        time.sleep(2.5)
        if proc.poll() is not None:
            print("Edge 窗口未能打开（进程立即退出）。")
            print("常见原因: 同一 profile 已被另一实例占用。请关闭其他 Qpdf 窗口后重试，")
            print("或删除 data\\edge-profile 目录再启动。")
            server.stop()
            release_instance_lock()
            return 1

        # 窗口关闭 → 专属 profile 的全部 Edge 进程退出 → wait 返回 → 收尾
        while proc.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        release_instance_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
