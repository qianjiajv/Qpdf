# -*- coding: utf-8 -*-
"""功能块注册表。

按规格 §7.1：每个功能块是 app/ops/ 下的一个文件，导出 BLOCK dict（id/tab/label/order/needs_doc）
和可选的 run(doc_bytes, params) -> bytes。此模块扫描该目录、收集所有 BLOCK，
供前端渲染 ribbon 按钮、供 API 路由 /api/ops/<id> 分发。
"""
import importlib
import os
import sys

OPS_DIR = os.path.dirname(os.path.abspath(__file__))

_registry = {}  # id -> module
_blocks = []    # BLOCK dicts (sorted)


def _load_blocks():
    """扫描 ops 目录，加载每个 *.py 中的 BLOCK 定义。"""
    global _blocks, _registry
    for name in sorted(os.listdir(OPS_DIR)):
        if not name.endswith(".py") or name.startswith("_"):
            continue
        mod_name = name[:-3]
        try:
            mod = importlib.import_module(f"app.ops.{mod_name}")
        except Exception as e:  # 单个块加载失败不拖垮框架
            print(f"[ops] 加载失败 {mod_name}: {e}", file=sys.stderr)
            continue
        block = getattr(mod, "BLOCK", None)
        if not isinstance(block, dict):
            continue
        bid = block.get("id")
        if not bid:
            continue
        block.setdefault("tab", "首页")
        block.setdefault("label", bid)
        block.setdefault("order", 100)
        block.setdefault("needs_doc", True)
        _registry[bid] = mod
        _blocks.append(block)
    _blocks.sort(key=lambda b: (b.get("tab", ""), b.get("order", 999)))


def get_blocks():
    """返回按标签和 order 排序的功能块定义列表（供前端渲染 ribbon）。"""
    if not _blocks and not _registry:
        _load_blocks()
    return list(_blocks)


def run_op(op_id: str, doc_bytes: bytes, params: dict) -> bytes:
    """执行一个功能块的 run()，返回新文档字节。

    若功能块未定义 run（纯展示/占位块），原样返回 doc_bytes。
    """
    if not _registry and not _blocks:
        _load_blocks()
    mod = _registry.get(op_id)
    if mod is None:
        raise ValueError(f"未知功能块: {op_id}")
    run = getattr(mod, "run", None)
    if run is None:
        return doc_bytes
    return run(doc_bytes, params or {})


# 模块加载时立即扫描一次
_load_blocks()
