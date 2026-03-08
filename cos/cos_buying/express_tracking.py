# Copyright (c) 2026, COS and contributors
# License: GNU General Public License v3. See license.txt
"""
快递100 实时查询 API 封装，用于采购运单轨迹查询。
"""

import hashlib
import json
import requests

import frappe
from frappe import _


def _make_sign(param_str: str, key: str, customer: str, swap: bool = False) -> str:
	"""生成快递100签名：MD5(param + key + customer)，32位大写。swap=True 时尝试 param + customer + key"""
	sign_str = param_str + customer + key if swap else param_str + key + customer
	return hashlib.md5(sign_str.encode()).hexdigest().upper()


def _parse_result(data: dict) -> dict:
	"""解析 API 返回，补充 state 中文映射"""
	state_map = {"0": "在途", "1": "已收", "2": "问题件", "3": "已签收", "4": "退签", "5": "派件", "6": "退回"}
	data["state"] = state_map.get(str(data.get("state", "")), data.get("state", ""))
	return data


def query_tracking(courier_code: str, tracking_no: str, phone: str = "", ship_from: str = "", ship_to: str = "") -> dict:
	"""调用快递100实时查询，返回 {state, data: [{context, time, status}]}。参考官方示例：param + key + customer 签名"""
	customer = frappe.conf.get("kuaidi100_customer")
	key = frappe.conf.get("kuaidi100_key")
	if not customer or not key:
		frappe.throw(
			_("未配置快递100 API，请在 site_config.json 设置 kuaidi100_customer、kuaidi100_key")
		)
	# 与成功请求格式一致：紧凑 JSON、含 from/to、phone 完整号、resultv2=0
	param = {
		"com": courier_code.lower().strip(),
		"num": str(tracking_no).strip(),
		"phone": str(phone).strip() if phone else "",
		"from": ship_from or "",
		"to": ship_to or "",
		"resultv2": "0",
		"show": "0",
		"order": "desc",
	}
	param_str = json.dumps(param, separators=(",", ":"))
	swap = frappe.conf.get("kuaidi100_swap_key_customer") or False

	def _do_request(use_swap: bool):
		sign = _make_sign(param_str, key, customer, swap=use_swap)
		resp = requests.post(
			"https://poll.kuaidi100.com/poll/query.do",
			data={"customer": customer, "param": param_str, "sign": sign},
			timeout=10,
		)
		resp.raise_for_status()
		return resp.json()

	def _is_ok(d):
		# 成功：status/returnCode=200，或 message=ok 且有 data
		if str(d.get("status", "")) == "200" or str(d.get("returnCode", "")) == "200":
			return True
		if str(d.get("message", "")) == "ok" and "data" in d:
			return True
		return False

	try:
		data = _do_request(swap)
	except requests.RequestException as e:
		frappe.throw(_("快递100 请求失败: {0}").format(str(e)))
	if not _is_ok(data):
		msg = data.get("message", _("查询失败"))
		if "验证签名失败" in str(msg) and not swap:
			# 自动用 param + customer + key 顺序重试一次
			try:
				data = _do_request(True)
				if _is_ok(data):
					return _parse_result(data)
				frappe.throw(data.get("message", msg))
			except requests.RequestException:
				frappe.throw(
					_("快递100 验证签名失败。请确认 site_config：kuaidi100_customer=授权码、kuaidi100_key=客户授权key")
				)
		if "验证码错误" in str(msg):
			frappe.throw(_("快递公司参数异常：请填写收/寄件人电话（顺丰必填）后重试"))
		frappe.throw(msg)
	return _parse_result(data)


@frappe.whitelist()
def refresh_order_shipment(shipment: str):
	"""根据订单运单 Order Shipment 刷新物流轨迹，仅更新 logistics_status、last_track_time、track_detail。
	status（签收状态）由用户手动确认，不随物流接口结果自动变更。"""
	doc = frappe.get_doc("Order Shipment", shipment)
	doc.check_permission("write")
	if not doc.logistics or not doc.tracking_no:
		frappe.throw(_("请先填写物流公司和运单号"))
	phone = (doc.get("phone") or "").strip()
	if not phone and doc.get("contact"):
		contact = frappe.get_cached_value("Contact", doc.contact, ["mobile_no", "phone"], as_dict=1)
		phone = (contact.get("mobile_no") or contact.get("phone") or "").strip()
	courier_code = (doc.logistics or "").strip().lower()
	if courier_code in ("shunfeng", "sf") and not phone:
		frappe.throw(_("顺丰快递需填写收/寄件人电话"))
	result = query_tracking(courier_code, doc.tracking_no, phone=phone)
	logistics_status = result.get("state") or result.get("status", "")
	detail = result.get("data", [])
	doc.logistics_status = logistics_status
	doc.last_track_time = frappe.utils.now()
	doc.track_detail = json.dumps(detail, ensure_ascii=False)
	doc.save()
	return {
		"logistics_status": logistics_status,
		"detail": detail,
		"last_track_time": doc.last_track_time,
	}
