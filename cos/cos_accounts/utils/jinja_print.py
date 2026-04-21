# Copyright (c) 2026, COS and contributors
"""财务相关打印模板 Jinja 全局方法。"""

from __future__ import annotations

from cos.cos_accounts.utils.currency import get_rmb_upper


def rmb_upper_amount(amount):
	"""金额中文大写（人民币），供打印格式 Jinja 使用。"""
	return get_rmb_upper(amount)
