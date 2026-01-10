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
        
        // 绑定按钮字段的点击事件
        if (frm.fields_dict.custom_sync_from_new_item_request) {
            // 先移除之前的绑定，避免重复绑定
            frm.fields_dict.custom_sync_from_new_item_request.$input.off('click');
            // 绑定新的点击事件
            frm.fields_dict.custom_sync_from_new_item_request.$input.on('click', function() {
                handle_sync_from_new_item_request(frm);
            });
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

// --- 从 New Item Request 同步绑定字段 ---
function handle_sync_from_new_item_request(frm) {
    // 检查是否有关联的 New Item Request
    if (!frm.doc.custom_new_item_request) {
        frappe.msgprint({
            title: __('错误'),
            message: __('此物料未关联到 New Item Request。'),
            indicator: 'red'
        });
        return;
    }
    
    // 确认对话框
    frappe.confirm(
        __('确定要从 New Item Request 同步绑定字段数据吗？<br><br>此操作将只覆盖在 New Item Request 中定义为绑定字段的字段。'),
        function() {
            // 确认后执行同步
                frappe.call({
                    method: 'cos.cos_stock.controllers.new_item_request.get_binding_fields_from_request',
                    args: {
                        item_name: frm.doc.name
                    },
                freeze: true,
                callback: function(r) {
                    if (r.message) {
                        let binding_fields = r.message.binding_fields || {};
                        let fields_count = r.message.fields_count || 0;
                        
                        if (fields_count === 0) {
                            frappe.msgprint({
                                title: __('提示'),
                                message: __('New Item Request 中未定义任何绑定字段。'),
                                indicator: 'blue'
                            });
                            return;
                        }
                        
                        // 显示将要更新的字段列表
                        let fields_list = Object.keys(binding_fields).map(field => {
                            let value = binding_fields[field];
                            // 截断过长的值
                            let display_value = value;
                            if (display_value && display_value.length > 50) {
                                display_value = display_value.substring(0, 50) + '...';
                            }
                            return `<li><b>${field}:</b> ${display_value || '(空)'}</li>`;
                        }).join('');
                        
                        frappe.confirm(
                            __('将更新以下 {0} 个绑定字段：<br><ul>{1}</ul>是否继续？', [fields_count, fields_list]),
                            function() {
                                // 更新字段
                                let updated_count = 0;
                                for (let field_name in binding_fields) {
                                    if (frm.doc[field_name] !== binding_fields[field_name]) {
                                        frm.set_value(field_name, binding_fields[field_name]);
                                        updated_count++;
                                    }
                                }
                                
                                if (updated_count > 0) {
                                    frappe.show_alert({
                                        message: __('已更新 {0} 个字段', [updated_count]),
                                        indicator: 'green'
                                    }, 3);
                                } else {
                                    frappe.show_alert({
                                        message: __('所有字段已是最新值，无需更新'),
                                        indicator: 'blue'
                                    }, 3);
                                }
                            }
                        );
                    }
                },
                error: function(r) {
                    frappe.msgprint({
                        title: __('错误'),
                        message: r.message || __('同步失败，请检查错误日志。'),
                        indicator: 'red'
                    });
                }
            });
        }
    );
}

