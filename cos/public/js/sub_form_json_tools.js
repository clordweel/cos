// 全局子表 JSON 上传下载工具
// 自动为所有带有 allow_bulk_edit 的子表添加 JSON 上传下载功能

frappe.ui.form.on('*', {
    refresh: function (frm) {
        // 延迟执行，确保系统批量按钮已初始化
        setTimeout(function() {
            add_enhanced_bulk_edit_tools_to_all_tables(frm);
        }, 200);
    }
});

// 为所有子表添加增强的批量编辑工具：支持 JSON 格式和粘贴
function add_enhanced_bulk_edit_tools_to_all_tables(frm) {
    // 遍历所有字段，查找 Table 类型的子表
    if (!frm.meta || !frm.meta.fields) return;
    
    frm.meta.fields.forEach(function(field) {
        if (field.fieldtype === 'Table' && field.allow_bulk_edit) {
            // 检查字段是否存在于表单中
            if (frm.fields_dict[field.fieldname] && frm.fields_dict[field.fieldname].grid) {
                add_enhanced_bulk_edit_tools(frm, field.fieldname);
            }
        }
    });
}

// 增强的批量编辑工具：支持 JSON 格式和粘贴（通用版本）
function add_enhanced_bulk_edit_tools(frm, fieldname) {
    let grid = frm.fields_dict[fieldname].grid;
    if (!grid) return;
    
    // 检查字段是否允许批量编辑
    let field_meta = frm.meta.fields.find(f => f.fieldname === fieldname);
    if (!field_meta || !field_meta.allow_bulk_edit) {
        return; // 如果不允许批量编辑，不添加按钮
    }
    
    // 等待系统初始化 .grid-bulk-actions
    let check_and_add = function() {
        let bulk_actions = grid.wrapper.find('.grid-bulk-actions');
        if (bulk_actions.length === 0) {
            // 如果还没有，再等待一下（最多等待 2 秒）
            setTimeout(check_and_add, 100);
            return;
        }
        
        // 检查系统批量按钮是否显示（如果系统按钮隐藏，我们也隐藏）
        let system_buttons = bulk_actions.find('button').not('.enhanced-json-tools button');
        let bulk_actions_visible = bulk_actions.is(':visible') && bulk_actions.css('display') !== 'none';
        
        if (!bulk_actions_visible || system_buttons.length === 0) {
            // 如果批量操作区域不可见或没有系统按钮，移除我们的按钮
            bulk_actions.find('.enhanced-json-tools').remove();
            return;
        }
        
        // 检查是否已经添加了按钮（避免重复添加）
        // 使用 data-fieldname 属性来区分不同字段的按钮
        let existing_tools = bulk_actions.find(`.enhanced-json-tools[data-fieldname="${fieldname}"]`);
        if (existing_tools.length > 0) {
            // 如果已存在，确保它显示（跟随系统按钮）
            existing_tools.show();
            return;
        }
        
        // 创建工具容器，添加 data-fieldname 属性用于标识
        let tools_container = $(`<span class="enhanced-json-tools" data-fieldname="${fieldname}" style="margin-left: 10px;"></span>`);
        
        // 下载 JSON 按钮（支持粘贴）
        let download_json_btn = $(`
            <button class="btn btn-sm btn-secondary" type="button" title="${__('下载 JSON 或复制 JSON 数据')}">
                <i class="fa fa-download"></i> ${__('Download JSON')}
            </button>
        `).on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            show_download_dialog(frm, fieldname);
        });
        
        // 上传 JSON 按钮（支持粘贴）
        let upload_json_btn = $(`
            <button class="btn btn-sm btn-secondary" type="button" title="${__('上传 JSON 文件或粘贴 JSON 数据')}">
                <i class="fa fa-upload"></i> ${__('Upload JSON')}
            </button>
        `).on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            show_upload_dialog(frm, fieldname);
        });
        
        tools_container.append(download_json_btn, upload_json_btn);
        bulk_actions.append(tools_container);
        
        // 监听系统按钮的显示/隐藏变化
        observe_bulk_actions_visibility(bulk_actions, tools_container);
    };
    
    setTimeout(check_and_add, 100);
}

// 监听系统批量按钮的显示/隐藏，同步我们的按钮
function observe_bulk_actions_visibility(bulk_actions, our_tools) {
    // 使用 MutationObserver 监听系统按钮的显示/隐藏
    let observer = new MutationObserver(function(mutations) {
        let bulk_actions_visible = bulk_actions.is(':visible') && bulk_actions.css('display') !== 'none';
        let system_buttons = bulk_actions.find('button').not('.enhanced-json-tools button');
        
        if (bulk_actions_visible && system_buttons.length > 0) {
            our_tools.show();
        } else {
            our_tools.hide();
        }
    });
    
    // 观察 bulk_actions 容器的变化
    if (bulk_actions.length > 0) {
        observer.observe(bulk_actions[0], {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
        
        // 也观察父容器的变化
        let parent = bulk_actions.parent();
        if (parent.length > 0) {
            observer.observe(parent[0], {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class']
            });
        }
    }
    
    // 定期检查（作为备用方案）
    let check_interval = setInterval(function() {
        let bulk_actions_visible = bulk_actions.is(':visible') && bulk_actions.css('display') !== 'none';
        let system_buttons = bulk_actions.find('button').not('.enhanced-json-tools button');
        
        if (bulk_actions_visible && system_buttons.length > 0) {
            our_tools.show();
        } else {
            our_tools.hide();
        }
    }, 500);
    
    // 当工具被移除时清除定时器
    our_tools.on('remove', function() {
        clearInterval(check_interval);
        observer.disconnect();
    });
}

// 显示下载对话框（支持下载和粘贴）
function show_download_dialog(frm, fieldname) {
    let data = frm.doc[fieldname] || [];
    
    if (data.length === 0) {
        frappe.msgprint(__('表格为空，无法下载'));
        return;
    }
    
    // 转换为纯对象数组（移除 Frappe 内部属性）
    let json_data = data.map(function(row) {
        let clean_row = {};
        let meta = frappe.get_meta(frm.fields_dict[fieldname].grid.doctype);
        meta.fields.forEach(function(field) {
            if (field.fieldname && row[field.fieldname] !== undefined) {
                clean_row[field.fieldname] = row[field.fieldname];
            }
        });
        return clean_row;
    });
    
    let json_str = JSON.stringify(json_data, null, 2);
    
    let dialog = new frappe.ui.Dialog({
        title: __('下载 JSON 数据'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'download_info',
                options: `<div style="margin-bottom: 10px;">
                    <p>${__('共 {0} 条记录', [data.length])}</p>
                </div>`
            },
            {
                fieldtype: 'Code',
                fieldname: 'json_content',
                label: __('JSON 数据'),
                default: json_str,
                options: {
                    language: 'json',
                    read_only: 1
                }
            },
            {
                fieldtype: 'HTML',
                fieldname: 'help_text',
                options: `
                    <div style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                        <strong>${__('提示')}:</strong><br>
                        ${__('您可以复制上面的 JSON 数据，或点击"下载文件"按钮保存为文件。')}
                    </div>
                `
            }
        ],
        primary_action_label: __('下载文件'),
        primary_action: function() {
            let blob = new Blob([json_str], { type: 'application/json' });
            let url = URL.createObjectURL(blob);
            let a = document.createElement('a');
            a.href = url;
            a.download = `${frm.doc.name || 'template'}_${fieldname}.json`;
            a.click();
            URL.revokeObjectURL(url);
            
            frappe.show_alert({
                message: __('JSON 文件已下载'),
                indicator: 'green'
            }, 3);
            
            dialog.hide();
        }
    });
    
    dialog.show();
}

// 显示上传对话框（支持上传和粘贴）
function show_upload_dialog(frm, fieldname) {
    let json_data_to_import = null;
    
    let dialog = new frappe.ui.Dialog({
        title: __('上传 JSON 数据'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'input_method',
                label: __('输入方式'),
                options: '上传文件\n粘贴数据',
                default: '粘贴数据',
                reqd: 1,
                change: function() {
                    let method = dialog.get_value('input_method');
                    if (method === '上传文件') {
                        dialog.set_df_property('json_content', 'hidden', 1);
                        dialog.set_df_property('file_input_html', 'hidden', 0);
                    } else {
                        dialog.set_df_property('json_content', 'hidden', 0);
                        dialog.set_df_property('file_input_html', 'hidden', 1);
                    }
                }
            },
            {
                fieldtype: 'HTML',
                fieldname: 'file_input_html',
                label: __('选择 JSON 文件'),
                hidden: 1,
                options: `
                    <div style="margin: 10px 0;">
                        <input type="file" accept=".json,application/json" id="json_file_input" style="width: 100%; padding: 5px;">
                    </div>
                `
            },
            {
                fieldtype: 'Code',
                fieldname: 'json_content',
                label: __('粘贴 JSON 数据'),
                reqd: 1,
                options: {
                    language: 'json'
                }
            },
            {
                fieldtype: 'HTML',
                fieldname: 'help_text',
                options: `
                    <div style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                        <strong>${__('提示')}:</strong><br>
                        ${__('JSON 格式')}: ${__('直接粘贴 JSON 数组，例如: [{"field1": "value1", "field2": "value2"}]')}<br>
                        ${__('上传文件')}: ${__('选择 JSON 文件后，内容会自动填充到粘贴框中，您可以编辑后再导入')}<br>
                        ${__('合并更新')}: ${__('合并更新会根据 parameter_name 字段匹配现有记录，匹配到则更新，否则添加为新记录')}
                    </div>
                `
            }
        ],
        primary_action_label: __('导入'),
        primary_action: function(values) {
            let json_data;
            
            try {
                // 优先使用从文件读取的数据
                if (json_data_to_import) {
                    json_data = json_data_to_import;
                } else {
                    // 尝试从粘贴框获取数据（即使字段被隐藏，也应该能获取值）
                    let json_content = values.json_content || dialog.get_value('json_content');
                    if (!json_content) {
                        frappe.msgprint({
                            title: __('错误'),
                            message: __('请先上传文件或粘贴 JSON 数据'),
                            indicator: 'red'
                        });
                        return;
                    }
                    json_data = JSON.parse(json_content);
                }
                
                import_table_data(frm, fieldname, json_data, 'json', false);
                dialog.hide();
            } catch (error) {
                frappe.msgprint({
                    title: __('错误'),
                    message: __('数据格式错误: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        },
        secondary_action_label: __('合并更新'),
        secondary_action: function(values) {
            let json_data;
            
            try {
                // 优先使用从文件读取的数据
                if (json_data_to_import) {
                    json_data = json_data_to_import;
                } else {
                    // 尝试从粘贴框获取数据（即使字段被隐藏，也应该能获取值）
                    let json_content = values.json_content || dialog.get_value('json_content');
                    if (!json_content) {
                        frappe.msgprint({
                            title: __('错误'),
                            message: __('请先上传文件或粘贴 JSON 数据'),
                            indicator: 'red'
                        });
                        return;
                    }
                    json_data = JSON.parse(json_content);
                }
                
                // 显示字段选择对话框
                show_match_field_dialog(frm, fieldname, json_data);
                dialog.hide();
            } catch (error) {
                frappe.msgprint({
                    title: __('错误'),
                    message: __('数据格式错误: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        }
    });
    
    dialog.show();
    
    // 处理文件上传
    setTimeout(function() {
        let file_input = dialog.$wrapper.find('#json_file_input');
        if (file_input.length) {
            file_input.on('change', function(e) {
                let file = e.target.files[0];
                if (!file) return;
                
                let reader = new FileReader();
                reader.onload = function(event) {
                    try {
                        json_data_to_import = JSON.parse(event.target.result);
                        // 将内容填充到粘贴框
                        dialog.set_value('json_content', JSON.stringify(json_data_to_import, null, 2));
                        // 切换到粘贴数据模式以便用户编辑
                        dialog.set_value('input_method', '粘贴数据');
                        dialog.set_df_property('json_content', 'hidden', 0);
                        dialog.set_df_property('file_input_html', 'hidden', 1);
                        
                        frappe.show_alert({
                            message: __('文件已加载，您可以编辑后点击导入'),
                            indicator: 'blue'
                        }, 3);
                    } catch (error) {
                        frappe.msgprint({
                            title: __('错误'),
                            message: __('JSON 文件格式错误: {0}', [error.message]),
                            indicator: 'red'
                        });
                        json_data_to_import = null;
                    }
                };
                reader.readAsText(file);
            });
        }
    }, 100);
}

// 显示匹配字段选择对话框（合并更新时使用）
function show_match_field_dialog(frm, fieldname, data) {
    let meta = frappe.get_meta(frm.fields_dict[fieldname].grid.doctype);
    
    // 获取所有可用字段（排除系统字段和只读字段）
    let available_fields = [];
    meta.fields.forEach(function(field) {
        // 排除系统字段、只读字段、按钮等
        if (field.fieldname && 
            field.fieldtype !== 'Section Break' && 
            field.fieldtype !== 'Column Break' &&
            field.fieldtype !== 'Tab Break' &&
            field.fieldtype !== 'HTML' &&
            field.fieldtype !== 'Button' &&
            !field.read_only &&
            field.fieldname !== 'idx' &&
            field.fieldname !== 'parent' &&
            field.fieldname !== 'parenttype' &&
            field.fieldname !== 'parentfield') {
            let label = field.label || field.fieldname;
            available_fields.push({
                fieldname: field.fieldname,
                label: label
            });
        }
    });
    
    if (available_fields.length === 0) {
        frappe.msgprint({
            title: __('错误'),
            message: __('没有可用的匹配字段'),
            indicator: 'red'
        });
        return;
    }
    
    // 构建字段选项（只使用字段名）
    let field_options = available_fields.map(function(f) {
        return f.fieldname;
    }).join('\n');
    
    // 默认选择第一个字段
    let default_field = available_fields[0].fieldname;
    
    let match_dialog = new frappe.ui.Dialog({
        title: __('选择匹配字段'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'match_field',
                label: __('标识符字段'),
                options: field_options,
                default: default_field,
                reqd: 1,
                description: __('选择用于匹配现有记录的字段，匹配到的记录将被更新，未匹配到的将添加为新记录')
            },
            {
                fieldtype: 'HTML',
                fieldname: 'info',
                options: `
                    <div style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                        <strong>${__('提示')}:</strong><br>
                        ${__('将合并更新 {0} 条记录', [data.length])}<br>
                        ${__('请选择用于匹配的唯一标识字段')}
                    </div>
                `
            }
        ],
        primary_action_label: __('确认'),
        primary_action: function(values) {
            let match_field = values.match_field;
            match_dialog.hide();
            import_table_data(frm, fieldname, data, 'json', true, match_field);
        }
    });
    
    match_dialog.show();
}

// 导入表格数据
function import_table_data(frm, fieldname, data, format, is_merge_mode, match_field) {
    if (!Array.isArray(data) || data.length === 0) {
        frappe.msgprint(__('数据为空或格式不正确'));
        return;
    }
    
    let meta = frappe.get_meta(frm.fields_dict[fieldname].grid.doctype);
    let field_map = {};
    
    // 构建字段映射（支持中英文）
    meta.fields.forEach(function(field) {
        if (field.fieldname) {
            field_map[field.fieldname] = field.fieldname;
            if (field.label) {
                field_map[field.label] = field.fieldname;
            }
        }
    });
    
    // 如果是合并模式，需要验证匹配字段
    if (is_merge_mode) {
        // 如果没有指定匹配字段，使用默认逻辑
        if (!match_field) {
            // 合并模式：优先使用 parameter_name，否则使用 name
            match_field = meta.fields.find(f => f.fieldname === 'parameter_name') ? 'parameter_name' : 'name';
        }
        
        // 验证匹配字段是否存在
        if (!meta.fields.find(f => f.fieldname === match_field)) {
            frappe.msgprint({
                title: __('错误'),
                message: __('匹配字段 {0} 不存在', [match_field]),
                indicator: 'red'
            });
            return;
        }
    }
    
    let confirm_message = is_merge_mode 
        ? __('将合并更新 {0} 条记录（根据 {1} 字段匹配），是否继续？', [data.length, match_field])
        : __('将导入 {0} 条记录（将替换现有数据），是否继续？', [data.length]);
    
    frappe.confirm(
        confirm_message,
        function() {
            let existing_data = frm.doc[fieldname] || [];
            let existing_map = {};
            let updated_count = 0;
            let added_count = 0;
            
            // 如果是合并模式，构建现有数据的映射（使用 parameter_name 或 name 字段作为唯一标识）
            if (is_merge_mode && existing_data.length > 0) {
                existing_data.forEach(function(row) {
                    let match_value = row[match_field];
                    if (match_value) {
                        existing_map[match_value] = row;
                    }
                });
            } else {
                // 替换模式：清空现有数据
                frm.clear_table(fieldname);
            }
            
            // 处理每条导入的数据
            data.forEach(function(row_data) {
                let target_row = null;
                let is_update = false;
                
                // 合并模式：尝试匹配现有记录
                if (is_merge_mode) {
                    // 尝试通过匹配字段匹配
                    let match_value = row_data[match_field] || row_data[field_map[match_field]];
                    if (match_value && existing_map[match_value]) {
                        target_row = existing_map[match_value];
                        is_update = true;
                        updated_count++;
                    }
                }
                
                // 如果没有匹配到现有记录，创建新记录
                if (!target_row) {
                    target_row = frm.add_child(fieldname);
                    added_count++;
                }
                
                // 映射字段并设置值
                Object.keys(row_data).forEach(function(key) {
                    let fieldname_mapped = field_map[key] || key;
                    if (meta.fields.find(f => f.fieldname === fieldname_mapped)) {
                        let value = row_data[key];
                        // 处理空值
                        if (value === '' || value === null || value === undefined) {
                            value = null;
                        }
                        // 如果是更新模式且字段是 name，跳过（name 是系统字段，不应更新）
                        if (is_update && fieldname_mapped === 'name') {
                            return;
                        }
                        target_row[fieldname_mapped] = value;
                    }
                });
                
                // 数据清理：根据 constraint_type 清理不相关的字段
                if (target_row.constraint_type !== 'Doctype') {
                    // 如果不是 Doctype 类型，清空 doctype_selector 和 value_doctype
                    if (target_row.doctype_selector) {
                        target_row.doctype_selector = null;
                    }
                    if (target_row.value_doctype) {
                        target_row.value_doctype = null;
                    }
                } else {
                    // 如果是 Doctype 类型，验证 doctype_selector 是否设置
                    if (target_row.value_doctype && !target_row.doctype_selector) {
                        // 如果 value_doctype 有值但 doctype_selector 未设置，清空 value_doctype
                        target_row.value_doctype = null;
                    }
                }
                
                // 清理其他类型不相关的字段
                if (target_row.constraint_type !== 'Float' && target_row.value_float) {
                    target_row.value_float = null;
                }
                if (target_row.constraint_type !== 'Integer' && target_row.value_integer) {
                    target_row.value_integer = null;
                }
                if (target_row.constraint_type !== 'Format' && target_row.value_format) {
                    target_row.value_format = null;
                }
            });
            
            frm.refresh_field(fieldname);
            
            // 显示导入结果
            let result_message;
            if (is_merge_mode) {
                result_message = __('合并更新完成：更新 {0} 条，新增 {1} 条', [updated_count, added_count]);
            } else {
                result_message = __('已导入 {0} 条记录', [data.length]);
            }
            
            frappe.show_alert({
                message: result_message,
                indicator: 'green'
            }, 3);
        }
    );
}
