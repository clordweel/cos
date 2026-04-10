# Copyright (c) 2026, bit and contributors
# For license information, please see license.txt

"""ZK/pyzk \u8fde\u63a5\u4e0e\u6570\u636e\u5e8f\u5217\u5316\uff08\u8003\u52e4\u673a\u7ba1\u7406 GUI\uff09"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _


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
	"""\u4e0e ai_cos_ops sync_once \u903b\u8f91\u4e00\u81f4\uff1a\u5e74\u4efd\u8fc7\u4f4e\u6216\u65e0\u6709\u6548\u7528\u6237\u952e\u7684\u8bb0\u5f55\u53ef\u6392\u9664\u5c55\u793a\u3002"""
	out = []
	for r in records:
		ts = getattr(r, "timestamp", None)
		if not isinstance(ts, datetime):
			continue
		if ts.year < int(min_year or 2010):
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
	_, conn = zk_connect(ip_address, port, password)
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
	"""only_valid=False 时返回设备缓存内全部记录（含占位/异常时间），仍受 limit 截断。"""
	lim = max(1, min(int(limit or 200), 2000))
	_, conn = zk_connect(ip_address, port, password)
	try:
		raw = list(conn.get_attendance())
	except Exception as e:
		zk_disconnect(conn)
		raise e
	try:
		if only_valid:
			filtered = filter_attendance_records(raw, min_year)
			if len(filtered) > lim:
				filtered = filtered[-lim:]
			return [serialize_attendance_row(r) for r in filtered]
		rows = [serialize_attendance_row(r) for r in raw]
		if len(rows) > lim:
			rows = rows[-lim:]
		return rows
	finally:
		zk_disconnect(conn)


def probe_device(ip_address: str, port: int, password: int) -> dict[str, Any]:
	"""\u8fde\u63a5\u5e76\u8bfb\u53d6\u7528\u6237\u6570\u4e0e\u7f13\u5b58\u6761\u6570\u3002"""
	_, conn = zk_connect(ip_address, port, password)
	try:
		users = conn.get_users()
		att = list(conn.get_attendance())
	finally:
		zk_disconnect(conn)
	return {"user_count": len(users), "attendance_count": len(att)}


def device_restart(ip_address: str, port: int, password: int) -> None:
	_, conn = zk_connect(ip_address, port, password)
	try:
		conn.restart()
	finally:
		zk_disconnect(conn)


def device_poweroff(ip_address: str, port: int, password: int) -> None:
	_, conn = zk_connect(ip_address, port, password)
	try:
		conn.poweroff()
	finally:
		zk_disconnect(conn)
