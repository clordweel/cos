// 立即执行：Material Request 等表单可能在 app_ready 之前加载，需尽早补丁
if (typeof frappe !== "undefined") {
	patch_erpnext_buying_prevent_past_schedule_dates();
}

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

// 获取当前会话公司的缩写并设置到body的data-company属性
const get_company_abbreviation = () => {
    const company = frappe.defaults.get_default('company');

    // 获取当前会话公司的缩写并设置到body的data-company属性
    frappe.db.get_value('Company', company, 'abbr').then((r) => {
        if (r?.message?.abbr) {
            const { abbr } = r.message;
            $('body').attr('data-company', abbr);

            // 注入公司标签
            // 全称标签（展开时显示）
            const companyBadge = $('<a>')
                .attr('id', 'company-abbreviation-badge')
                .attr('onclick', `return frappe.ui.toolbar.setup_session_defaults()`)
                .attr('class', 'custom-company-badge')
                .text(`${company} (${abbr})`);
            // 缩写标签（折叠时显示）
            const abbrBadge = $('<a>')
                .attr('id', 'abbr-company-abbreviation-badge')
                .attr('onclick', `return frappe.ui.toolbar.setup_session_defaults()`)
                .attr('class', 'custom-company-badge abbr')
                .text(`${abbr}`);

            // 如果已存在则先移除
            $('#company-abbreviation-badge').remove();
            $('#abbr-company-abbreviation-badge').remove();
            $('.body-sidebar').append(companyBadge);
            $('.body-sidebar').append(abbrBadge);
        } else {
            console.log("Company abbreviation not found.");
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
