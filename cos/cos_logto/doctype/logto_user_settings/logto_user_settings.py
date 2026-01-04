# Copyright (c) 2026, bit and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import requests
import base64


class LogtoUserSettings(Document):
	@frappe.whitelist()
	def update_logto_user_password(self):
		"""
		仅更新 Logto 管理器中的用户密码
		"""
		if not self.user or not self.password:
			frappe.throw(_("请先选择用户并输入密码"))
		
		if not self.server or not self.client_id or not self.client_secret:
			frappe.throw(_("请先配置 Logto M2M 连接信息"))

		# 使用表单中的 user_id（由前端自动填充）
		logto_sub = self.user_id
		if not logto_sub:
			frappe.throw(_("请先选择用户以获取 Logto User ID"))

		# 更新 Logto 远程密码
		try:
			access_token = self._get_logto_management_token()
			self._patch_logto_password(logto_sub, access_token)
			
			# 成功后清除当前表单的密码字段（安全考虑）
			self.password = ""
			
			return {"status": "success", "message": _("用户 {0} 的 Logto 密码已成功更新").format(self.user)}
		
		except Exception as e:
			if isinstance(e, frappe.ValidationError):
				raise e
			frappe.log_error(frappe.get_traceback(), _("Logto 远程密码更新失败"))
			frappe.throw(_("Logto 密码更新失败：{0}").format(str(e)))

	def _get_logto_management_token(self):
		"""
		通过 M2M 凭据获取 Management API 的 Access Token
		参考 curl 命令使用 Basic Auth 方式
		"""
		token_endpoint = f"{self.server.rstrip('/')}/oidc/token"
		resource = self.api_resource_indicator or "https://default.logto.app/api"
		
		# 使用 Basic Auth: base64(client_id:client_secret)
		credentials = f"{self.client_id}:{self.client_secret}"
		basic_auth = base64.b64encode(credentials.encode()).decode()
		
		headers = {
			"Authorization": f"Basic {basic_auth}",
			"Content-Type": "application/x-www-form-urlencoded"
		}
		
		# 使用 application/x-www-form-urlencoded 格式
		data = {
			"grant_type": "client_credentials",
			"resource": resource,
			"scope": "all"
		}
		
		try:
			response = requests.post(token_endpoint, data=data, headers=headers, timeout=10)
			response.raise_for_status()
			result = response.json()
			access_token = result.get("access_token")
			
			if not access_token:
				frappe.throw(_("获取 Logto Access Token 失败：响应中未包含 access_token"))
			
			return access_token
		except requests.exceptions.HTTPError as e:
			frappe.log_error(f"Logto Token API Error: {e.response.text if hasattr(e, 'response') else str(e)}", "Logto Token API")
			frappe.throw(_("获取 Logto Access Token 失败 (Status {0}): {1}").format(
				e.response.status_code if hasattr(e, 'response') else 'Unknown',
				e.response.text if hasattr(e, 'response') else str(e)
			))
		except Exception as e:
			frappe.throw(_("获取 Logto Access Token 失败: {0}").format(str(e)))

	def _patch_logto_password(self, logto_sub, access_token):
		"""
		调用 Logto Management API 修改密码
		参考 curl: PATCH /api/users/{id}/password
		"""
		api_url = f"{self.server.rstrip('/')}/api/users/{logto_sub}/password"
		
		headers = {
			"Authorization": f"Bearer {access_token}",
			"Content-Type": "application/json",
			"accept": "application/json"
		}
		
		payload = {
			"password": self.password
		}
		
		try:
			response = requests.patch(api_url, json=payload, headers=headers, timeout=10)
			
			if response.status_code == 200:
				return
			
			if response.status_code == 403:
				frappe.throw(_("Logto 权限不足：请确保 M2M 应用已授权访问 Management API"))
			
			frappe.log_error(f"Logto API Error {response.status_code}: {response.text}", "Logto API Debug")
			frappe.throw(_("Logto API 调用失败 (Status {0}): {1}").format(response.status_code, response.text))
		except requests.exceptions.HTTPError as e:
			if isinstance(e, frappe.ValidationError):
				raise e
			frappe.log_error(f"Logto Password API Error: {e.response.text if hasattr(e, 'response') else str(e)}", "Logto Password API")
			frappe.throw(_("调用 Logto API 时发生错误: {0}").format(str(e)))
		except Exception as e:
			if isinstance(e, frappe.ValidationError):
				raise e
			frappe.throw(_("调用 Logto API 时发生错误: {0}").format(str(e)))
