# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""Worker Portal API：供登录页/工作台检查登录状态，需 allow_guest 以支持 WebView/Capacitor 首次加载。

Token 鉴权：使用 Bearer token 替代 cookies，解决 iOS WebView 下 cookie 不可靠问题。
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils.password import check_password

# Worker Portal Token 前缀，用于区分 OAuth Bearer
WPT_PREFIX = "wpt."
CACHE_KEY_PREFIX = "worker_portal_token:"
TOKEN_EXPIRY_DAYS = 7


def _session_user_ok_for_wpt() -> str | None:
	"""返回可用于签发/恢复 wpt 的登录用户名；Guest/None/空/库中不存在 均视为未登录。"""
	su = frappe.session.user
	if not su or su == "Guest":
		return None
	if not isinstance(su, str):
		return None
	su = su.strip()
	if not su:
		return None
	if not frappe.db.exists("User", su):
		return None
	return su


def _wpt_cache_value_to_username(cached) -> str | None:
	"""Redis/pickle 可能返回 str 或 bytes；非法类型视为无缓存。"""
	if cached is None:
		return None
	if isinstance(cached, (bytes, bytearray)):
		try:
			cached = cached.decode("utf-8")
		except Exception:
			return None
	if not isinstance(cached, str):
		return None
	u = cached.strip()
	return u if u else None


def normalize_session_user_none_to_guest():
	"""auth_hooks 收尾：在部分请求下 LoginManager 结束后 session.user 仍为 None（既非 Guest）。

	此时若未成功通过 Bearer wpt 换身份，下游会把 None 当作 User 主键查询，触发 **User None not found**。
	强制回落为 Guest，使权限与 API 与「未登录」语义一致（如请先登录），而非框架级 DoesNotExist。
	"""
	if not getattr(frappe.local, "initialised", False):
		return
	try:
		su = frappe.session.user
	except Exception:
		su = None
	if su is None:
		frappe.set_user("Guest")


@frappe.whitelist(allow_guest=True)
def get_logged_user():
	"""返回当前登录用户，Guest 时返回 'Guest'。供 worker-portal 登录页判断是否已登录。"""
	return frappe.session.user or "Guest"


@frappe.whitelist(allow_guest=True, methods=["POST"])
def login_for_token(usr: str = None, pwd: str = None):
	"""使用账号密码登录，返回 Bearer token。供 React/WebView 使用，避免依赖 cookies。

	返回: {"token": "wpt.xxx", "user": "user@example.com"}
	"""
	if not (usr and pwd):
		frappe.throw(_("Username and password required"), frappe.ValidationError)

	user = frappe.db.get_value("User", usr, ["name", "enabled"], as_dict=True)
	if not user or not user.enabled:
		frappe.throw(_("Invalid credentials"), frappe.AuthenticationError)

	try:
		check_password(usr, pwd)
	except frappe.AuthenticationError:
		frappe.throw(_("Invalid credentials"), frappe.AuthenticationError)

	token = frappe.generate_hash(length=32)
	cache_key = f"{CACHE_KEY_PREFIX}{token}"
	expires_in_sec = TOKEN_EXPIRY_DAYS * 24 * 3600
	frappe.cache.set_value(cache_key, user.name, expires_in_sec=expires_in_sec)

	return {"token": f"{WPT_PREFIX}{token}", "user": user.name}


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def issue_token_from_session():
	"""在已具备 Frappe 登录会话（Cookie sid 等）时签发 Worker Portal Bearer token。

	供移动端壳在打开 WebView 前刷新 wpt，避免仅依赖密码登录时写入的 token 过期、
	或冷启动仅恢复 sid 而未带 wpt 导致 Portal 无法鉴权。
	"""
	su = _session_user_ok_for_wpt()
	if not su:
		# 勿仅用 == Guest：session.user 在部分边界请求下可能为 None，若仍写入 cache
		# 会导致后续 Bearer 请求不 set_user 却带着「伪 token」，进而触发 User None not found。
		frappe.throw(_("Login required"), frappe.AuthenticationError)
	raw = frappe.generate_hash(length=32)
	cache_key = f"{CACHE_KEY_PREFIX}{raw}"
	expires_in_sec = TOKEN_EXPIRY_DAYS * 24 * 3600
	frappe.cache.set_value(cache_key, su, expires_in_sec=expires_in_sec)
	return {"token": f"{WPT_PREFIX}{raw}"}


def validate_worker_portal_token():
	"""auth_hooks：校验 Authorization: Bearer wpt.xxx 并设置用户。"""
	auth = frappe.get_request_header("Authorization") or ""
	parts = auth.split(" ", 1)
	if len(parts) != 2 or parts[0].lower() != "bearer":
		return
	token = parts[1].strip()
	if not token.startswith(WPT_PREFIX):
		return
	raw = token[len(WPT_PREFIX) :]
	cache_key = f"{CACHE_KEY_PREFIX}{raw}"
	cached = frappe.cache.get_value(cache_key)
	user = _wpt_cache_value_to_username(cached)
	if not user or user == "Guest" or not frappe.db.exists("User", user):
		# 坏缓存（历史 bug 曾写入 None/非法串）：删掉以免客户端长期携带无效 wpt
		if cached is not None:
			try:
				frappe.cache.delete_value(cache_key)
			except Exception:
				pass
		return
	frappe.set_user(user)
	# Frappe LoginManager 在 Guest 会话初始化（非 resume）时会对 Website User 写入
	# frappe.local.response["message"] = "No App" 等登录占位字段（见 frappe/auth.py set_user_info）。
	# 若后续 handler 未覆盖 message（例如返回 None），API JSON 会错误携带该串。
	# Bearer wpt 已成功鉴权后应清除这些与当前 RPC 无关的字段。
	banner = frappe.local.response.get("message")
	if banner in ("No App", "Logged In", "Password Reset"):
		frappe.local.response.pop("message", None)
		frappe.local.response.pop("home_page", None)


# --- 采购垫付报销审批 ---


@frappe.whitelist()
def list_pi_reimbursement_pending_approval(limit=50, tab="pending"):
	"""返回员工垫付 + 已提交的采购发票列表，供 Worker Portal 登录审批。

	tab: all | pending | approved | rejected（默认 pending：待处理，与历史行为一致）
	"""
	limit = int(limit) if limit is not None else 50
	tab = (tab or "pending").strip().lower()
	filters = {
		"docstatus": 1,
		"custom_is_employee_advance": 1,
	}
	or_filters = None

	if tab == "all":
		pass
	elif tab == "pending":
		or_filters = [
			["custom_reimbursement_approval_status", "=", "Pending"],
			["custom_reimbursement_approval_status", "is", "not set"],
			["custom_reimbursement_approval_status", "=", ""],
		]
	elif tab == "approved":
		filters["custom_reimbursement_approval_status"] = "Approved"
	elif tab == "rejected":
		filters["custom_reimbursement_approval_status"] = "Rejected"
	else:
		or_filters = [
			["custom_reimbursement_approval_status", "=", "Pending"],
			["custom_reimbursement_approval_status", "is", "not set"],
			["custom_reimbursement_approval_status", "=", ""],
		]

	data = frappe.get_all(
		"Purchase Invoice",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"supplier",
			"custom_advance_employee",
			"grand_total",
			"posting_date",
			"bill_no",
			"custom_reimbursement_approval_status",
		],
		order_by="posting_date desc",
		limit=limit,
	)
	for row in data:
		emp_id = row.get("custom_advance_employee")
		row["employee_name"] = (
			frappe.db.get_value("Employee", emp_id, "employee_name") if emp_id else None
		)
	return data


@frappe.whitelist()
def list_employee_advance_pending(limit=50, approved_only=1):
	"""返回员工垫付未报销的采购发票列表，供审批页展示。
	approved_only=1 时仅返回报销审批已通过的 PI，便于财务创建 JE。"""
	limit = int(limit) if limit is not None else 50
	approved_only = int(approved_only) if approved_only is not None else 1
	filters = {
		"docstatus": 1,
		"custom_is_employee_advance": 1,
		"custom_employee_reimbursed": "未报销",
	}
	if approved_only:
		# 仅展示审批通过的；历史数据无此字段视为通过（向后兼容）
		filters["custom_reimbursement_approval_status"] = ["in", ["Approved", None, ""]]
	data = frappe.get_all(
		"Purchase Invoice",
		filters=filters,
		fields=[
			"name",
			"supplier",
			"custom_advance_employee",
			"grand_total",
			"posting_date",
			"custom_payable_transfer_je",
			"custom_reimbursement_approval_status",
		],
		order_by="posting_date desc",
		limit=limit,
	)
	# 补充员工真实姓名
	for row in data:
		emp_id = row.get("custom_advance_employee")
		row["employee_name"] = (
			frappe.db.get_value("Employee", emp_id, "employee_name") if emp_id else None
		)
	return data


@frappe.whitelist()
def get_purchase_invoice_detail(name: str = None):
	"""返回采购发票详情，供审批详情页展示。"""
	name = name or frappe.form_dict.get("name")
	if not name or not frappe.db.exists("Purchase Invoice", name):
		frappe.throw(_("Purchase Invoice not found"), frappe.DoesNotExistError)
	doc = frappe.get_doc("Purchase Invoice", name)
	if doc.docstatus != 1:
		frappe.throw(_("Purchase Invoice must be submitted"))
	if not doc.get("custom_is_employee_advance"):
		frappe.throw(_("Not an employee advance invoice"))
	emp_id = doc.get("custom_advance_employee")
	employee_name = frappe.db.get_value("Employee", emp_id, "employee_name") if emp_id else None
	return {
		"name": doc.name,
		"supplier": doc.supplier,
		"custom_advance_employee": emp_id,
		"employee_name": employee_name,
		"grand_total": doc.grand_total,
		"posting_date": str(doc.posting_date) if doc.posting_date else None,
		"custom_payable_transfer_je": doc.get("custom_payable_transfer_je"),
		"custom_employee_reimbursed": doc.get("custom_employee_reimbursed") or "未报销",
		"custom_reimbursement_approval_status": doc.get("custom_reimbursement_approval_status") or "Pending",
		"custom_reimbursement_approved_by": doc.get("custom_reimbursement_approved_by"),
		"custom_reimbursement_approved_on": str(doc.custom_reimbursement_approved_on) if doc.get("custom_reimbursement_approved_on") else None,
		"custom_reimbursement_remark": doc.get("custom_reimbursement_remark"),
		"items": [
			{
				"item_code": row.item_code,
				"item_name": row.item_name,
				"qty": row.qty,
				"rate": row.rate,
				"amount": row.amount,
			}
			for row in (doc.get("items") or [])
		],
	}


@frappe.whitelist()
def create_payable_transfer_je(docname: str = None):
	"""创建应付转员工日记账。包装 cos_accounts 方法。"""
	docname = docname or frappe.form_dict.get("docname")
	if not docname:
		frappe.throw(_("docname is required"), frappe.ValidationError)
	from cos.cos_accounts.utils.employee_advance_payable_transfer import create_payable_transfer_je as _create

	return _create(docname)
