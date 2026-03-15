"""
公司税费科目校验：保存时验证 custom_selling_tax_account、custom_buying_tax_account 所指科目存在且归属该公司。
"""
import frappe
from frappe import _


def validate_company_tax_accounts(doc, method=None):
    """
    Company 保存前校验：税费科目字段若已设置，则所指 Account 必须存在且 company 与当前公司一致。
    """
    tax_fields = [
        ("custom_selling_tax_account", _("销售税科目 (Selling Tax Account)")),
        ("custom_buying_tax_account", _("采购税科目 (Buying Tax Account)")),
    ]
    for fieldname, label in tax_fields:
        acc = doc.get(fieldname)
        if not acc:
            continue
        row = frappe.db.get_value("Account", acc, ["name", "company"], as_dict=True)
        if not row:
            frappe.throw(
                _("{0} 所指科目「{1}」不存在，请检查或清空后重试。").format(label, acc)
            )
        if row.company != doc.name:
            frappe.throw(
                _("{0} 所指科目「{1}」属于公司「{2}」，与当前公司「{3}」不一致。").format(
                    label, acc, row.company, doc.name
                )
            )
