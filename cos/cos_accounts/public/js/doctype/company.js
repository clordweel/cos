frappe.ui.form.on('Company', {
	refresh: function (frm) {
		if (frm.is_new()) {
			return;
		}

		// 直接显示工具按钮，在点击时进行检查和确认
		add_initialize_defaults_button(frm);
		add_initialize_tax_templates_button(frm);
	}
});

/**
 * 检查科目表类型并显示确认对话框
 * 处理从母公司继承科目表的情况
 */
function check_chart_and_confirm(frm, callback) {
	const chart_of_accounts = frm.doc.chart_of_accounts;
	const parent_company = frm.doc.parent_company;
	
	// 方法1: 先检查当前公司的科目表
	if (chart_of_accounts && chart_of_accounts.startsWith('一般企业会计准则(2024)')) {
		// 当前公司使用中国会计准则，直接执行回调
		callback(true);
		return;
	}
	
	// 方法2: 如果当前公司没有科目表或是子公司，检查母公司的科目表
	if (parent_company) {
		frappe.db.get_value('Company', parent_company, 'chart_of_accounts', (r) => {
			if (r && r.chart_of_accounts) {
				const parent_chart = r.chart_of_accounts;
				const is_cn_chart = parent_chart.startsWith('一般企业会计准则(2024)');
				
				if (is_cn_chart) {
					// 母公司使用中国会计准则，直接执行回调
					callback(true);
					return;
				} else {
					// 母公司不使用中国会计准则，显示确认对话框
					const message = chart_of_accounts 
						? __('当前公司的科目表不是"一般企业会计准则(2024)"，且父公司"{0}"的科目表也不是。', [parent_company]) + ' ' +
							__('是否仍要继续？')
						: __('该公司从父公司"{0}"继承科目表，但父公司的科目表不是"一般企业会计准则(2024)"。', [parent_company]) + ' ' +
							__('是否仍要继续？');
					show_confirmation_dialog(frm, false, message, callback);
				}
			} else {
				// 无法获取母公司科目表，显示确认对话框
				const message = chart_of_accounts
					? __('当前公司的科目表不是"一般企业会计准则(2024)"，且无法获取父公司"{0}"的科目表信息。', [parent_company]) + ' ' +
						__('是否仍要继续？')
					: __('该公司从父公司"{0}"继承科目表，但无法获取父公司的科目表信息。', [parent_company]) + ' ' +
						__('是否要继续？');
				show_confirmation_dialog(frm, false, message, callback);
			}
		});
	} else {
		// 没有母公司，显示确认对话框让用户确认
		const message = chart_of_accounts
			? __('当前公司的科目表不是"一般企业会计准则(2024)"，是否仍要继续？')
			: __('无法自动检测科目表类型。') + ' ' +
				__('是否要继续？');
		show_confirmation_dialog(frm, false, message, callback);
	}
}

/**
 * 显示确认对话框
 */
function show_confirmation_dialog(frm, is_likely_cn, message, callback) {
	const dialog = new frappe.ui.Dialog({
		title: __('确认操作'),
		fields: [
			{
				fieldtype: 'HTML',
				options: '<div style="padding: 10px 0;">' +
					'<p>' + message + '</p>' +
					(is_likely_cn ? 
						'<p style="color: #28a745; margin-top: 10px;"><strong>✓ 系统检测到可能使用中国会计准则</strong></p>' : 
						'<p style="color: #ffc107; margin-top: 10px;"><strong>⚠ 请确认是否使用中国会计准则</strong></p>') +
					'</div>'
			},
			{
				fieldtype: 'Check',
				label: __('确认继续'),
				fieldname: 'confirm',
				default: is_likely_cn ? 1 : 0,
				description: __('勾选后将执行操作')
			}
		],
		primary_action_label: __('确定'),
		secondary_action_label: __('取消'),
		primary_action: function() {
			const confirm = dialog.get_value('confirm');
			dialog.hide();
			if (confirm) {
				callback(true);
			}
		},
		secondary_action: function() {
			dialog.hide();
		}
	});
	dialog.show();
}

/**
 * 添加"初始化默认值"按钮
 */
function add_initialize_defaults_button(frm) {
	frm.add_custom_button(__('初始化默认值'), function () {
		// 先检查科目表类型并确认
		check_chart_and_confirm(frm, function(confirmed) {
			if (!confirmed) {
				return;
			}
			
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
				primary_action: function () {
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
							callback: function (r) {
								if (r.message) {
									const result = r.message;
									if (result.success) {
										// 在前端直接设置字段值
										if (result.values_to_set) {
											Object.keys(result.values_to_set).forEach(function (field_name) {
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
							error: function (r) {
								frappe.show_alert({
									message: __('初始化默认值时出现错误'),
									indicator: 'red'
								}, 5);
							}
						});
					}
				});
			dialog.show();
		});
	}, __('Tools'));
}

/**
 * 添加"初始化税费模板"按钮
 */
function add_initialize_tax_templates_button(frm) {
	frm.add_custom_button(__('初始化税费模板'), function () {
		// 先检查科目表类型并确认
		check_chart_and_confirm(frm, function(confirmed) {
			if (!confirmed) {
				return;
			}
			
			// 显示确认对话框
			const dialog = new frappe.ui.Dialog({
				title: __('初始化税费模板'),
				fields: [
					{
						fieldtype: 'HTML',
						options: '<p>' + __('确定要为该公司初始化税费模板吗？') + '</p>' +
							'<p style="color: #999; font-size: 12px;">' +
							__('将创建以下税率模板：13%、9%、6%、3%、1% 的销项和进项模板') +
							'</p>'
					}
				],
				primary_action_label: __('确定'),
				primary_action: function () {
					dialog.hide();

					// 执行初始化
					frappe.call({
						method: 'cos.cos_accounts.controllers.company_tax.initialize_tax_templates',
						args: {
							company: frm.doc.name
						},
						freeze: true,
						freeze_message: __('正在初始化进销项税费模板...'),
						callback: function (r) {
							if (r.message) {
								const result = r.message;
								if (result.success) {
									frappe.show_alert({
										message: result.message,
										indicator: 'green'
									}, 5);

									// 如果有详细信息，显示在控制台
									if (result.details) {
										if (result.details.deleted && result.details.deleted.count > 0) {
											console.log('删除的系统默认模板:', result.details.deleted.templates);
										}
										if (result.details.created_templates && result.details.created_templates.length > 0) {
											console.log('新建的模板:', result.details.created_templates);
										}
										if (result.details.skipped_templates && result.details.skipped_templates.length > 0) {
											console.log('跳过的已存在模板:', result.details.skipped_templates);
										}
										if (result.details.sales_templates && result.details.sales_templates.length > 0) {
											console.log('所有销项模板:', result.details.sales_templates);
										}
										if (result.details.purchase_templates && result.details.purchase_templates.length > 0) {
											console.log('所有进项模板:', result.details.purchase_templates);
										}
									}

									// 刷新表单以显示新创建的模板
									frm.reload_doc();
								} else {
									frappe.show_alert({
										message: result.message,
										indicator: 'orange'
									}, 5);
								}
							}
						},
						error: function (r) {
							frappe.show_alert({
								message: __('初始化税费模板时出现错误'),
								indicator: 'red'
							}, 5);
						}
					});
				}
			});
			dialog.show();
		});
	}, __('Tools'));
}
