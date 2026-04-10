# Copyright (c) 2026, bit and contributors
# For license information, please see license.txt

"""HRMS Employee Checkin \u5199\u5165\uff08\u540c\u673a Python \u8c03\u7528\uff09"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _


def _employee_field_value_from_attendance_row(r) -> str | None:
	raw_user = getattr(r, "user_id", None)
	internal_uid = getattr(r, "uid", None)
	ts = getattr(r, "timestamp", None)
	if not isinstance(ts, datetime):
		return None
	if raw_user is not None and str(raw_user).strip():
		return str(raw_user).strip()
	if internal_uid is not None and str(internal_uid).strip() and str(internal_uid).strip() != "0":
		return str(internal_uid).strip()
	return None


def fmt_ts(dt: datetime) -> str:
	return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def _log_type_from_zk_punch(r) -> str | None:
	"""从 pyzk Attendance.punch 推导 HRMS Employee Checkin.log_type。

	常见 ZK：0=签到 IN、1=签退 OUT；2/3 常表示外出/返回（与 pyzk 社区约定一致），映射为 OUT/IN。
	仍无法识别时返回 None，由调用方设置 skip_auto_attendance（见 push_attendance_rows），避免 HRMS
	「班次严格按 Log Type」时在无 log_type 下整批插入失败。
	"""
	p = getattr(r, "punch", None)
	if p is None:
		return None
	try:
		v = int(p)
	except Exception:
		return None
	if v == 0:
		return "IN"
	if v == 1:
		return "OUT"
	if v == 2:
		return "OUT"
	if v == 3:
		return "IN"
	return None


def push_attendance_rows(
	rows: list,
	*,
	device_code: str,
	employee_fieldname: str,
	min_year: int = 2010,
	log_type: str | None = None,
) -> tuple[int, int, list[str]]:
	"""返回 (success_count, fail_count, errors)。

	:param log_type: 若指定，则**每条**记录都使用该类型；若为 None，则按行用 ZK ``punch`` 推导；
		推导不出时传 ``skip_auto_attendance=1``，以便在班次「严格按 Log Type」时仍能插入（否则多数记录会失败）。
	"""
	try:
		from hrms.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field
	except Exception:
		frappe.throw(_("HRMS \u672a\u5b89\u88c5\u6216\u65e0\u6cd5\u5bfc\u5165 employee_checkin"))

	from cos.cos_biometric.utils.biometric_zk import filter_attendance_records

	ok = 0
	err = 0
	errors: list[str] = []
	filtered = filter_attendance_records(list(rows), min_year)
	for r in filtered:
		emp = _employee_field_value_from_attendance_row(r)
		if not emp:
			err += 1
			errors.append(_("skip: no user for row"))
			continue
		ts = getattr(r, "timestamp", None)
		if not isinstance(ts, datetime):
			err += 1
			continue
		kwargs: dict[str, Any] = {
			"employee_field_value": emp,
			"timestamp": fmt_ts(ts),
			"device_id": device_code,
			"employee_fieldname": employee_fieldname or "attendance_device_id",
		}
		lt = log_type if log_type else _log_type_from_zk_punch(r)
		if lt:
			kwargs["log_type"] = lt
		elif not log_type:
			# HRMS：班次为「Strictly based on Log Type」且 log_type 为空时会拒绝插入；未知 punch 时跳过该校验
			kwargs["skip_auto_attendance"] = 1
		try:
			add_log_based_on_employee_field(**kwargs)
			ok += 1
		except Exception as e:
			err += 1
			errors.append(str(e)[:500])
	return ok, err, errors
