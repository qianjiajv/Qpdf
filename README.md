# Qpdf — Portable Offline PDF Toolkit

> 便携离线 PDF 工具箱

**Status: 🚧 In early development** · Windows 10/11 · 100% offline · No installation · No admin rights

> **Note:** This project is unrelated to [qpdf](https://github.com/qpdf/qpdf), the Artifex command-line PDF tool. The namesake is purely coincidental.

## Why Qpdf?

Free PDF suites often force a **tool-per-operation** workflow: every function opens its own window and asks you to pick the file again. Qpdf takes a different shape — a **ribbon-style single-document workspace**:

- Open a PDF **once**; it stays in the viewer.
- Switch ribbon tabs (View / Convert / Edit / Annotate / Pages / Forms / Protect) without closing the document.
- Every operation acts on the **currently open file** and reloads the result back into the same window.

All of this runs from a **single portable folder** — copy it to a USB drive, plug into any Windows machine, double-click. No installer, no registry, no admin prompt, no network traffic.

## Features

- 📑 **Single-document ribbon workspace** — tools switch, the document stays
- 🚫🌐 **Fully offline** — PDF.js, fonts, CMaps and OCR models are bundled locally
- 📦 **Portable** — one folder on disk or USB stick; settings stored beside the executable
- 🔓 **Open-source engines** — no proprietary PDF SDKs (see [Engines](#open-source-engines))
- 🀄 **OCR for Chinese & English** — RapidOCR (Apache-2.0), bundled models
- 🔐 **AES-256 encryption, permissions, redaction, digital signatures**
- 🗂 **Page organizing** — merge, split, extract, rotate, crop, resize, Bates numbering
- 🔄 **Conversions** — PDF → Word / images / TXT / HTML; images → PDF
- 📝 **Annotations** — highlight, underline, strikethrough, notes, freehand, stamps

## Architecture

```
┌───────────────────────────────────────────────┐
│ pywebview window (system WebView2)            │
│   Ribbon tabs + PDF.js canvas (persistent)    │
└──────────────────┬────────────────────────────┘
                   │  http://127.0.0.1:<random port>
┌──────────────────▼────────────────────────────┐
│ Local HTTP server (Python stdlib, threaded)   │
│   static: /, /static/*, /pdfjs/*              │
│   API: open-dialog · document bytes · ops     │
└──────────────────┬────────────────────────────┘
                   │  in-process / subprocess
        PyMuPDF · RapidOCR · pdf2docx · qpdf · Ghostscript
```

A local loopback HTTP server serves the frontend and PDF byte streams (PDF.js requires `http(s)`, `file://` hits worker/CORS limits). Real file paths come from the native open dialog — browsers only hand out fake paths.

## Getting started (development)

Prerequisites: Windows 10/11, Python 3.12+.

```powershell
git clone https://github.com/qianjiajv/Qpdf.git
cd Qpdf
python -m venv .venv
.venv\Scripts\activate
pip install pymupdf pywebview
```

Download the [PDF.js release](https://github.com/mozilla/pdf.js/releases) (ES-module build) and extract it to `resources/pdfjs/`, then:

```powershell
python app\main.py      # or double-click run_dev.bat
```

> `app/main.py` and the frontend land in **Stage 0** — see the roadmap.

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| 0 | Reader shell: window + PDF.js viewer, open/zoom/page navigation | 🚧 in progress |
| 1 | Ribbon skeleton, document state, undo stack, drag & drop, recent files | ⏳ |
| 2 | Engine integration: pages, editing, annotations, forms, protection | ⏳ |
| 3 | OCR, conversions, compression, batch queue | ⏳ |
| 4 | PyInstaller portable packaging, USB-drive validation | ⏳ |
| 5 | Optional extras: LibreOffice interop, dark mode | ⏳ |

## Known limitations

- **In-place text reflow** (editing paragraphs inside an existing PDF) is out of scope for open-source engines; edits are applied as positioned replacements, not live re-layout.
- **PDF → Excel / PPT** output is basic; PDF → Word (via `pdf2docx`) works best on text-based PDFs.
- **Scanned PDFs** need OCR before any text-level operation; the OCR model is bundled once and works offline thereafter.
- PyMuPDF is **AGPL-3.0** — fine for personal/internal use; commercial closed-source distribution would require a license change or a `pypdfium2` fallback.

## Open-source engines

| Component | Role | License |
|---|---|---|
| [PDF.js](https://github.com/mozilla/pdf.js) | Rendering / viewer | Apache-2.0 |
| [pywebview](https://github.com/r0x0r/pywebview) | Desktop window shell | MIT |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | Core PDF engine | AGPL-3.0 |
| [RapidOCR](https://github.com/RapidAI/RapidOCR) | OCR (zh/en) | Apache-2.0 |
| [pdf2docx](https://github.com/dothinking/pdf2docx) | PDF → Word | MIT |
| [qpdf](https://github.com/qpdf/qpdf) | Compression / encryption | Apache-2.0 |
| [Ghostscript](https://github.com/ArtifexSoftware/ghostpdl-download) | Transformations | AGPL-3.0 |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | Packaging | GPL w/ exception |

## License

License to be announced. Bundled engines keep their own licenses (see table above).

---

# Qpdf — 便携离线 PDF 工具箱

**状态：🚧 早期开发中** · Windows 10/11 · 完全离线 · 免安装 · 免管理员权限

> **注**：本项目与 Artifex 的命令行工具 [qpdf](https://github.com/qpdf/qpdf) 无关，重名纯属巧合。

## 为什么做 Qpdf？

免费 PDF 工具大多采用"一个功能一个窗口"的模式：每换一个功能都要重新打开工具、重新选择文件。Qpdf 换了一种形态——**功能区（Ribbon）式单文档工作区**：

- PDF **只打开一次**，常驻阅读窗口；
- 顶部切换功能区标签（视图 / 转换 / 编辑 / 注释 / 页面 / 表单 / 保护），文档不关闭；
- 所有操作都作用于**当前打开的文件**，结果原地刷新回同一窗口。

整套软件跑在**一个便携文件夹**里——拷到 U 盘，插到任意 Windows 电脑上双击即用。不用安装、不写注册表、不要管理员权限、不发一个网络请求。

## 功能特性

- 📑 **单文档功能区工作区**——工具随切随用，文档始终在场
- 🚫🌐 **完全离线**——PDF.js、字体、CMap、OCR 模型全部本地打包
- 📦 **便携**——一个文件夹走天下（磁盘/U 盘均可），设置存在程序旁边
- 🔓 **全开源引擎**——不依赖任何商业 PDF SDK（见[引擎清单](#开源引擎)）
- 🀄 **中英文 OCR**——RapidOCR（Apache-2.0），模型随包分发
- 🔐 **AES-256 加密、权限控制、密文黑涂、数字签名**
- 🗂 **页面组织**——合并、拆分、提取、旋转、裁剪、改页大小、贝茨码
- 🔄 **格式转换**——PDF → Word/图片/TXT/HTML；图片 → PDF
- 📝 **批注**——高亮、下划线、删除线、便签、手绘、图章

## 系统架构

```
┌───────────────────────────────────────────────┐
│ pywebview 窗口（系统 WebView2 内核）           │
│   功能区标签 + PDF.js 渲染画布（常驻）          │
└──────────────────┬────────────────────────────┘
                   │  http://127.0.0.1:<随机端口>
┌──────────────────▼────────────────────────────┐
│ 本地 HTTP 服务（Python 标准库，多线程）         │
│   静态: /, /static/*, /pdfjs/*                │
│   API : 打开对话框 · 文档字节流 · 操作接口      │
└──────────────────┬────────────────────────────┘
                   │  进程内 / 子进程
        PyMuPDF · RapidOCR · pdf2docx · qpdf · Ghostscript
```

前端与 PDF 字节流走本地回环 HTTP（PDF.js 依赖 `http(s)` 协议，`file://` 会被 worker/CORS 限制拦截）；文件真实路径必须取自系统原生打开对话框（浏览器内文件选择只会给出假路径）。

## 快速开始（开发）

前置条件：Windows 10/11、Python 3.12+。

```powershell
git clone https://github.com/qianjiajv/Qpdf.git
cd Qpdf
python -m venv .venv
.venv\Scripts\activate
pip install pymupdf pywebview
```

下载 [PDF.js 发行版](https://github.com/mozilla/pdf.js/releases)（ES module 构建），解压到 `resources/pdfjs/`，然后：

```powershell
python app\main.py      # 或双击 run_dev.bat
```

> `app/main.py` 与前端将在**阶段 0** 落地——见路线图。

## 路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 | 阅读壳：窗口 + PDF.js 阅读器，打开/缩放/翻页 | 🚧 进行中 |
| 1 | 功能区骨架、文档状态、撤销栈、拖拽打开、最近文件 | ⏳ |
| 2 | 引擎接入：页面、编辑、批注、表单、保护 | ⏳ |
| 3 | OCR、格式转换、压缩、批量队列 | ⏳ |
| 4 | PyInstaller 便携打包、U 盘实测 | ⏳ |
| 5 | 可选增强：LibreOffice 互转、深色模式 | ⏳ |

## 已知局限

- **PDF 内文字的所见即所得重排**：开源引擎做不到商业级的段落重排，编辑以"定位替换"方式实现；
- **PDF → Excel/PPT**：基础可用，复杂表格还原度一般；文本型 PDF 转 Word（`pdf2docx`）效果最好；
- **扫描件**：需先 OCR 才能进行文字级操作；OCR 模型随包一次性分发，之后永久离线；
- PyMuPDF 为 **AGPL-3.0**：个人/内部使用无义务；闭源商用分发需购买授权或切换 `pypdfium2` 兜底。

## 开源引擎

| 组件 | 作用 | 许可证 |
|---|---|---|
| [PDF.js](https://github.com/mozilla/pdf.js) | 渲染 / 阅读器 | Apache-2.0 |
| [pywebview](https://github.com/r0x0r/pywebview) | 桌面窗口外壳 | MIT |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | PDF 核心引擎 | AGPL-3.0 |
| [RapidOCR](https://github.com/RapidAI/RapidOCR) | OCR（中英文） | Apache-2.0 |
| [pdf2docx](https://github.com/dothinking/pdf2docx) | PDF 转 Word | MIT |
| [qpdf](https://github.com/qpdf/qpdf) | 压缩 / 加密 | Apache-2.0 |
| [Ghostscript](https://github.com/ArtifexSoftware/ghostpdl-download) | 格式变换 | AGPL-3.0 |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | 打包 | GPL+例外 |

## 许可证

项目许可证待定。随包分发的引擎各自保留其开源许可证（见上表）。
