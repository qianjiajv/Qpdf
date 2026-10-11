// PDF.js 阅读器核心：初始化、渲染、翻页、缩放、搜索
// 配置: cmaps/standardFontDataUrl 防中文方块 (已在前会话踩坑确认)
import * as pdfjsLib from "/pdfjs/build/pdf.mjs";
pdfjsLib.GlobalWorkerOptions.workerSrc = "/pdfjs/build/pdf.worker.mjs";

const canvas = document.getElementById("pdf-canvas");
const ctx = canvas.getContext("2d");
const scroll = document.getElementById("viewer-scroll");
const emptyHint = document.getElementById("empty-hint");
const pageInput = document.getElementById("page-input");
const pageTotal = document.getElementById("page-total");
const zoomVal = document.getElementById("zoom-val");
const statusFile = document.getElementById("status-file");

const state = {
  pdfDoc: null,
  pageNum: 1,
  scale: 1.0,
  fitMode: "width",   // width | page | none
  fileName: "",
};

// ---------- 打开文档 ----------
async function openFromBytes(bytes, fileName) {
  state.fileName = fileName || "未命名.pdf";
  statusFile.textContent = state.fileName;
  document.title = state.fileName + " - Qpdf";
  const task = pdfjsLib.getDocument({
    data: bytes,
    cMapUrl: "/pdfjs/web/cmaps/",
    cMapPacked: true,
    standardFontDataUrl: "/pdfjs/web/standard_fonts/",
  });
  state.pdfDoc = await task.promise;
  state.pageNum = 1;
  emptyHint.hidden = true;
  canvas.hidden = false;
  pageTotal.textContent = "/ " + state.pdfDoc.numPages;
  applyFit();
  window.dispatchEvent(new CustomEvent("qpdf:doc-open", { detail: { numPages: state.pdfDoc.numPages } }));
}

// ---------- 渲染 ----------
let renderTask = null;
async function renderPage() {
  if (!state.pdfDoc) return;
  const page = await state.pdfDoc.getPage(state.pageNum);
  const viewport = page.getViewport({ scale: state.scale });
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(viewport.width * dpr);
  canvas.height = Math.floor(viewport.height * dpr);
  canvas.style.width = viewport.width + "px";
  canvas.style.height = viewport.height + "px";
  if (renderTask) { try { renderTask.cancel(); } catch (e) {} }
  renderTask = page.render({
    canvasContext: ctx,
    viewport,
    transform: dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : null,
  });
  try { await renderTask.promise; } catch (e) { return; }
  pageInput.value = state.pageNum;
  zoomVal.textContent = Math.round(state.scale * 100) + "%";
}

// ---------- 适应模式 ----------
async function applyFit() {
  if (!state.pdfDoc || state.fitMode === "none") return renderPage();
  const page = await state.pdfDoc.getPage(1);
  const vp = page.getViewport({ scale: 1.0 });
  const wrapW = scroll.clientWidth - 40;
  const wrapH = scroll.clientHeight - 40;
  if (state.fitMode === "width") {
    state.scale = wrapW / vp.width;
  } else {
    state.scale = Math.min(wrapW / vp.width, wrapH / vp.height);
  }
  return renderPage();
}

// ---------- 翻页 ----------
function gotoPage(n) {
  if (!state.pdfDoc) return;
  const nn = Math.min(Math.max(1, n | 0), state.pdfDoc.numPages);
  if (nn === state.pageNum) return;
  state.pageNum = nn;
  scroll.scrollTop = 0;
  renderPage();
}

// ---------- 缩放 ----------
function setScale(s) {
  if (!state.pdfDoc) return;
  state.scale = Math.min(Math.max(0.1, s), 10);
  state.fitMode = "none";
  renderPage();
}

// ---------- 快捷键 ----------
window.addEventListener("keydown", (e) => {
  if (!state.pdfDoc) return;
  if (e.target.tagName === "INPUT") return;
  if (e.key === "PageDown" || e.key === "ArrowRight" || e.key === " ") {
    e.preventDefault(); gotoPage(state.pageNum + 1);
  } else if (e.key === "PageUp" || e.key === "ArrowLeft") {
    e.preventDefault(); gotoPage(state.pageNum - 1);
  } else if (e.ctrlKey && (e.key === "=" || e.key === "+")) {
    e.preventDefault(); setScale(state.scale * 1.15);
  } else if (e.ctrlKey && e.key === "-") {
    e.preventDefault(); setScale(state.scale / 1.15);
  } else if (e.ctrlKey && e.key === "0") {
    e.preventDefault(); state.fitMode = "width"; applyFit();
  } else if (e.key === "Home") {
    e.preventDefault(); gotoPage(1);
  } else if (e.key === "End") {
    e.preventDefault(); gotoPage(state.pdfDoc.numPages);
  }
});

// ---------- 控件事件 ----------
document.getElementById("pg-prev").addEventListener("click", () => gotoPage(state.pageNum - 1));
document.getElementById("pg-next").addEventListener("click", () => gotoPage(state.pageNum + 1));
document.getElementById("zoom-in").addEventListener("click", () => setScale(state.scale * 1.15));
document.getElementById("zoom-out").addEventListener("click", () => setScale(state.scale / 1.15));
document.getElementById("zoom-fit").addEventListener("click", () => { state.fitMode = "width"; applyFit(); });
pageInput.addEventListener("change", () => gotoPage(parseInt(pageInput.value, 10)));
window.addEventListener("resize", () => { if (state.fitMode !== "none") applyFit(); });

// ---------- 对外接口 ----------
export const viewer = {
  openFromBytes,
  gotoPage,
  setScale,
  applyFit,
  get state() { return state; },
  get docBytes() { return state._docBytes || null; },
  set docBytes(b) { state._docBytes = b; },
};
