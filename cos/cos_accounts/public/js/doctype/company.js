frappe.ui.form.on('Company', {
	refresh: function(frm) {
		// 检查是否使用了一般企业会计准则(2024)科目表
		const chart_of_accounts = frm.doc.chart_of_accounts;
		const is_cn_chart = chart_of_accounts && chart_of_accounts.startsWith('一般企业会计准则(2024)');
		
		if (is_cn_chart && !frm.is_new()) {
			// 添加"初始化默认值"按钮
			frm.add_custom_button(__('初始化默认值'), function() {
				// 显示对话框，让用户选择是否覆盖已有值
				const dialog = new frappe.ui.Dialog({
					title: __('初始化默认值'),
					fields: [
						{
							fieldtype: 'HTML',
							options: '<p>' + __('确定要为该公司初始化默认值吗？') + '</p>'
						},
						{
							fieldtype: 'Check',
							label: __('覆盖已有值'),
							fieldname: 'override_existing',
							default: 0,
							description: __('勾选后将覆盖所有已有值的字段，否则只填充空值字段')
						}
					],
					primary_action_label: __('确定'),
					primary_action: function() {
						const override_existing = dialog.get_value('override_existing');
						dialog.hide();
						
						// 执行初始化
						frappe.call({
							method: 'cos.cos_accounts.controllers.company.initialize_company_defaults',
							args: {
								company: frm.doc.name,
								override_existing: override_existing ? 1 : 0
							},
							freeze: true,
							freeze_message: __('正在初始化默认值...'),
							callback: function(r) {
								if (r.message) {
									const result = r.message;
									if (result.success) {
										// 在前端直接设置字段值
										if (result.values_to_set) {
											Object.keys(result.values_to_set).forEach(function(field_name) {
												frm.set_value(field_name, result.values_to_set[field_name]);
											});
										}
										
										frappe.show_alert({
											message: result.message,
											indicator: 'green'
										}, 5);
									} else {
										frappe.show_alert({
											message: result.message,
											indicator: 'orange'
										}, 5);
									}
									
									// 如果有详细信息，显示在控制台
									if (result.details) {
										if (result.details.accounts_not_found && 
											Object.keys(result.details.accounts_not_found).length > 0) {
											console.log('未找到的账户字段:', result.details.accounts_not_found);
										}
										if (result.details.skipped_fields && 
											result.details.skipped_fields.length > 0) {
											console.log('跳过的字段:', result.details.skipped_fields);
										}
									}
								}
							},
							error: function(r) {
								frappe.show_alert({
									message: __('初始化默认值时出现错误'),
									indicator: 'red'
								}, 5);
							}
						});
					}
				});
				dialog.show();
			}, __('操作'));
		}
	}
});
