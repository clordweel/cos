// 为富文本编辑器添加源码切换按钮
$(document).on('app_ready', () => {
    add_source_toggle_to_text_editors();
});

// 为所有 Text Editor 字段添加源码切换按钮
const add_source_toggle_to_text_editors = () => {
    // 监听表单刷新事件，确保动态加载的字段也能添加按钮
    frappe.ui.form.on('*', {
        refresh: function(frm) {
            // 延迟执行，确保编辑器已完全初始化
            setTimeout(() => {
                add_toggle_buttons_to_form(frm);
            }, 500);
        }
    });

    // 为当前已存在的表单添加按钮
    if (typeof cur_frm !== 'undefined' && cur_frm) {
        setTimeout(() => {
            add_toggle_buttons_to_form(cur_frm);
        }, 500);
    }

    // 监听 DOM 变化，为动态添加的字段添加按钮（包括对话框中的字段）
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) { // Element node
                    const $node = $(node);
                    // 检查是否是 Text Editor 字段
                    const textEditor = $node.is('[data-fieldtype="Text Editor"]') ? 
                        $node : $node.find('[data-fieldtype="Text Editor"]');
                    
                    if (textEditor.length > 0) {
                        setTimeout(() => {
                            // 尝试从表单中获取，如果不在表单中，直接处理字段
                            const frm = typeof cur_frm !== 'undefined' ? cur_frm : null;
                            if (frm) {
                                add_toggle_buttons_to_form(frm);
                            } else {
                                // 处理不在表单中的字段（如对话框）
                                add_toggle_button_to_field(textEditor);
                            }
                        }, 300);
                    }
                }
            });
        });
    });

    // 开始观察 body 的变化
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
};

// 为表单中的所有 Text Editor 字段添加切换按钮
const add_toggle_buttons_to_form = (frm) => {
    if (!frm) return;

    // 尝试多种方式获取表单容器
    let $formWrapper = null;
    
    // 方法1: 尝试 frm.wrapper（可能是 DOM 元素或 jQuery 对象）
    if (frm.wrapper) {
        if (typeof frm.wrapper.find === 'function') {
            // 已经是 jQuery 对象
            $formWrapper = frm.wrapper;
        } else if (frm.wrapper.nodeType || frm.wrapper.jquery) {
            // 是 DOM 元素或 jQuery 对象
            $formWrapper = $(frm.wrapper);
        }
    }
    
    // 方法2: 尝试 frm.$wrapper
    if ((!$formWrapper || $formWrapper.length === 0) && frm.$wrapper) {
        $formWrapper = frm.$wrapper;
    }
    
    // 方法3: 如果都找不到，使用当前活动的表单区域
    if (!$formWrapper || $formWrapper.length === 0) {
        // 查找当前活动的表单容器
        $formWrapper = $('.form-page:visible, .form-container:visible, .layout-main:visible').first();
        if ($formWrapper.length === 0) {
            // 最后回退到整个可见区域
            $formWrapper = $('.page-content:visible, body').first();
        }
    }

    // 查找所有 Text Editor 字段
    $formWrapper.find('[data-fieldtype="Text Editor"]').each(function() {
        const $field = $(this);
        add_toggle_button_to_field($field, frm);
    });
};

// 为单个 Text Editor 字段添加切换按钮
const add_toggle_button_to_field = ($field, frm = null) => {
    const fieldname = $field.attr('data-fieldname');
    
    if (!fieldname) return;

    // 检查是否已经添加了按钮（避免重复添加）
    if ($field.find('.ql-source').length > 0) {
        return;
    }

    // 查找编辑器容器和工具栏
    const $editorContainer = $field.find('.ql-container');
    const $editor = $field.find('.ql-editor');
    const $toolbar = $field.find('.ql-toolbar');
    
    // 如果找不到 Quill 编辑器或工具栏，可能不是 Text Editor 字段或还未初始化
    if ($editorContainer.length === 0 || $editor.length === 0 || $toolbar.length === 0) {
        return;
    }

    // 创建新的 ql-formats 容器
    const $formats = $('<span class="ql-formats"></span>');
    
    // 创建源码切换按钮，使用与 Quill 工具栏按钮相同的样式
    const $toggleBtn = $('<button type="button" class="ql-source" aria-pressed="false" aria-label="HTML 源码" title="显示/隐藏 HTML 源码编辑器">')
        .html('<svg viewBox="0 0 18 18"><polyline class="ql-stroke" points="5 7 3 9 5 11"></polyline><polyline class="ql-stroke" points="13 7 15 9 13 11"></polyline><line class="ql-stroke" x1="10" x2="8" y1="5" y2="13"></line></svg>')
        .on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggle_html_editor($field, fieldname, frm);
        });

    $formats.append($toggleBtn);
    
    // 将按钮添加到工具栏末尾
    $toolbar.append($formats);
    
    // 保存工具栏和编辑器容器的引用，用于后续添加 HTML 编辑器
    if (!$field.data('toolbar')) {
        $field.data('toolbar', $toolbar);
    }
    if (!$field.data('editor-container')) {
        $field.data('editor-container', $editorContainer);
    }
};

// 切换 HTML 编辑器显示/隐藏
const toggle_html_editor = ($field, fieldname, frm) => {
    const $toggleBtn = $field.find('.ql-source');
    const $toolbar = $field.data('toolbar') || $field.find('.ql-toolbar');
    const $editor = $field.find('.ql-editor');
    
    // 检查是否已存在 HTML 源码输入框
    let $sourceTextarea = $field.find('.text-editor-source-textarea');
    
    if ($sourceTextarea.length > 0 && $sourceTextarea.is(':visible')) {
        // 隐藏 HTML 编辑器
        $sourceTextarea.hide();
        $toggleBtn.attr('aria-pressed', 'false');
    } else {
        // 显示 HTML 编辑器
        let htmlContent = '';
        
        // 优先从 Quill 编辑器获取内容
        if ($editor.length > 0) {
            const quill = $editor[0].__quill;
            if (quill) {
                htmlContent = quill.root.innerHTML;
            } else {
                htmlContent = $editor.html() || '';
            }
        }
        
        // 如果编辑器中没有内容，尝试从表单或字段属性获取
        if (!htmlContent && frm && frm.doc && frm.doc[fieldname]) {
            htmlContent = frm.doc[fieldname] || '';
        } else if (!htmlContent) {
            htmlContent = $field.attr('data-value') || '';
        }
        
        // 如果 HTML 编辑器已存在但隐藏，显示它并更新内容
        if ($sourceTextarea.length > 0) {
            $sourceTextarea.val(htmlContent).show();
        } else {
            // 创建 HTML 源码输入框，移除圆角和边距
            $sourceTextarea = $('<textarea class="text-editor-source-textarea form-control" style="min-height: 200px; font-family: monospace; font-size: 12px; width: 100%; display: block; border-radius: 0; margin: 0;"></textarea>')
                .val(htmlContent)
                .on('input', function() {
                    const newContent = $(this).val();
                    // 实时更新字段值
                    if (frm && frm.doc) {
                        frm.set_value(fieldname, newContent);
                    } else {
                        $field.attr('data-value', newContent);
                    }
                    
                    // 同步更新富文本编辑器内容
                    if ($editor.length > 0) {
                        const quill = $editor[0].__quill;
                        if (quill) {
                            quill.root.innerHTML = newContent;
                            quill.update();
                        } else {
                            $editor.html(newContent);
                        }
                    }
                });
            
            // 将 HTML 编辑器添加到工具栏后面
            $toolbar.after($sourceTextarea);
        }
        
        // 更新按钮状态
        $toggleBtn.attr('aria-pressed', 'true');
        
        // 聚焦到输入框
        setTimeout(() => {
            $sourceTextarea.focus();
        }, 100);
    }
};
