#!/usr/bin/env python3
"""
将 cache 中的文档单向推送到 Outline（documents.update / documents.create）。

依赖：项目根目录 .env 中的 OUTLINE_BASE_URL、OUTLINE_API_KEY。
读取：docs/outline/cache/collection.json、manifest.json、documents/*.md。
可选：--dry-run 仅打印将要执行的操作；--only <path> 仅推送指定 path 的文档。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = PROJECT_ROOT / "docs" / "outline" / "cache"
DOCS_DIR = CACHE_ROOT / "documents"

# UUID 简单匹配（用于区分已有文档 id.md 与 _new_*.md）
UUID_PATTERN = re.compile(
	r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.md$",
	re.I,
)


def _post(base_url: str, api_key: str, path: str, payload: dict) -> dict:
	url = base_url.rstrip("/") + path
	data = json.dumps(payload).encode("utf-8")
	req = request.Request(url, data=data, method="POST")
	req.add_header("Authorization", f"Bearer {api_key}")
	req.add_header("Content-Type", "application/json")
	with request.urlopen(req, timeout=60) as resp:
		body = resp.read().decode("utf-8")
	return json.loads(body)


def _parse_frontmatter_and_body(content: str) -> tuple[dict, str]:
	"""解析 --- ... --- 与正文。frontmatter 为 key: value 行，value 可为 JSON 字符串。"""
	fm = {}
	body = content
	if content.startswith("---"):
		parts = content.split("\n", 1)
		rest = parts[1] if len(parts) > 1 else ""
		idx = rest.find("\n---")
		if idx >= 0:
			fm_block = rest[:idx]
			body = rest[idx + 4:].lstrip("\n")
			for line in fm_block.split("\n"):
				line = line.strip()
				if not line or ":" not in line:
					continue
				k, v = line.split(":", 1)
				k, v = k.strip(), v.strip()
				if v.startswith('"') and v.endswith('"'):
					try:
						v = json.loads(v)
					except Exception:
						pass
				elif v == "null":
					v = None
				fm[k] = v
	return fm, body


def main() -> int:
	parser = argparse.ArgumentParser(description="将 cache 推送到 Outline（单向）")
	parser.add_argument("--dry-run", action="store_true", help="仅打印将要执行的操作，不调用 API")
	parser.add_argument("--only", metavar="PATH", help="仅推送指定 path 的文档（与 manifest pathToId 匹配）")
	args = parser.parse_args()

	base_url = (os.environ.get("OUTLINE_BASE_URL") or "").strip()
	api_key = (os.environ.get("OUTLINE_API_KEY") or "").strip()
	if not base_url or not api_key:
		sys.stderr.write("[outline-push] 缺少 OUTLINE_BASE_URL 或 OUTLINE_API_KEY（请检查 .env）\n")
		return 1

	if not CACHE_ROOT.exists() or not DOCS_DIR.exists():
		sys.stderr.write(f"[outline-push] cache 目录不存在: {DOCS_DIR}\n")
		return 1

	manifest_path = CACHE_ROOT / "manifest.json"
	if not manifest_path.exists():
		sys.stderr.write("[outline-push] manifest.json 不存在，请先执行 outline_pull_cache.py\n")
		return 1

	with open(manifest_path, "r", encoding="utf-8") as f:
		manifest = json.load(f)

	collection_id = manifest.get("collectionId")
	path_to_id = manifest.get("pathToId") or {}
	id_to_path = manifest.get("idToPath") or {}

	updated_manifest = False
	pushed = 0
	errors = 0

	for md_file in sorted(DOCS_DIR.glob("*.md")):
		name = md_file.name
		content = md_file.read_text(encoding="utf-8")
		fm, body = _parse_frontmatter_and_body(content)

		if UUID_PATTERN.match(name):
			doc_id = name[:-3]
			if args.only and id_to_path.get(doc_id) != args.only:
				continue
			if args.dry_run:
				print(f"[dry-run] update {doc_id} (path: {id_to_path.get(doc_id, '')})")
				pushed += 1
				continue
			try:
				_post(base_url, api_key, "/api/documents.update", {
					"id": doc_id,
					"title": fm.get("title") or doc_id,
					"text": body,
					"publish": True,
				})
				print(f"[outline-push] updated {doc_id}")
				pushed += 1
			except Exception as e:
				sys.stderr.write(f"[outline-push] update 失败 {doc_id}: {e}\n")
				errors += 1
			continue

		if name.startswith("_new_") and name.endswith(".md"):
			parent_id = fm.get("parentDocumentId")
			title = fm.get("title") or name
			if not parent_id:
				sys.stderr.write(f"[outline-push] 跳过 {name}: 缺少 parentDocumentId\n")
				continue
			if args.only:
				# 新文档暂无 path，用 title 或 slug 匹配
				slug = name[5:-3]
				if args.only != slug and args.only not in title:
					continue
			if args.dry_run:
				print(f"[dry-run] create under {parent_id}: title={title}")
				pushed += 1
				continue
			try:
				data = _post(base_url, api_key, "/api/documents.create", {
					"collectionId": collection_id,
					"parentDocumentId": parent_id,
					"title": title,
					"text": body,
					"publish": True,
				})
				created = data.get("data") or data
				new_id = created.get("id")
				if new_id:
					new_path = DOCS_DIR / f"{new_id}.md"
					# 重写 frontmatter 带上 id
					fm["id"] = new_id
					fm_lines = ["---"]
					for k, v in fm.items():
						fm_lines.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
					fm_lines.append("---")
					fm_lines.append("")
					new_path.write_text("\n".join(fm_lines) + "\n" + body, encoding="utf-8")
					md_file.unlink()
					path_to_id[title] = new_id
					id_to_path[new_id] = title
					manifest["pathToId"] = path_to_id
					manifest["idToPath"] = id_to_path
					manifest.setdefault("documents", []).append({
						"id": new_id,
						"title": title,
						"path": title,
						"parentDocumentId": parent_id,
					})
					manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
					updated_manifest = True
					print(f"[outline-push] created {new_id} (title: {title})")
					pushed += 1
			except Exception as e:
				sys.stderr.write(f"[outline-push] create 失败 {name}: {e}\n")
				errors += 1

	if args.dry_run:
		print(f"[dry-run] 将执行 {pushed} 次更新/创建")
	elif pushed:
		print(f"[outline-push] 已推送 {pushed} 篇文档")
	if errors:
		sys.stderr.write(f"[outline-push] 失败 {errors} 篇\n")
		return 2
	return 0


if __name__ == "__main__":
	sys.exit(main())
