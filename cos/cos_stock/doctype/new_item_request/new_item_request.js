// Copyright (c) 2025, BIoT and contributors

const trigger_preview_calculation = frappe.utils.debounce((frm) => {
    let context_data = {};
    let has_format = false;

    // 收集所有当前值作为 Jinja 渲染的初始变量
    (frm.doc.parameters || []).forEach(row => {
        let val = row.parameter_value;
        if (row.constraint_type === 'Integer' || row.constraint_type === 'Float') {
            val = flt(val);
        }
        if (row.parameter_name) {
            context_data[row.parameter_name] = val;
        }
        if (row.constraint_type === 'Format') {
            has_format = true;
        }
    });

    if (!has_format) return;

    frm.call({
        doc: frm.doc,
        method: 'preview_parameters',
        args: {
            parameters: frm.doc.parameters,
            context: context_data
        },
        callback: (r) => {
            if (r.message) {
                frm._is_system_updating = true;
                let has_changes = false;

                $.each(frm.doc.parameters, function (i, row) {
                    if (r.message[row.name] !== undefined && row.parameter_value !== r.message[row.name]) {
                        frappe.model.set_value(row.doctype, row.name, 'parameter_value', r.message[row.name]);
                        has_changes = true;
                    }
                });

                frm._is_system_updating = false;
                if (has_changes) {
                    frm.refresh_field('parameters');
                }
            }
        }
    });
}, 500);

frappe.ui.form.on('New Item Request', {
    refresh(frm) {
        frm._is_system_updating = false;
        if (!frm.is_new()) {
            frm.add_custom_button(__('Check Parameter Duplicates'), () => run_duplicate_check(frm));
        }

        // 草稿模式下，仅 Administrator 用户可见的创建物料按钮
        if (frm.doc.docstatus === 0 && frappe.user.name === 'Administrator') {
            frappe.db.get_value('Item', { 'custom_new_item_request': frm.doc.name }, 'name', (r) => {
                if (r && r.name) {
                    frm.add_custom_button(__('View Created Item'), () => frappe.set_route('Form', 'Item', r.name));
                } else {
                    frm.add_custom_button(__('Create Item (Draft)'), function () {
                            frappe.confirm(
                            __('您正在草稿模式下创建物料。此操作仅限管理员使用。是否继续？'),
                            function() {
                                frm.call({
                                    doc: frm.doc,
                                    method: 'generate_item_data_dict',
                                    freeze: true,
                                    callback(res) {
                                        if (res.message) {
                                            let new_item = frappe.model.get_new_doc('Item');
                                            $.extend(new_item, res.message);
                                            new_item.custom_new_item_request = frm.doc.name;
                                            frappe.set_route('Form', 'Item', new_item.name);
                                        }
                                    }
                                });
                            }
                        );
                    });
                }
            });
        }

        if (frm.doc.docstatus === 1) {
            frappe.db.get_value('Item', { 'custom_new_item_request': frm.doc.name }, 'name', (r) => {
                if (r && r.name) {
                    frm.add_custom_button(__('View Created Item'), () => frappe.set_route('Form', 'Item', r.name));
                } else {
                    frm.add_custom_button(__('Create Item (Review)'), function () {
                        run_duplicate_check(frm, function () {
                            frm.call({
                                doc: frm.doc,
                                method: 'generate_item_data_dict',
                                freeze: true,
                                callback(res) {
                                    if (res.message) {
                                        let new_item = frappe.model.get_new_doc('Item');
                                        $.extend(new_item, res.message);
                                        new_item.custom_new_item_request = frm.doc.name;
                                        frappe.set_route('Form', 'Item', new_item.name);
                                    }
                                }
                            });
                        });
                    });
                }
            });
        }
        
        // 监听参数表的行删除事件，触发预览计算更新
        // 延迟执行，确保 grid 已完全初始化
        setTimeout(() => {
            setup_parameter_delete_listener(frm);
        }, 500);
    },
    
    parameters: function(frm) {
        // 当参数表发生变化时（包括删除行），触发预览计算
        // 使用 debounce 避免频繁触发
        if (!frm._is_system_updating) {
            // 清除之前的定时器
            if (frm._parameter_change_timeout) {
                clearTimeout(frm._parameter_change_timeout);
            }
            frm._parameter_change_timeout = setTimeout(() => {
                frm._parameter_change_timeout = null;
                trigger_preview_calculation(frm);
            }, 300);
        }
    },

    validate(frm) {
        // 提交时验证所有参数
        let validation_errors = [];
        
        (frm.doc.parameters || []).forEach(row => {
            if (row.constraint_type === 'Data' && row.allowed_data) {
                let validation_result = validate_allowed_data(row.parameter_value, row.allowed_data);
                if (!validation_result.valid) {
                    validation_errors.push({
                        parameter_name: row.parameter_name || __('未命名参数'),
                        message: validation_result.message
                    });
                }
            }
        });
        
        if (validation_errors.length > 0) {
            let error_messages = validation_errors.map(err => 
                __('参数 "{0}": {1}', [err.parameter_name, err.message])
            ).join('<br>');
            
            frappe.throw({
                title: __('验证失败'),
                message: error_messages,
                indicator: 'red'
            });
        }
    },

    template(frm) {
        if (!frm.doc.template) {
            frm.clear_table('parameters');
            frm.clear_table('uoms');
            frm.refresh_field('parameters');
            return;
        }
        frappe.call({
            method: 'frappe.client.get',
            args: { doctype: 'Item Parameter Template', name: frm.doc.template },
            freeze: true,
            callback(r) {
                if (!r.message) return;
                frm._is_system_updating = true;
                frm.clear_table('parameters');
                (r.message.parameters || []).forEach(row => {
                    let new_row = frm.add_child('parameters');
                    Object.assign(new_row, {
                        from_template: 1,
                        parameter_name: row.parameter_name,
                        description: row.description,
                        constraint_type: row.constraint_type,
                        readonly_value: row.readonly_value,
                        join_to_hash: row.join_to_hash,
                        binding_field: row.binding_field,
                        target_field: row.target_field,
                        doctype_selector: row.doctype_selector,
                        value_format: row.value_format,
                        value_float: row.value_float,
                        value_integer: row.value_integer,
                        value_doctype: row.value_doctype,
                        parameter_value: row.parameter_default_value,
                        allowed_data: row.allowed_data
                    });
                });
                frm.clear_table('uoms');
                (r.message.uoms || []).forEach(row => {
                    let u = frm.add_child('uoms');
                    u.uom = row.uom;
                    u.conversion_factor = row.conversion_factor;
                });
                if (r.message.item_group) frm.set_value('item_group', r.message.item_group);
                frm.refresh_field('parameters');
                frm.refresh_field('uoms');
                frm._is_system_updating = false;
                trigger_preview_calculation(frm);
            }
        });
    }
});

frappe.ui.form.on('Item Parameter Definition', {
    value_float: (frm, cdt, cdn) => sync_value(frm, cdt, cdn, 'value_float'),
    value_integer: (frm, cdt, cdn) => sync_value(frm, cdt, cdn, 'value_integer'),
    value_doctype: (frm, cdt, cdn) => sync_value(frm, cdt, cdn, 'value_doctype'),
    value_format: (frm, cdt, cdn) => sync_value(frm, cdt, cdn, 'value_format'),
    parameter_value: (frm, cdt, cdn) => {
        if (frm._is_system_updating) return;
        
        // 验证 allowed_data 约束（输入时验证）
        let row = locals[cdt][cdn];
        if (row.constraint_type === 'Data' && row.allowed_data) {
            let validation_result = validate_allowed_data(row.parameter_value, row.allowed_data);
            
            // 清除之前的错误提示
            clear_field_error(frm, cdt, cdn, 'parameter_value');
            
            if (!validation_result.valid) {
                // 显示 toast 提示（不干扰交互）
                frappe.show_alert({
                    message: validation_result.message,
                    indicator: 'orange'
                }, 3);
                
                // 设置字段错误提示
                set_field_error(frm, cdt, cdn, 'parameter_value', validation_result.message);
                return;
            }
        } else {
            // 如果不需要验证，清除错误提示
            clear_field_error(frm, cdt, cdn, 'parameter_value');
        }
        
        trigger_preview_calculation(frm);
    }
});

function sync_value(frm, cdt, cdn, field) {
    if (frm._is_system_updating) return;
    let row = locals[cdt][cdn];
    frm._is_system_updating = true;
    frappe.model.set_value(cdt, cdn, 'parameter_value', row[field]);
    frm._is_system_updating = false;
    trigger_preview_calculation(frm);
}

/**
 * 验证 allowed_data 约束
 * @param {string} value - 要验证的值
 * @param {string} allowed_data - 允许的数据规则
 * @returns {Object} {valid: boolean, message: string}
 */
function validate_allowed_data(value, allowed_data) {
    // 空值不做任何限制
    if (!allowed_data || allowed_data.trim() === '') {
        return { valid: true, message: '' };
    }
    
    let trimmed_allowed = allowed_data.trim();
    
    // 情况1: 选项模式 [Option1, Option2, Other]
    if (trimmed_allowed.startsWith('[') && trimmed_allowed.endsWith(']')) {
        try {
            // 移除方括号并解析选项
            let options_str = trimmed_allowed.slice(1, -1);
            let options = options_str.split(',').map(opt => opt.trim());
            
            // 如果值为空，也允许（允许用户清空字段）
            if (!value || value.trim() === '') {
                return { valid: true, message: '' };
            }
            
            if (options.includes(value)) {
                return { valid: true, message: '' };
            } else {
                return {
                    valid: false,
                    message: __('不在允许的选项中。允许的选项: {0}', [options.join(', ')])
                };
            }
        } catch (e) {
            return {
                valid: false,
                message: __('选项格式解析错误: {0}', [e.message])
            };
        }
    }
    
    // 情况2: 正则表达式模式 /x._+\d\W/
    if (trimmed_allowed.startsWith('/') && trimmed_allowed.endsWith('/')) {
        try {
            // 移除首尾的斜杠，提取正则表达式
            let regex_str = trimmed_allowed.slice(1, -1);
            let regex = new RegExp('^' + regex_str + '$');
            
            // 如果值为空，也允许（允许用户清空字段）
            if (!value || value.trim() === '') {
                return { valid: true, message: '' };
            }
            
            if (regex.test(value)) {
                return { valid: true, message: '' };
            } else {
                return {
                    valid: false,
                    message: __('不符合允许的格式规则: /{0}/', [regex_str])
                };
            }
        } catch (e) {
            return {
                valid: false,
                message: __('正则表达式格式错误: {0}', [e.message])
            };
        }
    }
    
    // 如果格式不匹配任何已知模式，返回验证通过（向后兼容）
    return { valid: true, message: '' };
}

/**
 * 设置字段错误提示
 * @param {Object} frm - 表单对象
 * @param {string} cdt - 子表类型
 * @param {string} cdn - 子表行名称
 * @param {string} fieldname - 字段名
 * @param {string} message - 错误消息
 */
function set_field_error(frm, cdt, cdn, fieldname, message) {
    // 使用 setTimeout 确保 DOM 已更新
    setTimeout(() => {
        let grid = frm.fields_dict.parameters?.grid;
        if (!grid) return;
        
        // 安全地获取行索引
        let row_idx = -1;
        if (typeof grid.get_row_index === 'function') {
            row_idx = grid.get_row_index(cdn);
        } else if (grid.grid_rows) {
            // 备用方法：遍历查找
            for (let i = 0; i < grid.grid_rows.length; i++) {
                if (grid.grid_rows[i] && grid.grid_rows[i].doc && grid.grid_rows[i].doc.name === cdn) {
                    row_idx = i;
                    break;
                }
            }
        }
        
        if (row_idx === -1) {
            // 如果找不到行，尝试直接通过 DOM 查找
            let row_wrapper = grid.wrapper.find(`[data-name="${cdn}"]`);
            if (row_wrapper.length) {
                let input = row_wrapper.find(`[data-fieldname="${fieldname}"] input`);
                if (input && input.length) {
                    input.addClass('error');
                    input.attr('title', message);
                }
            }
            return;
        }
        
        let grid_row = grid.grid_rows[row_idx];
        if (!grid_row) return;
        
        // 尝试多种方式设置错误提示
        let field = grid_row.grid_form?.fields_dict?.[fieldname];
        if (field && typeof field.set_error === 'function') {
            field.set_error(message);
        } else {
            // 备用方案：直接在输入框上设置错误样式
            let input = grid_row.$wrapper?.find(`[data-fieldname="${fieldname}"] input`);
            if (input && input.length) {
                input.addClass('error');
                input.attr('title', message);
            }
        }
    }, 100);
}

/**
 * 清除字段错误提示
 * @param {Object} frm - 表单对象
 * @param {string} cdt - 子表类型
 * @param {string} cdn - 子表行名称
 * @param {string} fieldname - 字段名
 */
function clear_field_error(frm, cdt, cdn, fieldname) {
    setTimeout(() => {
        let grid = frm.fields_dict.parameters?.grid;
        if (!grid) return;
        
        // 安全地获取行索引
        let row_idx = -1;
        if (typeof grid.get_row_index === 'function') {
            row_idx = grid.get_row_index(cdn);
        } else if (grid.grid_rows) {
            // 备用方法：遍历查找
            for (let i = 0; i < grid.grid_rows.length; i++) {
                if (grid.grid_rows[i] && grid.grid_rows[i].doc && grid.grid_rows[i].doc.name === cdn) {
                    row_idx = i;
                    break;
                }
            }
        }
        
        if (row_idx === -1) {
            // 如果找不到行，尝试直接通过 DOM 查找
            let row_wrapper = grid.wrapper.find(`[data-name="${cdn}"]`);
            if (row_wrapper.length) {
                let input = row_wrapper.find(`[data-fieldname="${fieldname}"] input`);
                if (input && input.length) {
                    input.removeClass('error');
                    input.removeAttr('title');
                }
            }
            return;
        }
        
        let grid_row = grid.grid_rows[row_idx];
        if (!grid_row) return;
        
        // 尝试多种方式清除错误提示
        let field = grid_row.grid_form?.fields_dict?.[fieldname];
        if (field && typeof field.set_error === 'function') {
            field.set_error('');
        } else {
            // 备用方案：清除输入框上的错误样式
            let input = grid_row.$wrapper?.find(`[data-fieldname="${fieldname}"] input`);
            if (input && input.length) {
                input.removeClass('error');
                input.removeAttr('title');
            }
        }
    }, 100);
}

// 设置参数删除监听器
function setup_parameter_delete_listener(frm) {
    if (!frm.fields_dict.parameters || !frm.fields_dict.parameters.grid) {
        return;
    }
    
    let grid = frm.fields_dict.parameters.grid;
    
    // 清除之前的定时器
    if (frm._parameter_delete_check_interval) {
        clearInterval(frm._parameter_delete_check_interval);
    }
    
    let last_row_count = (frm.doc.parameters || []).length;
    
    // 方法1: 直接在 grid wrapper 上监听删除按钮点击（使用事件委托）
    grid.wrapper.on('click', '.grid-delete-row', function(e) {
        // 记录删除前的行数
        let before_count = (frm.doc.parameters || []).length;
        // 延迟检查，确保删除操作完成
        setTimeout(() => {
            let after_count = (frm.doc.parameters || []).length;
            if (after_count < before_count && !frm._is_system_updating) {
                console.log('检测到删除行，触发预览计算', { before: before_count, after: after_count });
                trigger_preview_calculation(frm);
            }
        }, 500);
    });
    
    // 方法2: 定期检查行数变化（作为备用方案，确保不会遗漏）
    frm._parameter_delete_check_interval = setInterval(function() {
        let current_row_count = (frm.doc.parameters || []).length;
        if (current_row_count < last_row_count && !frm._is_system_updating) {
            // 行数减少，说明有行被删除
            console.log('定期检查发现行数减少，触发预览计算', { before: last_row_count, after: current_row_count });
            setTimeout(() => {
                trigger_preview_calculation(frm);
            }, 200);
        }
        last_row_count = current_row_count;
    }, 400);
}

function run_duplicate_check(frm, callback) {
    // 使用控制器方法调用，避免文档状态检查（允许对已取消的文档进行检查）
    frappe.call({
        method: 'cos.cos_stock.controllers.new_item_request.check_duplicate_request',
        args: {
            unique_code: frm.doc.unique_code,
            current_docname: frm.doc.name
        },
        callback(r) {
            if (r.message && r.message.duplicate) {
                frappe.throw({ title: __('发现重复'), message: r.message.message, indicator: 'red' });
            } else {
                frappe.show_alert({ message: r.message.message, indicator: 'green' });
                if (callback) callback();
            }
        }
    });
}