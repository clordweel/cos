#!/usr/bin/env python3
"""
将 Outline 默认文档集的文档拉取到本地 cache。

依赖：项目根目录 .env 中的 OUTLINE_BASE_URL、OUTLINE_API_KEY。
读取：docs/outline/outline-index.json（collection id 与 nodes 列表）。
输出：docs/outline/cache/collection.json、manifest.json、documents/<id>.md。
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = PROJECT_ROOT / "docs" / "outline" / "outline-index.json"
CACHE_ROOT = PROJECT_ROOT / "docs" / "outline" / "cache"
DOCS_DIR = CACHE_ROOT / "documents"


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
		try:
			err = e.read().decode("utf-8")
		except Exception:
			err = ""
		sys.stderr.write(f"[outline-pull] HTTP {e.code} {path}\n")
		if err:
			sys.stderr.write(f"[outline-pull] {err[:500]}\n")
		raise


def _path_for_id(nodes: dict, paths: dict, doc_id: str) -> str | None:
	"""从 paths 中找出指向 doc_id 的 path（取第一个）。"""
	for path_str, ids in (paths or {}).items():
		if ids and ids[0] == doc_id:
			return path_str
	return None


def main() -> int:
	base_url = (os.environ.get("OUTLINE_BASE_URL") or "").strip()
	api_key = (os.environ.get("OUTLINE_API_KEY") or "").strip()
	if not base_url or not api_key:
		sys.stderr.write("[outline-pull] 缺少 OUTLINE_BASE_URL 或 OUTLINE_API_KEY（请检查 .env）\n")
		return 1

	if not INDEX_PATH.exists():
		sys.stderr.write(f"[outline-pull] 未找到索引: {INDEX_PATH}\n")
		return 1

	with open(INDEX_PATH, "r", encoding="utf-8") as f:
		index = json.load(f)

	collection = index.get("collection") or {}
	collection_id = collection.get("id")
	if not collection_id:
		sys.stderr.write("[outline-pull] outline-index.json 缺少 collection.id\n")
		return 1

	nodes = index.get("nodes") or {}
	paths = index.get("paths") or {}

	CACHE_ROOT.mkdir(parents=True, exist_ok=True)
	DOCS_DIR.mkdir(parents=True, exist_ok=True)

	# 写入 collection.json
	collection_file = CACHE_ROOT / "collection.json"
	collection_file.write_text(
		json.dumps({"name": collection.get("name"), "id": collection_id, "url": collection.get("url")}, ensure_ascii=False, indent=2),
		encoding="utf-8",
	)

	manifest_docs: list[dict] = []
	id_to_path: dict[str, str] = {}
	path_to_id: dict[str, str] = {}

	for doc_id, meta in nodes.items():
		title = (meta.get("title") or "").strip() or doc_id
		path_str = _path_for_id(nodes, paths, doc_id) or title
		parent_id = meta.get("parentDocumentId")
		url = meta.get("url") or ""
		updated_at = meta.get("updatedAt") or ""

		# 拉取正文
		try:
			data = _post(base_url, api_key, "/api/documents.info", {"id": doc_id})
			doc = data.get("data") or data
			text = doc.get("text") or doc.get("content") or ""
		except Exception as e:
			sys.stderr.write(f"[outline-pull] documents.info 失败 {doc_id}: {e}\n")
			text = ""

		# 安全文件名：id 已是 UUID，直接使用
		safe_id = re.sub(r"[^\w\-]", "_", doc_id)
		md_path = DOCS_DIR / f"{doc_id}.md"

		frontmatter = {
			"id": doc_id,
			"title": title,
			"path": path_str,
			"parentDocumentId": parent_id,
			"url": url,
			"updatedAt": updated_at,
		}
		fm_lines = ["---"]
		for k, v in frontmatter.items():
			if v is None:
				v = ""
			fm_lines.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
		fm_lines.append("---")
		fm_lines.append("")
		body = (text or "").rstrip()
		if body and not body.endswith("\n"):
			body += "\n"
		content = "\n".join(fm_lines) + "\n" + body

		md_path.write_text(content, encoding="utf-8")

		manifest_docs.append({"id": doc_id, "title": title, "path": path_str, "parentDocumentId": parent_id})
		id_to_path[doc_id] = path_str
		path_to_id[path_str] = doc_id

	manifest = {
		"collectionId": collection_id,
		"idToPath": id_to_path,
		"pathToId": path_to_id,
		"documents": manifest_docs,
	}
	manifest_file = CACHE_ROOT / "manifest.json"
	manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

	print(f"[outline-pull] collection: {collection.get('name')} ({collection_id})")
	print(f"[outline-pull] cache: {CACHE_ROOT}")
	print(f"[outline-pull] documents: {len(manifest_docs)}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
