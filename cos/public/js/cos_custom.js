$(document).on('app_ready', () => {
    get_company_abbreviation();
    patch_code_field();
});

// 获取当前会话公司的缩写并设置到body的data-company属性
const get_company_abbreviation = () => {
    const company = frappe.defaults.get_default('company');

    // 获取当前会话公司的缩写并设置到body的data-company属性
    frappe.db.get_value('Company', company, 'abbr').then((r) => {
        if (r?.message?.abbr) {
            const { abbr } = r.message;
            $('body').attr('data-company', abbr);

            // 注入公司缩写标签
            const companyBadge = $('<a>')
                .attr('onclick', `return frappe.ui.toolbar.setup_session_defaults()`)
                .attr('id', 'company-abbreviation-badge')
                .text(`${company} (${abbr})`);

            // 如果已存在则先移除
            $('#company-abbreviation-badge').remove();
            $('.body-sidebar').append(companyBadge);
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