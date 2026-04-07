# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""兼容 Frappe 17 dev：core/doctype/version/version.py 在 get_diff 中调用
frappe.db.get_values(..., ignore_ifnull=True)，而 Database.get_values 若尚未声明该参数会抛出 TypeError。

剥离未知关键字，行为与未传该参数一致（与当前 get_values 实现一致）。
上游 Database 正式支持 ignore_ifnull 后可移除此 patch。
"""


def patch():
	try:
		from frappe.database.database import Database
	except ImportError:
		return

	if getattr(Database.get_values, "_cos_ignore_ifnull_patched", False):
		return

	_orig = Database.get_values

	def get_values(self, *args, **kwargs):
		kwargs.pop("ignore_ifnull", None)
		return _orig(self, *args, **kwargs)

	get_values._cos_ignore_ifnull_patched = True
	Database.get_values = get_values
