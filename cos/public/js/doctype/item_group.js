frappe.ui.form.on('Item Group', {
    refresh: function (frm) {
        if (!frm.is_new()) {
            // 添加一个名为“税务管理”的下拉菜单
            frm.add_custom_button(__('Cleanup Legacy Templates (Global)'), function () {
                // 执行清理逻辑
                handle_cleanup(frm);
            }, __('Tax Tools'));

            frm.add_custom_button(__('Sync to Child Items'), function () {
                // 执行同步逻辑
                handle_sync(frm);
            }, __('Tax Tools'));

            // 将菜单加粗或变色，突出显示
            frm.page.set_inner_btn_group_dot(__('Tax Tools'), 'orange');
        }
    }
});

// --- 清理逻辑 ---
function handle_cleanup(frm) {
    frappe.confirm(__('<b>Dangerous Operation:</b> This will globally delete all legacy templates with titles containing "(Output)" or "(Input)" and force unbind items. Are you sure?'), () => {
        frappe.prompt([
            { label: 'Please enter CLEANUP to confirm', fieldname: 'confirm', fieldtype: 'Data', reqd: 1 }
        ], (data) => {
            if (data.confirm === 'CLEANUP') {
                frappe.call({
                    method: "cos.cos_accounts.api.tax.bulk_cleanup_tax_templates",
                    args: { keyword: "(Output)" },
                    callback: function () {
                        frappe.call({
                            method: "cos.cos_accounts.api.tax.bulk_cleanup_tax_templates",
                            args: { keyword: "(Input)" },
                            callback: function (r) {
                                frappe.show_alert({ message: __('Legacy Template Cleanup Completed'), indicator: 'green' });
                            }
                        });
                    }
                });
            }
        }, __('Security Verification'), __('Execute Cleanup'));
    });
}

// --- 同步逻辑 ---
function handle_sync(frm) {
    if (frm.is_dirty()) {
        frappe.msgprint(__('Please save the current item group changes before syncing.'));
        return;
    }
    frappe.confirm(__('Are you sure you want to sync the current tax rate {0}% to all items in this group and its child groups?', [frm.doc.custom_standard_tax_rate]), () => {
        frappe.show_alert({ message: __('Syncing, please wait...'), indicator: 'blue' });
        frappe.call({
            method: "cos.cos_accounts.api.tax.sync_group_taxes_to_items",
            args: { item_group: frm.doc.name },
            callback: function (r) {
                if (r.message) {
                    frappe.msgprint(r.message.message);
                }
            }
        });
    });
}