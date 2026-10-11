# -*- coding: utf-8 -*-
"""Qpdf 入口：PySide6(QtWebEngine) 内嵌壳 + 本地 HTTP 服务（规格 §2/§4 外壳）。

外壳选型说明（三度更迭，详见规格 §8 风险表）：
1) pywebview：Windows 依赖 pythonnet，本机 netfx/coreclr 双路均不可用 → 否决；
2) 系统 Edge 应用窗口：引擎随系统走，目标机器被精简/无 Edge 时不可用，
   不满足"换电脑继续使用"的便携要求 → 否决；
3) 最终方案 PySide6 + QtWebEngine：自带完整 Chromium 内核并随包分发，
   离线、免管理员、不依赖系统浏览器；LGPL 许可，出处见规格 §2。
文件对话框走 QWebChannel 桥（Python 侧原生 QFileDialog），
PDF 字节仍走本地 HTTP（server.py），与功能块共用同一服务。
"""
import ctypes
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from PySide6.QtCore import QObject, QUrl, Slot
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow
except ImportError as e:  # 缺依赖时给出明确指引
    print("缺少 PySide6（内嵌浏览器壳），请先安装依赖: pip install -r requirements.txt")
    print(f"导入错误: {e}")
    sys.exit(1)

from app.server import PdfToolServer  # noqa: E402

FE_DIR = os.path.join(ROOT, "app", "frontend")
PDFJS_DIR = os.path.join(ROOT, "resources", "pdfjs")
LOCK_PATH = os.path.join(ROOT, "data", "qpdf.lock")  # 单实例锁 (记录宿主 PID)


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
    """已有存活实例 → 返回 False（避免双开互相干扰）。"""
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
    """只释放自己写入的锁；删除失败重试几次（杀软/索引可能瞬时占用），
    仍失败也不阻塞退出——下次启动 _pid_alive 探测到死进程会覆盖陈旧锁。"""
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
            import time
            time.sleep(0.2 * (i + 1))
    print(f"警告: 无法删除锁文件 {LOCK_PATH}（不影响下次启动，会自动覆盖）。")


class FileBridge(QObject):
    """前端 → Python 的文件对话框桥（QWebChannel 注册名 "bridge"）。"""

    @Slot(result=str)
    def pickOpenPath(self):
        path, _ = QFileDialog.getOpenFileName(
            None, "打开 PDF", "", "PDF 文档 (*.pdf);;所有文件 (*.*)"
        )
        return path or ""

    @Slot(str, result=str)
    def pickSavePath(self, suggested):
        path, _ = QFileDialog.getSaveFileName(
            None, "另存为", suggested or "document.pdf",
            "PDF 文档 (*.pdf);;所有文件 (*.*)",
        )
        return path or ""


def _qwebchannel_js():
    """从 Qt 资源读出官方 qwebchannel.js（前端桥必需，随 PySide6 分发）。"""
    from PySide6.QtCore import QFile, QIODevice
    f = QFile(":/qtwebchannel/qwebchannel.js")
    if not f.open(QIODevice.OpenModeFlag.ReadOnly):
        return None
    data = bytes(f.readAll())
    f.close()
    return data or None


def main():
    if not acquire_instance_lock():
        print("Qpdf 已在运行。请切换到已打开的窗口；若窗口不见了，删除 data\\qpdf.lock 后重试。")
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("Qpdf")

    server = PdfToolServer()
    server.add_file("/", os.path.join(FE_DIR, "index.html"), "text/html; charset=utf-8")
    server.add_tree("/frontend", FE_DIR)
    server.add_tree("/pdfjs", PDFJS_DIR)
    qcjs = _qwebchannel_js()
    if qcjs:
        server.add_bytes("/frontend/qwebchannel.js", qcjs, "text/javascript; charset=utf-8")
    server.start()

    win = QMainWindow()
    win.setWindowTitle("Qpdf")
    win.resize(1280, 800)
    win.setMinimumSize(900, 600)

    view = QWebEngineView(win)
    win.setCentralWidget(view)

    channel = QWebChannel(view.page())
    bridge = FileBridge()
    channel.registerObject("bridge", bridge)
    view.page().setWebChannel(channel)

    view.load(QUrl(server.base_url + "/"))
    win.show()

    try:
        app.exec()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        release_instance_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
