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
