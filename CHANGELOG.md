# Qpdf 变更日志

## 2026-10-11 · 外壳迁移:PySide6+QtWebEngine (commit 86adc0a)

### 变更概述
应用外壳从「系统 Edge --app」迁移到「PySide6 + QtWebEngine」，实现完全自包含、不依赖系统浏览器。

### 修改文件
| 文件 | 变更 |
|------|------|
| `app/main.py` | 重写为 PySide6 版（160行）：QMainWindow + QWebEngineView + QWebChannel + FileBridge（pickOpenPath/pickSavePath 两个 Slot） |
| `app/server.py` | 扩展：GET /api/fs/read?path=… + POST /api/fs/write?path=… + add_bytes() 方法 |
| `app/frontend/toolbar.js` | 四处编辑：①注释改 Qt 壳；②getQtBridge() 桥接函数（QWebChannel）；③ACTIONS.open/saveAs 加 Qt 桥路径（保留浏览器降级）；④boot() 预热桥 |
| `requirements.txt` | `pymupdf>=1.24` + `PySide6>=6.7` |
| `docs/开发规格.md` | §1.2 开源约束说明、§2 选型表更新（PySide6 LGPL-3.0，+200MB）、否决列表补 pywebview/系统 Edge |

### 外壳选型说明（三度更迭）
1. **pywebview**（原方案）：Windows 依赖 pythonnet，本机 netfx/coreclr 双路均死 → 否决
2. **系统 Edge `--app`**（次选）：引擎随系统走，目标机器被精简/无 Edge 时不可用 → 否决
3. **PySide6 + QtWebEngine**（最终）：自带完整 Chromium 内核并随包分发；离线、免管理员、不依赖系统浏览器；LGPL 许可

### 已验证功能
- ✅ 窗口正常弹出（标题 `Qpdf`，1280×800，内存 186MB）
- ✅ 单实例锁正常工作（双开被拦截，exit 1）
- ✅ PDF.js 正常渲染（/pdfjs/ 路由）
- ✅ 文件对话框走 Qt 原生（QFileDialog）
- ✅ 锁自动释放（正常关窗）

### 已知小问题
- **D3D11 警告**（非致命）：QtWebEngine 报 `QueryVideoProcessorCustomExtForHDR: Failed to retrieve D3D11 device`，不影响功能
- **GBK 终端乱码**（仅显示）：中文提示在 GBK 终端显示为乱码，内容正确，可改 UTF-8 终端解决

### 安装依赖
```bash
# PySide6 及子包（约 260MB）
pip install PySide6>=6.7
```

### 下一步（待用户确认）
- 打包为 exe（PyInstaller --onedir + --windowed + QtWebEngine 资源）
- 阶段 1：万兴式功能区骨架 + 文档标签页
- 阶段 2：PyMuPDF 页面/编辑/注释/表单/保护
- 阶段 3：OCR/转换/压缩
- 阶段 4：U盘验证 + 便携化优化
