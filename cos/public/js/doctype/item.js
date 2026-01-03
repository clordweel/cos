frappe.ui.form.on('Item', {
    refresh: function (frm) {
        if (!frm.is_new()) {
            // 添加诊断按钮
            frm.add_custom_button(__('Diagnose Item Tax Settings'), function () {
                handle_diagnose_tax(frm);
            }, __('Tax Tools'));

            // 添加手动更新税率按钮
            frm.add_custom_button(__('Update Item Tax Templates'), function () {
                handle_update_tax(frm);
            }, __('Tax Tools'));
        }
    }
});

// --- 诊断逻辑 ---
function handle_diagnose_tax(frm) {
    frappe.call({
        method: "cos.cos_accounts.controllers.tax.diagnose_item_tax",
        args: { item_code: frm.doc.name },
        freeze: true,
        callback: function (r) {
            if (r.message) {
                let result = r.message;
                let message = `<h4>物料税率诊断结果</h4>`;
                message += `<p><b>物料代码:</b> ${result.item_code}</p>`;
                message += `<p><b>物料名称:</b> ${result.item_name}</p>`;
                message += `<p><b>物料组:</b> ${result.item_group || '未设置'}</p>`;

                if (result.tax_rate) {
                    message += `<p><b>税率:</b> ${result.tax_rate}%</p>`;
                }

                message += `<h5>当前税率模板:</h5>`;
                if (result.current_taxes && result.current_taxes.length > 0) {
                    message += `<ul>`;
                    result.current_taxes.forEach(tax => {
                        message += `<li>${tax.template || '未设置'}</li>`;
                    });
                    message += `</ul>`;
                } else {
                    message += `<p style="color: red;">未设置税率模板</p>`;
                }

                if (result.expected_taxes && result.expected_taxes.length > 0) {
                    message += `<h5>期望的税率模板:</h5>`;
                    message += `<ul>`;
                    result.expected_taxes.forEach(tax => {
                        message += `<li>${tax.template}</li>`;
                    });
                    message += `</ul>`;
                }

                if (result.companies && result.companies.length > 0) {
                    message += `<h5>公司状态:</h5>`;
                    message += `<ul>`;
                    result.companies.forEach(company => {
                        let status = '';
                        if (company.template_created) {
                            status = `<span style="color: green;">✓ 已创建模板: ${company.template_name}</span>`;
                        } else if (company.missing_accounts) {
                            status = `<span style="color: red;">✗ 缺少科目: ${company.missing_accounts.join(', ')}</span>`;
                        } else {
                            status = `<span style="color: orange;">⚠ 未创建模板</span>`;
                        }
                        message += `<li><b>${company.name}:</b> ${status}</li>`;
                    });
                    message += `</ul>`;
                }

                message += `<h5>诊断信息:</h5>`;
                message += `<ul>`;
                result.diagnosis.forEach(diag => {
                    let color = diag.level === 'error' ? 'red' :
                        diag.level === 'warning' ? 'orange' :
                            diag.level === 'success' ? 'green' : 'blue';
                    message += `<li style="color: ${color};">${diag.message}</li>`;
                });
                message += `</ul>`;

                frappe.msgprint({
                    title: __('税率诊断结果'),
                    message: message,
                    indicator: result.diagnosis.some(d => d.level === 'error') ? 'red' :
                        result.diagnosis.some(d => d.level === 'warning') ? 'orange' : 'green'
                });
            }
        },
        error: function (r) {
            frappe.msgprint({
                title: __('Error'),
                message: __('诊断失败，请检查错误日志。'),
                indicator: 'red'
            });
        }
    });
}

// --- 手动更新税率逻辑 ---
function handle_update_tax(frm) {
    frappe.confirm(__('确定要手动更新此物料的税率模板吗？'), () => {
        frappe.show_alert({ message: __('正在更新，请稍候...'), indicator: 'blue' }, 5);
        frappe.call({
            method: "cos.cos_accounts.controllers.tax.update_single_item_tax",
            args: {
                item_code: frm.doc.name
            },
            callback: function (r) {
                if (r.exc) {
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('更新失败: {0}', [r.exc]),
                        indicator: 'red'
                    });
                } else {
                    frappe.show_alert({
                        message: __('税率模板已更新'),
                        indicator: 'green'
                    });
                    // 刷新表单以显示最新状态
                    frm.reload_doc();
                }
            },
            error: function (r) {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('更新失败，请检查错误日志。'),
                    indicator: 'red'
                });
            }
        });
    });
}

