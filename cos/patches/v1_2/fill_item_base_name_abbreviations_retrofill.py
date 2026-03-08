"""对缩写为空的基础名再次执行缩写填充（数据在首次 migrate 之后才导入时使用）。"""
from __future__ import annotations

from cos.patches.v1_2.fill_item_base_name_abbreviations import run_fill_abbreviations


def execute():
    run_fill_abbreviations()
