import frappe
from frappe.contacts.doctype.address.address import get_address_display


def update_address_display(doc, method=None):
	"""
	更新地址的 custom_address_display 字段，使用地址模板渲染完整地址
	
	Args:
		doc: Address doctype 实例
		method: 事件方法名称（可选）
	"""
	if not doc:
		return
	
	try:
		# 获取地址字典，排除系统字段
		address_dict = doc.as_dict()
		
		# 使用 Frappe 的 get_address_display 方法获取格式化的地址
		# get_address_display 接受地址名称或地址字典
		address_display = get_address_display(address_dict)
		
		# 更新自定义字段
		if hasattr(doc, 'custom_address_display'):
			doc.custom_address_display = address_display
	except Exception as e:
		frappe.log_error(
			message=f"更新地址显示失败: {str(e)}\n地址: {doc.name if hasattr(doc, 'name') else 'Unknown'}",
			title="Address Display Update Error"
		)
