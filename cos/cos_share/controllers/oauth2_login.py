"""
社交登录后自动绑定 Logto User 角色
使用 on_login 和 on_session_creation 钩子在用户登录后自动处理角色绑定
"""
import frappe
from frappe import _


def on_login(login_manager):
	"""
	登录后钩子函数
	检查用户是否通过 COS 社交登录，如果是，自动绑定 Logto User 角色
	
	Args:
		login_manager: Frappe 的登录管理器对象
	"""
	try:
		user = login_manager.user
		
		# 跳过系统用户
		if user in ("Administrator", "Guest"):
			return
		
		# 方法1: 检查 login_manager 中是否有 provider 信息（首次登录时）
		provider = getattr(login_manager, "provider", None)
		
		if provider == "COS":
			_bind_logto_user_role(user)
			return
		
		# 方法2: 检查用户是否有 COS 社交登录记录（已存在的用户）
		has_cos_social_login = frappe.db.exists(
			"User Social Login",
			{"parent": user, "provider": "COS"}
		)
		
		if has_cos_social_login:
			_bind_logto_user_role(user)
		
	except Exception as e:
		frappe.log_error(
			f"登录后角色绑定处理失败: {str(e)}\nUser: {login_manager.user if hasattr(login_manager, 'user') else 'Unknown'}",
			"Logto User Role Binding Error"
		)


def _bind_logto_user_role(user):
	"""
	将用户绑定到 Logto User 角色
	
	Args:
		user: 用户名
	"""
	try:
		# 检查 Logto User 角色是否存在
		if not frappe.db.exists("Role", "Logto User"):
			return
		
		# 获取用户文档
		user_doc = frappe.get_doc("User", user)
		
		# 检查用户是否已有 Logto User 角色
		has_role = any(role.role == "Logto User" for role in user_doc.get("roles", []))
		
		# 如果没有角色，添加角色
		if not has_role:
			user_doc.append("roles", {
				"role": "Logto User"
			})
			user_doc.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.logger().info(f"已自动为用户 {user} 绑定 Logto User 角色")
		
	except Exception as e:
		frappe.log_error(
			f"绑定 Logto User 角色失败: {str(e)}\nUser: {user}",
			"Logto User Role Binding Error"
		)
