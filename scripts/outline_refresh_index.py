#!/usr/bin/env python3
"""
刷新 Outline 默认文档集的目录索引（不含密钥）。

依赖环境变量（来自项目根目录 .env）：
- OUTLINE_BASE_URL
- OUTLINE_API_KEY
- OUTLINE_DEFAULT_COLLECTION（默认：COS 文档）

输出文件：
- docs/outline/outline-index.json
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib import request
from urllib.error import HTTPError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = PROJECT_ROOT / "docs" / "outline" / "outline-index.json"


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _post(base_url: str, api_key: str, path: str, payload: dict) -> dict:
	url = base_url.rstrip("/") + path
	data = json.dumps(payload).encode("utf-8")
	req = request.Request(url, data=data, method="POST")
	req.add_header("Authorization", f"Bearer {api_key}")
	req.add_header("Content-Type", "application/json")
	try:
		with request.urlopen(req, timeout=60) as resp:
			body = resp.read().decode("utf-8")
		return json.loads(body)
	except HTTPError as e:
		# 不输出任何密钥，仅输出服务端错误摘要，便于排查
		try:
			err = e.read().decode("utf-8")
		except Exception:
			err = ""
		print(f"[outline-index] HTTP {e.code} {path}")
		if err:
			print(f"[outline-index] error_body: {err[:800]}")
		raise


def _list_documents(
	base_url: str,
	api_key: str,
	collection_id: str,
	parent_document_id: str | None,
) -> list[dict]:
	out: list[dict] = []
	offset = 0
	while True:
		payload: dict = {"collectionId": collection_id, "limit": 100, "offset": offset}
		if parent_document_id is not None:
			payload["parentDocumentId"] = parent_document_id
		data = _post(base_url, api_key, "/api/documents.list", payload)
		items = data.get("data") or []
		out.extend(items)
		if len(items) < 100:
			break
		offset += 100
		if offset > 50_000:
			break
	return out


def main() -> int:
	base_url = (os.environ.get("OUTLINE_BASE_URL") or "").strip()
	api_key = (os.environ.get("OUTLINE_API_KEY") or "").strip()
	collection_name = (os.environ.get("OUTLINE_DEFAULT_COLLECTION") or "COS 文档").strip()

	if not base_url or not api_key:
		print("[outline-index] 缺少 OUTLINE_BASE_URL 或 OUTLINE_API_KEY（请检查 .env）")
		return 1

	cols = _post(base_url, api_key, "/api/collections.list", {"limit": 100, "offset": 0})
	collection = None
	for c in cols.get("data") or []:
		if c.get("name") == collection_name:
			collection = c
			break
	if not collection:
		print(f"[outline-index] 未找到默认文档集：{collection_name}")
		return 1

	collection_id = collection.get("id")
	if not collection_id:
		print("[outline-index] collections.list 返回缺少 collectionId，终止。")
		return 1

	nodes: dict[str, dict] = {}
	children: dict[str | None, list[str]] = defaultdict(list)

	# 根目录
	root_docs = _list_documents(base_url, api_key, collection_id, None)
	root_ids: list[str] = []
	for d in root_docs:
		doc_id = d.get("id")
		if not doc_id:
			continue
		nodes[doc_id] = d
		root_ids.append(doc_id)

	# BFS 递归拉取
	queue = list(root_ids)
	seen = set(queue)
	while queue:
		parent_id = queue.pop(0)
		kids = _list_documents(base_url, api_key, collection_id, parent_id)
		for k in kids:
			doc_id = k.get("id")
			if not doc_id:
				continue
			nodes[doc_id] = k
			children[parent_id].append(doc_id)
			if doc_id not in seen:
				seen.add(doc_id)
				queue.append(doc_id)
		# 防止极端情况无限增长
		if len(nodes) > 10_000:
			print("[outline-index] 文档数量超过 10000，已停止继续抓取（请确认是否存在循环/异常结构）。")
			break

	# 反向建立 parent -> children（根 parent 为 None）
	for doc_id, d in nodes.items():
		pid = d.get("parentDocumentId")
		if pid is None:
			continue
		# children[pid] 在上面已填充；这里只做补全不会漏掉的 parent（例如某些 list 返回不一致）
		if doc_id not in children[pid]:
			children[pid].append(doc_id)

	def title_of(doc_id: str) -> str:
		return (nodes.get(doc_id) or {}).get("title") or ""

	def parent_of(doc_id: str) -> str | None:
		return (nodes.get(doc_id) or {}).get("parentDocumentId")

	def build_path(doc_id: str) -> str:
		parts: list[str] = []
		cur: str | None = doc_id
		guard: set[str] = set()
		while cur and cur not in guard and len(parts) < 40:
			guard.add(cur)
			parts.append(title_of(cur) or f"<untitled:{cur[:8]}>")
			cur = parent_of(cur)
		return "/".join(reversed(parts))

	# 同父级重名检查（用于提示整理）
	dup_counter = Counter()
	for doc_id, d in nodes.items():
		t = (d.get("title") or "").strip()
		dup_counter[(d.get("parentDocumentId"), t)] += 1
	dups = [(k, c) for k, c in dup_counter.items() if k[1] and c > 1]

	# 构建 paths：path -> [ids]
	paths: dict[str, list[str]] = defaultdict(list)
	for doc_id in nodes.keys():
		paths[build_path(doc_id)].append(doc_id)

	# 输出索引（仅保留必要字段，不包含正文 text）
	index_nodes: dict[str, dict] = {}
	for doc_id, d in nodes.items():
		index_nodes[doc_id] = {
			"title": d.get("title"),
			"url": d.get("url"),
			"collectionId": d.get("collectionId"),
			"parentDocumentId": d.get("parentDocumentId"),
			"updatedAt": d.get("updatedAt"),
			"archivedAt": d.get("archivedAt"),
			"childCount": len(children.get(doc_id) or []),
		}

	index = {
		"schemaVersion": 1,
		"generatedAt": _now_iso(),
		"collection": {"name": collection_name, "id": collection_id, "url": collection.get("url")},
		"rootIds": root_ids,
		"nodes": index_nodes,
		"paths": dict(sorted(paths.items(), key=lambda kv: kv[0])),
	}

	OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
	# 注意：本仓库 .editorconfig 对 .json 指定了奇特的 1-space 缩进，这里保持一致
	OUT_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")

	print(f"[outline-index] collection: {collection_name} ({collection_id})")
	print(f"[outline-index] wrote: {OUT_FILE.relative_to(PROJECT_ROOT)}")
	print(f"[outline-index] nodes: {len(index_nodes)}, roots: {len(root_ids)}")
	if dups:
		print(f"[outline-index] 注意：发现同父级重名 {len(dups)} 组（仅展示前 10）")
		for (pid, t), c in dups[:10]:
			pname = "(根目录)" if pid is None else (title_of(pid) or pid[:8] + "…")
			print(f'  - 父级 {pname} 下标题“{t}”重复 {c} 次')
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

