# Copyright (c) 2026, bit and contributors
# For license information, please see license.txt

import re
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

SERVICE_NAME_RE = re.compile(r"^[a-zA-Z0-9._@-]+$")


class BiometricDevice(Document):
	pass


def _require_biometric_perm() -> None:
	if frappe.session.user == "Administrator":
		return
	roles = frappe.get_roles(frappe.session.user)
	if "System Manager" in roles or "Biometric Manager" in roles:
		return
	frappe.throw(_("Insufficient permission for biometric operations"), frappe.PermissionError)


def _comm_password_int(doc: BiometricDevice) -> int:
	raw = doc.get_password("comm_password", raise_exception=False)
	if raw is None or str(raw).strip() == "":
		return 0
	try:
		return int(str(raw).strip())
	except Exception:
		return 0


def _log_action(device_name: str | None, action: str, status: str, summary: str) -> None:
	try:
		row = {
			"doctype": "Biometric Device Action Log",
			"action": action,
			"status": status,
			"result_summary": (summary or "")[:2000],
			"requested_by": frappe.session.user,
			"requested_at": frappe.utils.now(),
		}
		if device_name:
			row["device"] = device_name
		frappe.get_doc(row).insert(ignore_permissions=True)
	except Exception:
		frappe.logger("biometric").exception("biometric log insert failed")


def _get_device_doc(device_name: str) -> BiometricDevice:
	_require_biometric_perm()
	doc = frappe.get_doc("Biometric Device", device_name)
	if not doc.enabled:
		frappe.throw(_("Device is disabled"))
	return doc


def _validate_service_name(name: str) -> str:
	n = (name or "").strip()
	if not n or not SERVICE_NAME_RE.match(n):
		frappe.throw(_("Invalid systemd unit name"))
	return n


@frappe.whitelist()
def biometric_probe(device_name: str) -> dict[str, Any]:
	doc = _get_device_doc(device_name)
	from cos.cos_biometric.utils.biometric_zk import probe_device

	try:
		out = probe_device(doc.ip_address, int(doc.port or 4370), _comm_password_int(doc))
		_log_action(device_name, "probe", "OK", str(out))
		return {"ok": True, **out}
	except Exception as e:
		_log_action(device_name, "probe", "Error", str(e))
		frappe.throw(str(e))


@frappe.whitelist()
def biometric_fetch_users(device_name: str) -> list[dict[str, Any]]:
	doc = _get_device_doc(device_name)
	from cos.cos_biometric.utils.biometric_zk import list_users_from_device

	try:
		rows = list_users_from_device(doc.ip_address, int(doc.port or 4370), _comm_password_int(doc))
		_log_action(device_name, "fetch_users", "OK", f"count={len(rows)}")
		return rows
	except Exception as e:
		_log_action(device_name, "fetch_users", "Error", str(e))
		frappe.throw(str(e))


@frappe.whitelist()
def biometric_fetch_attendance(
	device_name: str,
	min_year: int | None = None,
	limit: int | None = None,
	only_valid: int | None = None,
) -> list[dict[str, Any]]:
	doc = _get_device_doc(device_name)
	from cos.cos_biometric.utils.biometric_zk import list_attendance_from_device

	my = int(min_year or 2010)
	lim = int(limit or 200)
	ov = 1 if only_valid is None else int(only_valid)
	try:
		rows = list_attendance_from_device(
			doc.ip_address,
			int(doc.port or 4370),
			_comm_password_int(doc),
			min_year=my,
			limit=lim,
			only_valid=bool(ov),
		)
		_log_action(
			device_name,
			"fetch_attendance",
			"OK",
			f"count={len(rows)} only_valid={bool(ov)}",
		)
		return rows
	except Exception as e:
		_log_action(device_name, "fetch_attendance", "Error", str(e))
		frappe.throw(str(e))


@frappe.whitelist()
def biometric_device_restart(device_name: str) -> str:
	doc = _get_device_doc(device_name)
	from cos.cos_biometric.utils.biometric_zk import device_restart

	try:
		device_restart(doc.ip_address, int(doc.port or 4370), _comm_password_int(doc))
		_log_action(device_name, "device_restart", "OK", "sent")
		return "ok"
	except Exception as e:
		_log_action(device_name, "device_restart", "Error", str(e))
		frappe.throw(str(e))


@frappe.whitelist()
def biometric_device_poweroff(device_name: str) -> str:
	doc = _get_device_doc(device_name)
	from cos.cos_biometric.utils.biometric_zk import device_poweroff

	try:
		device_poweroff(doc.ip_address, int(doc.port or 4370), _comm_password_int(doc))
		_log_action(device_name, "device_poweroff", "OK", "sent")
		return "ok"
	except Exception as e:
		_log_action(device_name, "device_poweroff", "Error", str(e))
		frappe.throw(str(e))


@frappe.whitelist()
def biometric_push_attendance_to_hrms(device_name: str, min_year: int | None = None) -> dict[str, Any]:
	doc = _get_device_doc(device_name)
	settings = frappe.get_single("Biometric Sync Settings")
	fieldname = settings.hrms_employee_fieldname or "attendance_device_id"

	from cos.cos_biometric.utils.biometric_zk import zk_connect, zk_disconnect

	zk_inst, conn = zk_connect(doc.ip_address, int(doc.port or 4370), _comm_password_int(doc))
	try:
		rows = list(conn.get_attendance())
	finally:
		zk_disconnect(conn)

	from cos.cos_biometric.utils.biometric_hrms import push_attendance_rows

	ok, err, errors = push_attendance_rows(
		rows,
		device_code=doc.device_code,
		employee_fieldname=fieldname,
		min_year=int(min_year or 2010),
		log_type=None,
	)
	summary = _("success: {0}, failed: {1}").format(ok, err)
	_log_action(device_name, "push_hrms", "OK" if err == 0 else "Error", summary)
	return {"success": ok, "failed": err, "errors": errors[:20], "summary": summary}
