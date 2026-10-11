// ribbon 渲染 + 全局操作 (规格 §4/§7.1)
// 框架级按钮(打开/另存为等)内置; 功能块按钮由 GET /api/blocks 动态合并, 未实现的灰态占位
// 外壳: PySide6(QtWebEngine) 内嵌窗口; 文件对话框优先走 QWebChannel 桥(原生对话框),
// 普通浏览器开发模式自动降级 File System Access API / input[type=file]
import { viewer } from "/frontend/viewer.js";

let docBytes = null;       // 当前文档字节 (功能块执行入参)
const blockHandlers = {};  // block.id -> handler

// ---------- Qt 壳桥 (QWebChannel): pickOpenPath/pickSavePath → 本地 HTTP 读写 ----------
let qtBridge = null;
function getQtBridge() {
  if (qtBridge) return Promise.resolve(qtBridge);
  return new Promise((resolve) => {
    if (!(window.qt && window.qt.webChannelTransport)) return resolve(null); // 浏览器开发模式
    const s = document.createElement("script");
    s.src = "/frontend/qwebchannel.js";
    s.onload = () => {
      new QWebChannel(window.qt.webChannelTransport, (ch) => {
        qtBridge = ch.objects.bridge || null;
        resolve(qtBridge);
      });
    };
    s.onerror = () => resolve(null);
    document.head.appendChild(s);
  });
}

// ---------- 各标签的静态按钮 ----------
// B0: 文件/首页/视图可用; 其余标签仅占位(待对应功能块点亮)
const STATIC_TABS = [
  { id: "文件", label: "文件", groups: [
    { name: "文档", items: [
      { id: "f.open",  ico: "📂", label: "打开",   act: "open" },
      { id: "f.save",  ico: "💾", label: "另存为", act: "saveAs", needsDoc: true },
      { id: "f.info",  ico: "ℹ",  label: "文档信息", act: "docInfo", needsDoc: true },
    ]},
  ]},
  { id: "首页", label: "首页", groups: [
    { name: "文档", items: [
      { id: "h.open",  ico: "📂", label: "打开",   act: "open" },
      { id: "h.recent", ico: "🕘", label: "最近文件", disabled: true },
    ]},
    { name: "页面", items: [
      { id: "h.prev",  ico: "◀", label: "上一页", act: "prev", needsDoc: true },
      { id: "h.next",  ico: "▶", label: "下一页", act: "next", needsDoc: true },
      { id: "h.first", ico: "⏮", label: "第一页", act: "first", needsDoc: true },
      { id: "h.last",  ico: "⏭", label: "最后页", act: "last", needsDoc: true },
    ]},
  ]},
  { id: "视图", label: "视图", groups: [
    { name: "缩放", items: [
      { id: "v.zin",   ico: "🔍+", label: "放大", act: "zoomIn", needsDoc: true },
      { id: "v.zout",  ico: "🔍-", label: "缩小", act: "zoomOut", needsDoc: true },
      { id: "v.fit",   ico: "↔",   label: "适应宽度", act: "fitW", needsDoc: true },
      { id: "v.fitp",  ico: "⛶",  label: "适应页面", act: "fitP", needsDoc: true },
    ]},
    { name: "显示", items: [
      { id: "v.thumb",  ico: "▤", label: "缩略图", disabled: true },
      { id: "v.dual",   ico: "▥", label: "双页",   disabled: true },
      { id: "v.full",   ico: "⬜", label: "全屏",   disabled: true },
      { id: "v.night",  ico: "🌙", label: "夜间",   disabled: true },
    ]},
  ]},
  { id: "编辑", label: "编辑", groups: [
    { name: "内容", items: [
      { id: "e.text",  ico: "T",  label: "加文字", disabled: true },
      { id: "e.image", ico: "🖼", label: "加图片", disabled: true },
      { id: "e.wm",    ico: "💧", label: "水印",   disabled: true },
      { id: "e.hf",    ico: "📄", label: "页眉页脚", disabled: true },
    ]},
  ]},
  { id: "注释", label: "注释", groups: [
    { name: "标注", items: [
      { id: "c.hl",   ico: "🖍", label: "高亮", disabled: true },
      { id: "c.ul",   ico: "U",  label: "下划线", disabled: true },
      { id: "c.sl",   ico: "S",  label: "删除线", disabled: true },
      { id: "c.note", ico: "📌", label: "便签", disabled: true },
      { id: "c.pen",  ico: "✏",  label: "画笔", disabled: true },
    ]},
  ]},
  { id: "页面", label: "页面", groups: [
    { name: "组织", items: [
      { id: "p.rot",  ico: "↻",  label: "旋转", disabled: true },
      { id: "p.del",  ico: "🗑", label: "删除", disabled: true },
      { id: "p.ins",  ico: "➕", label: "插入", disabled: true },
      { id: "p.re",   ico: "⇅",  label: "重排", disabled: true },
      { id: "p.ext",  ico: "📤", label: "提取", disabled: true },
    ]},
  ]},
  { id: "表单", label: "表单", groups: [
    { name: "表单", items: [
      { id: "fm.fill",  ico: "📝", label: "填表", disabled: true },
      { id: "fm.new",   ico: "🧾", label: "创建", disabled: true },
      { id: "fm.flat",  ico: "🧱", label: "扁平化", disabled: true },
    ]},
  ]},
  { id: "保护", label: "保护", groups: [
    { name: "安全", items: [
      { id: "pr.enc",  ico: "🔒", label: "加密", disabled: true },
      { id: "pr.dec",  ico: "🔓", label: "解密", disabled: true },
      { id: "pr.red",  ico: "⬛", label: "密文黑涂", disabled: true },
      { id: "pr.meta", ico: "🧽", label: "清除元数据", disabled: true },
    ]},
  ]},
  { id: "转换", label: "转换", groups: [
    { name: "导出", items: [
      { id: "cv.word",  ico: "W",  label: "转Word", disabled: true },
      { id: "cv.img",   ico: "🖼", label: "转图片", disabled: true },
      { id: "cv.txt",   ico: "TXT", label: "转TXT", disabled: true },
      { id: "cv.ocr",   ico: "👁", label: "OCR", disabled: true },
      { id: "cv.comp",  ico: "📦", label: "压缩", disabled: true },
    ]},
  ]},
  { id: "帮助", label: "帮助", groups: [
    { name: "关于", items: [
      { id: "hp.about", ico: "❓", label: "关于", act: "about" },
    ]},
  ]},
];

// ---------- 框架级动作 ----------
const ACTIONS = {
  open: async () => {
    // Qt 壳: 原生对话框拿真实路径, 字节走本地 HTTP /api/fs/read
    const bridge = await getQtBridge();
    if (bridge) {
      const path = await bridge.pickOpenPath();
      if (!path) return; // 用户取消
      try {
        const resp = await fetch("/api/fs/read?path=" + encodeURIComponent(path));
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({ error: "HTTP " + resp.status }));
          throw new Error(err.error || "读取失败");
        }
        docBytes = new Uint8Array(await resp.arrayBuffer());
        await viewer.openFromBytes(docBytes, path.split(/[\\/]/).pop());
        refreshEnabled();
      } catch (e) { toast("打开失败: " + (e.message || e), true); }
      return;
    }
    // 浏览器开发模式: File System Access API / input[type=file] 兜底
    let file = null;
    if (window.showOpenFilePicker) {
      try {
        const [handle] = await window.showOpenFilePicker({
          types: [{ description: "PDF 文档", accept: { "application/pdf": [".pdf"] } }],
          multiple: false,
        });
        file = await handle.getFile();
      } catch (e) { return; } // 用户取消
    } else {
      file = await new Promise((resolve) => {
        const inp = document.createElement("input");
        inp.type = "file";
        inp.accept = ".pdf,application/pdf";
        inp.onchange = () => resolve(inp.files[0] || null);
        inp.click();
      });
      if (!file) return;
    }
    docBytes = new Uint8Array(await file.arrayBuffer());
    await viewer.openFromBytes(docBytes, file.name);
    refreshEnabled();
  },
  saveAs: async () => {
    if (!docBytes) return;
    // Qt 壳: 原生对话框选保存路径, 字节走本地 HTTP /api/fs/write
    const bridge = await getQtBridge();
    if (bridge) {
      const path = await bridge.pickSavePath(viewer.state.fileName || "document.pdf");
      if (!path) return; // 用户取消
      try {
        const resp = await fetch("/api/fs/write?path=" + encodeURIComponent(path), { method: "POST", body: docBytes });
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({ error: "HTTP " + resp.status }));
          throw new Error(err.error || "写入失败");
        }
        toast("已保存: " + path.split(/[\\/]/).pop());
      } catch (e) { toast("保存失败: " + (e.message || e), true); }
      return;
    }
    // 浏览器开发模式兜底
    if (window.showSaveFilePicker) {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: viewer.state.fileName || "document.pdf",
          types: [{ description: "PDF 文档", accept: { "application/pdf": [".pdf"] } }],
        });
        const w = await handle.createWritable();
        await w.write(docBytes);
        await w.close();
        toast("已保存: " + handle.name);
      } catch (e) {
        if (e && e.name !== "AbortError") toast("保存失败: " + (e.message || e));
      }
      return;
    }
    const blob = new Blob([docBytes], { type: "application/pdf" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = viewer.state.fileName || "document.pdf";
    a.click();
    URL.revokeObjectURL(a.href);
    toast("已下载: " + a.download);
  },
  docInfo: () => {
    const s = viewer.state;
    alert(`文件: ${s.fileName}\n页数: ${s.pdfDoc ? s.pdfDoc.numPages : "-"}\n缩放: ${Math.round(s.scale * 100)}%`);
  },
  prev: () => viewer.gotoPage(viewer.state.pageNum - 1),
  next: () => viewer.gotoPage(viewer.state.pageNum + 1),
  first: () => viewer.gotoPage(1),
  last: () => viewer.gotoPage(viewer.state.pdfDoc.numPages),
  zoomIn: () => viewer.setScale(viewer.state.scale * 1.15),
  zoomOut: () => viewer.setScale(viewer.state.scale / 1.15),
  fitW: () => { viewer.state.fitMode = "width"; viewer.applyFit(); },
  fitP: () => { viewer.state.fitMode = "page"; viewer.applyFit(); },
  about: () => alert("Qpdf — 便携离线 PDF 工具箱\n单文档 ribbon 工作区\n开源引擎: PDF.js / PyMuPDF"),
};

// ---------- 功能块执行 (契约 /api/ops/<id>) ----------
async function runBlock(id) {
  if (!docBytes) { toast("请先打开文档"); return; }
  const btns = document.querySelectorAll(`[data-block="${id}"]`);
  btns.forEach((b) => (b.disabled = true));
  try {
    const resp = await fetch("/api/ops/" + id, { method: "POST", body: docBytes });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: "HTTP " + resp.status }));
      throw new Error(err.error || "操作失败");
    }
    docBytes = new Uint8Array(await resp.arrayBuffer());
    await viewer.openFromBytes(docBytes, viewer.state.fileName);
    toast("✓ 完成");
  } catch (e) {
    toast("✗ " + e.message, true);
  } finally {
    btns.forEach((b) => (b.disabled = false));
    refreshEnabled();
  }
}

// ---------- 渲染 ----------
let activeTab = "首页";
function render() {
  const tabsEl = document.getElementById("ribbon-tabs");
  const bodyEl = document.getElementById("ribbon-body");
  tabsEl.innerHTML = "";
  bodyEl.innerHTML = "";
  for (const t of STATIC_TABS) {
    const tab = document.createElement("div");
    tab.className = "tab" + (t.id === activeTab ? " active" : "");
    tab.textContent = t.label;
    tab.addEventListener("click", () => { activeTab = t.id; render(); });
    tabsEl.appendChild(tab);
    if (t.id !== activeTab) continue;
    for (const g of t.groups) {
      const gel = document.createElement("div");
      gel.className = "ribbon-group";
      const items = document.createElement("div");
      items.className = "group-items";
      for (const it of g.items) {
        items.appendChild(makeBtn(it));
      }
      // 合并注册到本标签的功能块按钮
      for (const b of (blockList[t.label] || [])) {
        items.appendChild(makeBtn({ id: b.id, ico: "⚙", label: b.label, block: b.id, needsDoc: b.needs_doc }));
      }
      gel.appendChild(items);
      const lab = document.createElement("div");
      lab.className = "group-label";
      lab.textContent = g.name;
      gel.appendChild(lab);
      bodyEl.appendChild(gel);
    }
  }
  refreshEnabled();
}
function makeBtn(it) {
  const b = document.createElement("button");
  b.className = "rbtn";
  b.innerHTML = `<span class="ico">${it.ico}</span><span>${it.label}</span>`;
  if (it.disabled) { b.disabled = true; b.title = "待实现"; }
  if (it.block) { b.dataset.block = it.block; b.addEventListener("click", () => runBlock(it.block)); }
  else if (it.act && ACTIONS[it.act]) { b.dataset.act = it.act; b.addEventListener("click", () => ACTIONS[it.act]()); }
  if (it.needsDoc) b.dataset.needsDoc = "1";
  return b;
}
function refreshEnabled() {
  document.querySelectorAll("[data-needs-doc]").forEach((b) => {
    b.disabled = !docBytes;
  });
}

// ---------- 轻提示 ----------
let toastEl = null;
function toast(msg, isErr) {
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.style.cssText =
      "position:fixed;bottom:44px;left:50%;transform:translateX(-50%);background:#111827;color:#fff;padding:7px 18px;border-radius:8px;font-size:13px;z-index:99;max-width:70vw;";
    document.body.appendChild(toastEl);
  }
  toastEl.style.background = isErr ? "#b91c1c" : "#111827";
  toastEl.textContent = msg;
  toastEl.style.display = "block";
  clearTimeout(toastEl._t);
  toastEl._t = setTimeout(() => (toastEl.style.display = "none"), 2600);
}

// ---------- 功能块列表 ----------
const blockList = {};
async function loadBlocks() {
  try {
    const resp = await fetch("/api/blocks");
    const blocks = await resp.json();
    for (const b of blocks) {
      (blockList[b.tab] = blockList[b.tab] || []).push(b);
    }
    render();
  } catch (e) { /* 框架不因块加载失败而挂 */ }
}

// ---------- 启动 (Qt 壳走 QWebChannel 桥, 浏览器开发模式自动降级) ----------
function boot() {
  render();
  loadBlocks();
  getQtBridge(); // 预热桥连接 (失败不阻塞 UI)
}
boot();
