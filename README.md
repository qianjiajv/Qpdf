# Qpdf — 便携离线 PDF 工具箱｜Portable Offline PDF Toolkit

> 单文档工作区 · 完全离线 · 免安装 · 非管理员可用
> Single-document workspace · Fully offline · No install · No admin rights

**状态 Status**：🚧 早期开发中 Early development · Windows 10/11 · 100% 离线 Offline · 免安装 No install · 免管理员 No admin

> **命名说明 Name note**：本项目与同名的 `qpdf` 命令行工具无关，重名纯属巧合。
> *This project is unrelated to the `qpdf` command-line PDF tool of the same name; the namesake is coincidental.*

---

## 为什么做 Qpdf｜Why Qpdf

**中文**：多数免费 PDF 工具采用「一个功能一个窗口」的模式：每换一项功能都要重新打开工具、重新选择文件。Qpdf 换一种形态——**功能区（Ribbon）式单文档工作区**：PDF 只打开一次、常驻阅读窗口；切换顶部功能区标签（视图 / 转换 / 编辑 / 注释 / 页面 / 表单 / 保护 / 工具），文档不关闭；所有操作都作用于**当前打开的文件**，结果原地刷新回同一窗口。
整套软件跑在**一个便携文件夹**里——拷到 U 盘，插到任意 Windows 电脑上双击即用。不安装、不写注册表、不要管理员权限、不发任何网络请求。

**English**: Most free PDF tools adopt a "one feature, one window" model: switching features means reopening a tool and reselecting the file. Qpdf takes a different shape — a **ribbon-style single-document workspace**: open a PDF once and keep it in the viewer; switch ribbon tabs (View / Convert / Edit / Annotate / Pages / Forms / Protect / Tools) without closing the document; every operation acts on the **currently open file** and reloads the result into the same window.
The whole app runs from **a single portable folder** — copy it to a USB drive, plug into any Windows machine, double-click. No installer, no registry writes, no admin prompt, no network traffic.

---

## 功能特性｜Features

- 📑 **单文档功能区工作区｜Single-document ribbon workspace** —— 工具随切随用，文档始终在场
- 🚫🌐 **完全离线｜Fully offline** —— PDF.js、字体、CMap、OCR 模型全部本地打包
- 📦 **便携｜Portable** —— 一个文件夹走天下（磁盘 / U 盘均可），设置存在程序旁边
- 🔓 **全开源引擎｜Open-source engines** —— 不依赖任何专有 PDF SDK
- 🀄 **OCR（中 / 英）｜OCR (Chinese & English)** —— 免费模型随包分发，离线可用
- 🔐 **加密与保护｜Encryption & protection** —— AES-256 加密、权限控制、密文黑涂、去元数据
- 🗂 **页面组织｜Page organizing** —— 合并、拆分、提取、旋转、裁剪、改页大小、贝茨码
- 🔄 **格式转换｜Conversions** —— PDF → Word / 图片 / TXT / HTML；图片 → PDF
- 📝 **注释｜Annotations** —— 高亮、下划线、删除线、便签、手绘、图章

---

## 系统架构｜Architecture

```
┌───────────────────────────────────────────────┐
│ 应用窗口（chrome.exe --app，包内 Chromium 优先）  │
│   功能区标签 + PDF.js 渲染画布（常驻）          │
└──────────────────┬────────────────────────────┘
                   │  http://127.0.0.1:<随机端口>
┌──────────────────▼────────────────────────────┐
│ 本地 HTTP 服务（Python 标准库，多线程）         │
│   静态: /, /static/*, /pdfjs/*                │
│   API : 文档字节流 · 操作接口                   │
└──────────────────┬────────────────────────────┘
                   │  进程内 / 子进程
        PyMuPDF · RapidOCR · pdf2docx · qpdf · Ghostscript
```

前端与 PDF 字节流走本地回环 HTTP（PDF.js 依赖 `http(s)` 协议，`file://` 会被 worker / CORS 限制拦截）；文件真实路径取自系统原生打开对话框。
The frontend and PDF byte streams use a local loopback HTTP server (PDF.js needs `http(s)`; `file://` is blocked by worker/CORS limits); real file paths come from the native open dialog.

---

## 功能对照｜Feature Map

| 标签 Tab | 功能 Functions | 引擎 Engine |
|---|---|---|
| 文件 File | 打开 / 保存 / 另存 / 打印 / 最近文件 / 文档属性 / 修复 | PyMuPDF + 系统打印 |
| 视图 View | 缩略图 / 书签 / 缩放 / 全屏 / 夜间 / 文本搜索 | PDF.js |
| 转换 Convert | PDF → Word / 图片 / TXT / HTML；图片 → PDF；OCR | pdf2docx · PyMuPDF · RapidOCR |
| 编辑 Edit | 加文本 / 图片 / 链接 / 水印 / 页眉页脚 / 贝茨码 | PyMuPDF |
| 注释 Annotate | 高亮 / 下划线 / 删除线 / 便签 / 手绘 / 图章 | PDF.js + PyMuPDF 写回 |
| 页面 Pages | 旋转 / 删除 / 提取 / 插入 / 裁剪 / 改页大小 / 排序 / 合并 / 拆分 | PyMuPDF |
| 表单 Forms | 填表 / 创建可填写表单 / 提取数据 / 扁平化 | PyMuPDF AcroForm |
| 保护 Protect | AES-256 加密 / 解密 / 密文黑涂 / 去元数据 | PyMuPDF · qpdf |
| 工具 Tools | 压缩 / 优化 / 批量处理 | qpdf · Ghostscript |

---

## 开源引擎与许可证｜Open-Source Engines & Licenses

所有引擎均为开源、可离线自由使用。引入第三方代码 / 资源时**注明出处与许可证**（项目红线）。
All engines are open source and freely usable offline. Every third-party component is **cited with its source and license**.

| 组件 Component | 用途 Role | 许可证 License | 来源 Source |
|---|---|---|---|
| PDF.js | 渲染 / 阅读器 Rendering / viewer | Apache-2.0 | github.com/mozilla/pdf.js |
| PyMuPDF | PDF 核心引擎 Core engine | AGPL-3.0 | github.com/pymupdf/PyMuPDF |
| RapidOCR | OCR（中 / 英）OCR (zh/en) | Apache-2.0 | github.com/RapidAI/RapidOCR |
| pdf2docx | PDF → Word | MIT | github.com/dothinking/pdf2docx |
| qpdf | 压缩 / 加密 Compression / encryption | Apache-2.0 | github.com/qpdf/qpdf |
| Ghostscript | 格式变换 Transformations | AGPL-3.0 | ghostscript.com |
| PyInstaller | 打包 Packaging | GPL + 例外 | github.com/pyinstaller/pyinstaller |
| Tesseract | OCR（备选）OCR (fallback) | Apache-2.0 | github.com/tesseract-ocr/tesseract |
| LibreOffice（可选）| Office 互转（可选）Interop (optional) | MPL-2.0 | libreoffice.org |

> **AGPL 说明｜AGPL note**：PyMuPDF 的 AGPL 对**个人 / 内部离线使用**零义务；仅当闭源商用分发时才需购买授权或切换 `pypdfium2`（BSD）兜底。
> *AGPL imposes no obligation for personal/internal offline use; a commercial closed-source distribution would require a license change or a `pypdfium2` fallback.*

---

## 目录结构（开发态）｜Project Layout (dev)

```
Qpdf/
├─ app/                    # Python 后端 + 前端四件套
│  ├─ main.py             # 入口：起服务 + 拉起应用窗口（包内 Chromium 优先）
│  ├─ server.py           # 本地静态 HTTP 服务
│  ├─ ops/                # 功能块（每个操作一个文件，注册进框架）
│  └─ frontend/           # index.html / viewer.js / toolbar.js / style.css
├─ docs/开发规格.md        # 开发规格文档
├─ resources/pdfjs/       # PDF.js 发行版（官方 Release 解压，gitignore）
├─ local/                 # 私有区：备份脚本 / token（gitignore，永不上传）
├─ data/                  # 运行时数据（最近文件 / 设置，gitignore）
├─ README.md
└─ requirements.txt       # 仅 pymupdf（外壳为浏览器 --app 模式，无需 pywebview）
```

---

## 快速开始（开发）｜Getting Started (dev)

前置条件 Prerequisites：Windows 10/11、Python 3.12+。

```
git clone https://github.com/qianjiajv/Qpdf.git
cd Qpdf
python -m venv .venv
.venv\Scripts\activate
pip install pymupdf
```

下载 PDF.js 发行版（ES module 构建），解压到 `resources/pdfjs/`，然后：
Download the PDF.js release (ES-module build), extract into `resources/pdfjs/`, then:

```
python app\main.py      # 或双击 run_dev.bat
```

---

## 路线图｜Roadmap

| 阶段 Stage | 内容 Scope | 状态 Status |
|---|---|---|
| 0 | 阅读壳：窗口 + PDF.js 阅读器，打开 / 缩放 / 翻页 | 🚧 进行中 In progress |
| 1 | 功能区骨架、文档状态、撤销栈、拖拽打开、最近文件 | ⏳ |
| 2 | 引擎接入：页面 / 编辑 / 注释 / 表单 / 保护 | ⏳ |
| 3 | OCR、格式转换、压缩、批量队列 | ⏳ |
| 4 | PyInstaller 便携打包、U 盘实测 | ⏳ |
| 5 | 可选增强：LibreOffice 互转、深色模式 | ⏳ |

---

## 已知局限｜Known Limitations

- **PDF 内文字的所见即所得重排**：开源引擎做不到商业级的段落重排，编辑以「定位替换」方式实现（删旧字 → 原位插新字并匹配字体字号）。
  *In-place WYSIWYG text reflow is out of scope for open-source engines; edits are applied as positioned replacements.*
- **PDF → Excel / PPT**：基础可用，复杂表格还原度一般；文本型 PDF 转 Word（`pdf2docx`）效果最好。
  *PDF → Excel/PPT is basic; PDF → Word works best on text-based PDFs.*
- **扫描件**：需先 OCR 才能进行文字级操作；OCR 模型随包一次性分发，之后永久离线。
  *Scanned PDFs need OCR first; the OCR model is bundled once and works offline thereafter.*
- **PyMuPDF 为 AGPL-3.0**：个人 / 内部使用无义务；闭源商用分发需购买授权或切换 `pypdfium2` 兜底。
  *PyMuPDF is AGPL-3.0 — fine for personal/internal use; commercial closed-source distribution needs a license change.*

---

## 工作进度备份｜Progress Backup

本仓库的工作进度通过 `local/backup.ps1`（走 `api.github.com` REST 接口，内容级快照推送）备份到 GitHub；仅白名单内工程文件（`.gitignore` / `README.md` / `app/` / `docs/` / `run_dev.bat` / `requirements.txt`）会被上传，`local/`、`data/`、`resources/pdfjs/`、`.venv/` 永不上传。
Working progress is backed up to GitHub via `local/backup.ps1` (REST snapshot push through `api.github.com`); only whitelisted engineering files are uploaded, while `local/`, `data/`, `resources/pdfjs/`, `.venv/` are never uploaded.

---

## 许可证｜License

项目许可证待定。随包分发的引擎各自保留其开源许可证（见上表）。
Project license to be announced. Bundled engines keep their own open-source licenses (see table above).
