# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""采购发票员工垫付：报销审批 API（链接审批、生成链接）。"""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse

import frappe
from frappe import _


TOKEN_EXPIRY_DAYS = 7


def _get_secret() -> str:
	"""获取签名密钥。"""
	secret = frappe.conf.get("encryption_key") or frappe.conf.get("secret_key") or ""
	if not secret:
		frappe.throw(
			_("系统未配置 encryption_key，无法生成审批链接"),
			title=_("配置缺失"),
		)
	return secret


def _sign_params(params: dict) -> str:
	"""对参数字典生成 HMAC-SHA256 签名。"""
	secret = _get_secret()
	# 按 key 排序后拼接，与常见做法一致
	parts = [f"{k}={v}" for k, v in sorted(params.items()) if v is not None]
	msg = "|".join(parts)
	sig = hmac.new(
		secret.encode("utf-8"),
		msg.encode("utf-8"),
		hashlib.sha256,
	).hexdigest()
	return sig


def _verify_token(pi_name: str, expiry: str, signature: str) -> bool:
	"""校验 token 签名与过期时间。"""
	if not all([pi_name, expiry, signature]):
		return False
	try:
		exp_ts = int(expiry)
		if time.time() > exp_ts:
			return False
	except (ValueError, TypeError):
		return False
	params = {"expiry": expiry, "pi_name": pi_name}
	expected = _sign_params(params)
	return hmac.compare_digest(expected, signature)


@frappe.whitelist()
def get_approval_url(pi_name: str, approver_user: str = "", base_url: str = "") -> str:
	"""生成带签名的报销审批链接。需 Purchase Invoice 读权限。"""
	frappe.has_permission("Purchase Invoice", "read", throw=True)
	if not pi_name or not frappe.db.exists("Purchase Invoice", pi_name):
		frappe.throw(_("采购发票 {0} 不存在").format(pi_name or ""), title=_("参数错误"))
	pi = frappe.get_doc("Purchase Invoice", pi_name)
	if not pi.get("custom_is_employee_advance"):
		frappe.throw(_("该发票未勾选员工垫付"), title=_("无法生成链接"))
	exp_ts = int(time.time()) + TOKEN_EXPIRY_DAYS * 24 * 3600
	params = {"pi_name": pi_name, "expiry": str(exp_ts)}
	signature = _sign_params(params)
	params["_signature"] = signature
	query = urllib.parse.urlencode(params)
	if not base_url:
		base_url = frappe.utils.get_url()
	# 审批页部署在 Worker Portal
	path = "/worker-portal/pi-reimbursement-approval"
	if base_url.rstrip("/").endswith("/app") or "/app/" in base_url:
		base_url = base_url.split("/app")[0]
	url = f"{base_url.rstrip('/')}{path}?{query}"
	return url


def _pi_summary_payload(pi) -> dict:
	"""从 Purchase Invoice 文档构造审批页摘要（与链接审批、登录审批共用）。"""
	emp_id = pi.get("custom_advance_employee")
	employee_name = frappe.db.get_value("Employee", emp_id, "employee_name") if emp_id else None
	return {
		"name": pi.name,
		"supplier": pi.supplier,
		"grand_total": pi.grand_total,
		"advance_employee": emp_id,
		"employee_name": employee_name,
		"bill_no": pi.get("bill_no") or "-",
		"posting_date": str(pi.posting_date) if pi.posting_date else None,
	}


def _apply_pi_reimbursement_decision(pi_name: str, action: str, remark: str) -> dict:
	"""校验业务状态后写入审批结果。调用方需已通过 token 或权限校验。"""
	if not frappe.db.exists("Purchase Invoice", pi_name):
		frappe.throw(_("采购发票不存在"), title=_("无法审批"))
	pi = frappe.get_doc("Purchase Invoice", pi_name)
	if not pi.get("custom_is_employee_advance"):
		frappe.throw(_("该发票未勾选员工垫付"), title=_("无法审批"))
	status = pi.get("custom_reimbursement_approval_status") or "Pending"
	if status != "Pending":
		frappe.throw(
			_("该发票已审批，当前状态：{0}").format(status),
			title=_("无法重复审批"),
		)
	action = (action or "approve").lower()
	if action not in ("approve", "reject"):
		frappe.throw(_("action 必须为 approve 或 reject"), title=_("参数错误"))
	new_status = "Approved" if action == "approve" else "Rejected"
	approved_by = frappe.session.user if frappe.session.user != "Guest" else None
	frappe.db.set_value(
		"Purchase Invoice",
		pi_name,
		{
			"custom_reimbursement_approval_status": new_status,
			"custom_reimbursement_approved_by": approved_by,
			"custom_reimbursement_approved_on": frappe.utils.now(),
			"custom_reimbursement_remark": (remark or "")[:140],
		},
		update_modified=True,
	)
	frappe.db.commit()
	return {"success": True, "status": new_status, "message": _("已批准") if action == "approve" else _("已拒绝")}


def _parse_token_params(token: str = None, pi_name: str = None, expiry: str = None, _signature: str = None) -> tuple:
	"""从 token 或单独参数解析 pi_name, expiry, _signature。"""
	if pi_name and expiry and _signature:
		return pi_name, expiry, _signature
	if token:
		query = token.split("?")[-1] if "?" in (token or "") else (token or "")
		parsed = urllib.parse.parse_qs(query)
		pi_name = (parsed.get("pi_name") or [None])[0]
		expiry = (parsed.get("expiry") or [None])[0]
		_signature = (parsed.get("_signature") or [None])[0]
	return pi_name, expiry, _signature


@frappe.whitelist(allow_guest=True)
def get_pi_summary_for_approval(token: str = None, pi_name: str = None, expiry: str = None, _signature: str = None) -> dict:
	"""校验 token 后返回 PI 摘要，供审批页展示。allow_guest 以支持链接免登录审批。"""
	pi_name, expiry, _signature = _parse_token_params(token, pi_name, expiry, _signature)
	if not all([pi_name, expiry, _signature]):
		frappe.throw(_("链接无效或已过期"), title=_("无法审批"))
	if not _verify_token(pi_name, expiry, _signature):
		frappe.throw(_("链接无效或已过期"), title=_("无法审批"))
	if not frappe.db.exists("Purchase Invoice", pi_name):
		frappe.throw(_("采购发票不存在"), title=_("无法审批"))
	pi = frappe.get_doc("Purchase Invoice", pi_name)
	if not pi.get("custom_is_employee_advance"):
		frappe.throw(_("该发票未勾选员工垫付"), title=_("无法审批"))
	status = pi.get("custom_reimbursement_approval_status") or "Pending"
	if status != "Pending":
		frappe.throw(
			_("该发票已审批，当前状态：{0}").format(status),
			title=_("无法重复审批"),
		)
	return _pi_summary_payload(pi)


@frappe.whitelist(allow_guest=True)
def approve_pi(token: str = None, pi_name: str = None, expiry: str = None, _signature: str = None, action: str = "approve", remark: str = "") -> dict:
	"""审批通过或拒绝。action: approve | reject。"""
	pi_name, expiry, _signature = _parse_token_params(token, pi_name, expiry, _signature)
	if not all([pi_name, expiry, _signature]):
		frappe.throw(_("链接无效或已过期"), title=_("无法审批"))
	if not _verify_token(pi_name, expiry, _signature):
		frappe.throw(_("链接无效或已过期"), title=_("无法审批"))
	action = (action or "approve").lower()
	if action not in ("approve", "reject"):
		frappe.throw(_("action 必须为 approve 或 reject"), title=_("参数错误"))
	return _apply_pi_reimbursement_decision(pi_name, action, remark)


@frappe.whitelist()
def get_pi_summary_for_logged_in_approval(pi_name: str = None) -> dict:
	"""已登录用户查看某张 PI 的报销审批摘要（需 Purchase Invoice 读权限）。"""
	pi_name = pi_name or frappe.form_dict.get("pi_name")
	if frappe.session.user == "Guest":
		frappe.throw(_("请先登录"), title=_("无法审批"))
	if not pi_name or not frappe.db.exists("Purchase Invoice", pi_name):
		frappe.throw(_("采购发票不存在"), title=_("无法审批"))
	pi = frappe.get_doc("Purchase Invoice", pi_name)
	frappe.has_permission("Purchase Invoice", "read", doc=pi, throw=True)
	if not pi.get("custom_is_employee_advance"):
		frappe.throw(_("该发票未勾选员工垫付"), title=_("无法审批"))
	status = pi.get("custom_reimbursement_approval_status") or "Pending"
	payload = _pi_summary_payload(pi)
	# 已决状态：允许只读打开详情（书签/双开/列表滞后），避免抛错；批准/拒绝仍由 approve_pi_logged_in 拦截
	if status != "Pending":
		payload["readonly"] = True
		payload["reimbursement_approval_status"] = status
	return payload


@frappe.whitelist()
def approve_pi_logged_in(pi_name: str = None, action: str = "approve", remark: str = "") -> dict:
	"""已登录用户批准/拒绝报销审批（需 Purchase Invoice 写权限）。"""
	pi_name = pi_name or frappe.form_dict.get("pi_name")
	if frappe.session.user == "Guest":
		frappe.throw(_("请先登录"), title=_("无法审批"))
	if not pi_name or not frappe.db.exists("Purchase Invoice", pi_name):
		frappe.throw(_("采购发票不存在"), title=_("无法审批"))
	pi = frappe.get_doc("Purchase Invoice", pi_name)
	frappe.has_permission("Purchase Invoice", "write", doc=pi, throw=True)
	return _apply_pi_reimbursement_decision(pi_name, action, remark)
