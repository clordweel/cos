# Copyright (c) 2026, COS and contributors
"""已废弃：请勿再用本脚本从 print_format/<subdir> 回写 fixture。

打印格式维护请以 `cos/fixtures/print_format.json` 为唯一真相源（见 `print_format/README.md`）。

若需把仍仅存于子目录的模板一次性并入 JSON，请使用：
  python scripts/merge_print_format_dirs_into_fixture.py
"""

from __future__ import annotations

import sys


def main() -> None:
	sys.stderr.write(
		"已废弃: _sync_print_format_fixture_from_dirs.py\n"
		"请直接编辑 cos/fixtures/print_format.json，或运行 scripts/merge_print_format_dirs_into_fixture.py\n"
		"说明见 print_format/README.md「维护约定」\n"
	)
	sys.exit(1)


if __name__ == "__main__":
	main()
