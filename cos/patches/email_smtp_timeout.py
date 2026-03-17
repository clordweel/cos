# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""延长 Email Account SMTP 校验超时。

Frappe 默认 15 秒，连接 Brevo 等海外 SMTP 时 TLS+AUTH 可能超时。
本 patch 将校验超时改为 60 秒。
"""


def patch():
	from frappe.email.doctype.email_account import email_account as mod

	if getattr(mod.EmailAccount, "_cos_smtp_timeout_patched", False):
		return

	_orig = mod.EmailAccount.sendmail_config

	def sendmail_config(self):
		config = _orig(self)
		if getattr(self, "flags", None) and getattr(self.flags, "validate_smtp_connection", False):
			config["timeout"] = 60
		return config

	mod.EmailAccount.sendmail_config = sendmail_config
	mod.EmailAccount._cos_smtp_timeout_patched = True
