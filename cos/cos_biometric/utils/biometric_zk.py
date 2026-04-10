# Copyright (c) 2026, bit and contributors
# For license information, please see license.txt

"""ZK/pyzk \u8fde\u63a5\u4e0e\u6570\u636e\u5e8f\u5217\u5316\uff08\u8003\u52e4\u673a\u7ba1\u7406 GUI\uff09"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import add_days, now_datetime


def _get_pyzk():
	try:
		from zk import ZK

		return ZK
	except ImportError:
		frappe.throw(
			_("bench \u73af\u5883\u672a\u5b89\u88c5 pyzk\uff0c\u8bf7\u6267\u884c: bench pip install pyzk"),
			title="pyzk",
		)


def zk_connect(ip_address: str, port: int, password: int, timeout: int = 30):
	ZK = _get_pyzk()
	zk = ZK(str(ip_address).strip(), port=int(port or 4370), timeout=int(timeout or 30), password=int(password or 0))
	conn = zk.connect()
	return zk, conn


def zk_disconnect(conn) -> None:
	if not conn:
		return
	try:
		conn.disconnect()
	except Exception:
		pass


def serialize_user(u) -> dict[str, Any]:
	return {
		"uid": getattr(u, "uid", None),
		"user_id": getattr(u, "user_id", None) or "",
		"name": getattr(u, "name", None) or "",
		"privilege": getattr(u, "privilege", None),
		"card": getattr(u, "card", None),
		"group_id": getattr(u, "group_id", None),
	}


def serialize_attendance_row(r) -> dict[str, Any]:
	ts = getattr(r, "timestamp", None)
	return {
		"user_id": getattr(r, "user_id", None) or "",
		"uid": getattr(r, "uid", None),
		"timestamp": ts.isoformat() if isinstance(ts, datetime) else str(ts),
		"status": getattr(r, "status", None),
		"punch": getattr(r, "punch", None),
	}


def filter_attendance_records(records: list, min_year: int) -> list:
	"""\u4e0e ai_cos_ops sync_once \u903b\u8f91\u4e00\u81f4\uff1a\u5e74\u4efd\u8fc7\u4f4e\u6216\u65e0\u6709\u6548\u7528\u6237\u952e\u7684\u8bb0\u5f55\u53ef\u6392\u9664\u5c55\u793a\u3002

	ZK \u8bbe\u5907\u7f13\u5b58\u4e2d\u5e38\u6709\u5360\u4f4d/\u635f\u574f\u6761\u76ee\uff08\u7a7a user_id\u3001\u5f02\u5e38 uid\u3001\u672a\u6765\u5e74\u4efd\u5982 2044\u3001\u975e\u6cd5 punch\uff09\uff0c\u4e0d\u5e94\u8fdb\u5165 HRMS\u3002
	"""
	out = []
	now = now_datetime()
	max_ts = add_days(now, 366)
	for r in records:
		ts = getattr(r, "timestamp", None)
		if not isinstance(ts, datetime):
			continue
		if ts.year < int(min_year or 2010):
			continue
		if ts > max_ts:
			continue
		raw_user = getattr(r, "user_id", None)
		internal_uid = getattr(r, "uid", None)
		if raw_user is not None and str(raw_user).strip():
			pass
		elif internal_uid is not None and str(internal_uid).strip() and str(internal_uid).strip() != "0":
			pass
		else:
			continue
		out.append(r)
	return out


def list_users_from_device(ip_address: str, port: int, password: int) -> list[dict[str, Any]]:
	zk_inst, conn = zk_connect(ip_address, port, password)
	try:
		users = conn.get_users()
	except Exception as e:
		zk_disconnect(conn)
		raise e
	try:
		return [serialize_user(u) for u in users]
	finally:
		zk_disconnect(conn)


def list_attendance_from_device(
	ip_address: str,
	port: int,
	password: int,
	*,
	min_year: int = 2010,
	limit: int = 200,
	only_valid: bool = True,
) -> list[dict[str, Any]]:
	"""从设备读取考勤缓存。

	:param limit: 返回条数上限。**0** 表示不截断（过滤后全部返回，受设备缓存大小与请求超时影响）。
		大于 0 时，在设备返回的有序列表上**只保留末尾最近 limit 条**（多数设备时间为升序，即最新一段）。
	:param only_valid: True 时经 :func:`filter_attendance_records` 过滤（年份、异常时间、无用户键等）。
	"""
	def _tail(seq: list, lim: int) -> list:
		if lim <= 0 or len(seq) <= lim:
			return seq
		return seq[-lim:]

	zk_inst, conn = zk_connect(ip_address, port, password)
	try:
		raw = list(conn.get_attendance())
	except Exception as e:
		zk_disconnect(conn)
		raise e
	try:
		if only_valid:
			filtered = filter_attendance_records(raw, min_year)
			# limit>0 时最多保留最近 lim 条；limit==0 为全量
			lim = int(limit)
			if lim > 0:
				lim = min(lim, 100000)
			filtered = _tail(filtered, lim)
			return [serialize_attendance_row(r) for r in filtered]
		rows = [serialize_attendance_row(r) for r in raw]
		lim = int(limit)
		if lim > 0:
			lim = min(lim, 100000)
		rows = _tail(rows, lim)
		return rows
	finally:
		zk_disconnect(conn)


def probe_device(ip_address: str, port: int, password: int) -> dict[str, Any]:
	"""\u8fde\u63a5\u5e76\u8bfb\u53d6\u7528\u6237\u6570\u4e0e\u7f13\u5b58\u6761\u6570\u3002"""
	zk_inst, conn = zk_connect(ip_address, port, password)
	try:
		users = conn.get_users()
		att = list(conn.get_attendance())
	finally:
		zk_disconnect(conn)
	return {"user_count": len(users), "attendance_count": len(att)}


def device_restart(ip_address: str, port: int, password: int) -> None:
	zk_inst, conn = zk_connect(ip_address, port, password)
	try:
		conn.restart()
	finally:
		zk_disconnect(conn)


def device_poweroff(ip_address: str, port: int, password: int) -> None:
	zk_inst, conn = zk_connect(ip_address, port, password)
	try:
		conn.poweroff()
	finally:
		zk_disconnect(conn)
