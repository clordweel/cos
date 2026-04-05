// 立即执行：Material Request 等表单可能在 app_ready 之前加载，需尽早补丁
(function try_patch() {
	function run() {
		if (typeof frappe !== "undefined" && typeof frappe.provide === "function") {
			patch_erpnext_buying_prevent_past_schedule_dates();
			return true;
		}
		return false;
	}
	if (run()) return;
	// frappe 未就绪时：DOMContentLoaded 后再试（若已过则立即执行）
	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", run);
	} else {
		setTimeout(run, 0);
	}
})();

$(document).on('app_ready', () => {
    patch_erpnext_buying_prevent_past_schedule_dates();
    get_company_abbreviation();
    patch_code_field();
});

// COS doctype_js 覆盖了 Purchase Order 的 ERPNext 脚本，需补上 erpnext.buying.prevent_past_schedule_dates
// 供 BuyingController / 物料需求单 / 采购订单表单使用
function patch_erpnext_buying_prevent_past_schedule_dates() {
    frappe.provide('erpnext.buying');
    if (typeof erpnext.buying.prevent_past_schedule_dates !== 'function') {
        erpnext.buying.prevent_past_schedule_dates = function (frm) {
            if (frm.doc.transaction_date && frm.fields_dict?.schedule_date?.datepicker) {
                frm.fields_dict.schedule_date.datepicker.update({
                    minDate: new Date(frm.doc.transaction_date),
                });
            }
        };
    }
}

// 仅将会话公司缩写写到 body[data-company]（供主题/样式等使用）；已弃用侧栏底部公司徽章 DOM 注入。
const get_company_abbreviation = () => {
    const company = frappe.defaults.get_default('company');
    frappe.db.get_value('Company', company, 'abbr').then((r) => {
        if (r?.message?.abbr) {
            $('body').attr('data-company', r.message.abbr);
        }
    });
};


// 重写 Code 字段的初始化逻辑
const patch_code_field = () => {
    if (frappe.ui.form.ControlCode) {
        const standard_make_ace_editor = frappe.ui.form.ControlCode.prototype.make_ace_editor;
        frappe.ui.form.ControlCode.prototype.make_ace_editor = function () {
            standard_make_ace_editor.apply(this, arguments);
            if (this.editor) {
                this.editor.setOption("wrap", true); // 开启换行
                this.editor.setOption("showPrintMargin", false); // 隐藏打印边界线
            }
        };
    }
};
