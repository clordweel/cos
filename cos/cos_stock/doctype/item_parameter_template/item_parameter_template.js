// Copyright (c) 2025, BIoT and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Parameter Template', {
    refresh: function (frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Create Item Request'), function () {

                const template_name = frm.doc.name;

                // 🌟 关键修正：使用 frappe.model.with_doctype 和 frappe.model.get_new_doc
                frappe.model.with_doctype('New Item Request', function () {

                    // 1. 在内存中创建一个新的 Doc 对象
                    var new_request_doc = frappe.model.get_new_doc('New Item Request');

                    // 2. 预设字段值
                    // 预设字段名必须与 New Item Request DocType 上的字段名一致
                    new_request_doc.template = template_name;
                    // 命名系列字段会在这里被初始化 (即使 DocName 仍是 'New Item Request-00001')

                    // 3. 导航到新的 Doc 对象
                    // 我们使用 new_request_doc.name，它此时是一个临时客户端名称
                    frappe.set_route('Form', 'New Item Request', new_request_doc.name);
                });

            }, __('Action'));
        }
        
        // JSON 上传下载功能已通过全局脚本 sub_form_json_tools.js 自动应用到所有子表
    }
});

frappe.ui.form.on('Item Parameter Template Definition', { // 监听子表事件 (保持不变)
    // 监听所有动态输入字段的变动
    value_float(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_float'); },
    value_integer(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_integer'); },
    value_doctype(frm, cdt, cdn) { 
        var row = locals[cdt][cdn];
        // 验证：如果设置了 value_doctype，必须先设置 doctype_selector
        if (row.constraint_type === 'Doctype' && row.value_doctype && !row.doctype_selector) {
            frappe.msgprint({
                title: __('验证错误'),
                message: __('文档类型选择器必须首先设置。'),
                indicator: 'red'
            });
            // 清空 value_doctype
            frappe.model.set_value(cdt, cdn, 'value_doctype', null);
            return;
        }
        sync_value(frm, cdt, cdn, 'value_doctype'); 
    },
    value_format(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_format'); },
    
    // 监听 doctype_selector 变化，如果清空则同时清空 value_doctype
    doctype_selector(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (!row.doctype_selector && row.value_doctype) {
            frappe.model.set_value(cdt, cdn, 'value_doctype', null);
        }
    },

    // 监听约束类型变化，用于清空不相关的字段 (防脏数据)
    constraint_type(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        var fields_to_clear = ['value_float', 'value_integer', 'value_format', 'value_doctype'];

        fields_to_clear.forEach(function (fieldname) {
            // 修正清除逻辑，避免清除当前类型对应的值
            const constraint_type = row.constraint_type ? row.constraint_type.toLowerCase().trim() : '';
            const field_is_relevant = fieldname.includes(constraint_type);

            if (row[fieldname] !== null && row[fieldname] !== undefined && !field_is_relevant) {
                frappe.model.set_value(cdt, cdn, fieldname, null);
            }
        });
        
        // 如果约束类型不是 Doctype，清空 doctype_selector 和 value_doctype
        if (row.constraint_type !== 'Doctype') {
            if (row.doctype_selector) {
                frappe.model.set_value(cdt, cdn, 'doctype_selector', null);
            }
            if (row.value_doctype) {
                frappe.model.set_value(cdt, cdn, 'value_doctype', null);
            }
        } else {
            // 如果约束类型是 Doctype，但 doctype_selector 未设置，清空 value_doctype
            if (!row.doctype_selector && row.value_doctype) {
                frappe.model.set_value(cdt, cdn, 'value_doctype', null);
            }
        }

        frappe.model.set_value(cdt, cdn, 'parameter_default_value', null);
    }
});

// 通用同步函数 (必须放在全局，或者在frappe.ui.form.on之外) (保持不变)
function sync_value(frm, cdt, cdn, source_field) {
    var row = locals[cdt][cdn];
    var val = row[source_field];

    if (frappe.get_meta(cdt).fields.find(f => f.fieldname == source_field && f.fieldtype == 'Link')) {
        val = String(val || "");
    } else if (val === null || val === undefined) {
        val = null;
    } else {
        val = String(val);
    }

    frappe.model.set_value(cdt, cdn, 'parameter_default_value', val);

    frm.refresh_field('parameters');
}

// JSON 上传下载功能已通过全局脚本 sub_form_json_tools.js 实现
// 该功能会自动应用到所有带有 allow_bulk_edit 的子表