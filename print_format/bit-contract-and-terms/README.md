# 购销合同模板

## 模板概述

本模板用于生成"购销合同"，适用于比特物联科技有限公司的销售合同打印格式。

## 模板特点

### 1. 合同结构
- **合同类型**：购销合同
- **合同标题**：购销合同（居中显示，顶部留白30px，下边距 `mb-2`）
- **合同编号**：标题下方居中显示，格式为"编号：{合同编号}"（无下划线，下边距 `mb-4`）
  - 优先使用 `doc.custom_contract_no`，否则使用 `doc.name`
- **合同双方**：甲方（需方）、乙方（供方）（左侧，两列横排布局）
  - 使用 `<u>` 标签显示下划线
- **签订信息**：签订时间、签订地点（右侧，与合同双方信息横排对齐）
  - 签订时间：优先使用 `doc.custom_signing_date`，否则使用 `doc.transaction_date`
  - 签订地点：使用 `doc.custom_signing_location`
  - 使用 `<u>` 标签显示下划线
- **布局特点**：使用 Bootstrap v3.3.1 的 `row`/`col-xs-6` 实现两列布局，防止打印时换行

### 2. 主要章节（共十二条）

#### 第一条：项目及服务说明
- 1.1 产品名称、规格型号、数量、金额（表格形式，备注列显示 `item.description`，使用 `striptags` 提取纯文本）
- 1.2 服务与支持（包含免费调试天数、超期收费标准，关键数值使用 `<u>` 标签标记）
- 1.3 合同总金额（含税金额、税率说明，金额和税率使用 `<u>` 标签标记）

#### 第二条：付款方式及发票开具
- 2.1 付款方式（表格形式，从 `doc.payment_schedule` 字段动态渲染，包含序号、款项名称、付款条件、付款比例、付款金额、结算方式）
- 2.2 发票开具（发票开具时间要求，包含90%付款额触发全额发票的条款）

#### 第三条：制作要求及质量标准
- 3.1 技术标准要求
- 3.2 产品质量要求

#### 第四条：项目交付与验收
- 4.1 交货时间与地点（交货期限左对齐填空，包含收货人、收货电话、收货地址，均使用 `<u>` 标签标记）
- 4.2 项目交付（到货验收期限7天、补救措施期限3个工作日，关键时间使用 `<u>` 标签标记）

#### 第五条：质量保证与售后服务
- 质保期说明
- 技术支持要求

#### 第六条：知识产权
- 知识产权保护条款

#### 第七条：违约责任
- 7.1 甲方逾期付款责任（每日违约金0.05%，逾期超过30天可暂停履行）
- 7.2 乙方逾期交付责任（每日违约金0.05%，逾期超过30天可解除合同，违约金20%）
- 7.3 质量不符合要求的责任（违约金20%）
- **关键数值标记**：所有违约金比例、逾期天数、违约金百分比均使用 `<u>` 标签标记，数值与单位分离（如"<u>0.05</u> %"）

#### 第八条：不可抗力
- 不可抗力处理方式（通知期限24小时、证明文件提供期限3日，关键时间使用 `<u>` 标签标记）

#### 第九条：争议解决
- 争议解决方式

#### 第十条：通知与送达
- 通知方式要求
- 通信信息表格（通信方、联系人、通讯地址、联系电话、邮箱）
  - 使用自定义字段：`custom_first_party_signer`、`custom_first_party_signer_phone`、`custom_first_party_signer_email`、`custom_second_party_signer`、`custom_second_party_signer_phone`、`custom_second_party_signer_email`

#### 第十一条：其他款项
- 合同生效、份数、补充协议

#### 第十二条：附件
- 附件说明
- 12.2 附件清单：后添加 `<u>` 标签下划线填空区域
- 双方详细信息表格（单位名称、单位地址、签订代表、联系方式、开户银行、银行账号、企业税号）
  - 表格调整为两列等宽（各50%），内容左对齐，垂直对齐顶部
  - 标签宽度统一为80px，布局更紧凑
  - 使用 `table-bordered` 边框样式，padding 为 `20px !important`
  - 使用自定义字段：
    - 甲方：`custom_first_party_law`、`custom_first_party_signer`、`custom_first_party_signer_phone`、`custom_payment_bank`、`custom_payment_bank_account_no`、`custom_first_party_tax_id`
    - 乙方：`custom_second_party_law`、`company_address_display`、`custom_second_party_signer`、`custom_second_party_signer_phone`、`custom_payment_bank`、`custom_payment_bank_account_no`、`custom_second_party_tax_id`

### 3. HTML结构特点

#### 样式框架
- **Bootstrap CSS框架**：模板使用 **Bootstrap v3.3.1** 进行样式化
- **兼容性注意**：Bootstrap v3.3.1 不包含 flex 相关样式，使用 `row`/`col-xs-*` 网格系统实现布局
- **自定义样式**：通过`styles.css`补充Bootstrap未覆盖的样式需求

#### 主要容器
- **注意**：模板外层系统已提供 `print-format` 容器，模板内不再使用此容器

#### 关键元素类名（结合Bootstrap类）
- `.header-title`：合同标题（顶部留白30px，下边距 `mb-2`）
- `.contract-number`：合同编号（标题下方居中，下边距 `mb-4`，无下划线）
- `.contract-parties`：合同双方信息（左侧列）
- `.party-line`：单方信息行（使用 `white-space: nowrap` 防止打印时换行）
- `.party-label`：标签（如"甲方（需方）："，宽度100px）
- `.party-value`：值（使用 `<u>` 标签显示下划线）
- `.contract-date-location`：签订信息（右侧列）
- `.date-location-item`：单个日期/地点项（使用 `white-space: nowrap` 防止打印时换行）
- `.date-location-label`：日期/地点标签（宽度80px）
- `.date-location-value`：日期/地点值（使用 `<u>` 标签显示下划线）
- `.regulatory-info`：前言说明（无 `small` 标签，直接使用正常字体）
- `.section-title`：章节标题（如"第一条"，上边距24px，下边距12px）
- `.section-subtitle`：小节标题（如"1.1"，上边距16px，下边距10px）
- `.item-table`：表格（产品表格、付款方式表格、通信信息表格，单元格默认居中对齐）
- `.clause-content`：条款内容容器（下边距16px，行高1.8）
- `.clause-item`：单个条款项（下边距10px，文本两端对齐）
- `.indent`：缩进（用于子条款）
- **填充字段**：使用 `<u>` 标签替代 `.fill-field` 类，直接显示下划线
- `.signature-table`：签名/附件信息表格（两列等宽，内容左对齐，使用 `table-bordered`，padding `20px !important`）
- `.signature-info`：签名信息行
- `.signature-label`：签名信息标签（宽度80px）
- `.signature-value`：签名信息值

#### Bootstrap工具类使用
- **布局类**：`row`, `col-xs-6`（Bootstrap v3 网格系统，不使用 flex 相关类）
- **间距类**：`mb-2`, `mb-3`, `mb-4`, `mt-3`, `mt-4`, `mr-2`, `pt-3`
- **文本类**：`text-center`, `text-right`, `text-left`, `text-muted`, `font-weight-bold`
- **表格类**：`table`, `table-bordered`, `table-sm`, `table-borderless`
- **边框类**：`border-top`
- **注意**：不再使用 `small` 标签，避免字体过小

#### 表格对齐
- 默认：所有表格单元格默认居中对齐（通过CSS设置）
- `.text-left`：左对齐（Bootstrap类，用于备注列等需要左对齐的内容）
- `.text-right`：右对齐（Bootstrap类）

#### 表格结构特点
- 使用 `data-row` 属性标识表格行（Quill 编辑器输出格式）
- 表格使用 `table-bordered` 边框样式
- 表格字体大小统一为 `12px`
- 表格单元格使用内联样式设置宽度和对齐方式

### 4. 数据字段映射

#### 从doc对象获取的字段

##### 基础字段
- `doc.name`：合同编号（默认值，显示为"编号：{doc.name}"，无下划线）
- `doc.custom_contract_no`：自定义合同编号（优先使用，如果存在则替代 `doc.name`）
- `doc.customer_name`：甲方（需方）名称（使用 `<u>` 标签显示下划线）
- `doc.company`：乙方（供方）名称（使用 `<u>` 标签显示下划线）
- `doc.transaction_date`：签订时间（默认值，格式化为"yyyy年mm月dd日"）
- `doc.custom_signing_date`：自定义签订时间（优先使用，如果存在则替代 `doc.transaction_date`）
- `doc.custom_signing_location`：签订地点

##### 产品列表
- `doc.items`：产品列表
  - `item.item_name`：产品名称
  - `item.custom_specification`：规格型号
  - `item.qty`：数量
  - `item.uom`：单位
  - `item.rate`：单价
  - `item.amount`：总价
  - `item.description`：备注（使用 `striptags` 过滤器提取纯文本）

##### 金额相关
- `doc.grand_total`：合同总金额（格式化为千分位，使用 `<u>` 标签标记）
- `doc.in_words`：金额大写（使用 `<u>` 标签标记）

##### 付款方式
- `doc.payment_schedule`：付款方式列表（动态渲染付款方式表格）
  - `payment.description`：款项名称
  - `payment.payment_term`：付款条件
  - `payment.invoice_portion`：付款比例
  - `payment.due_date`：付款日期
  - `payment.payment_amount`：付款金额

##### 通信信息（自定义字段）
- `doc.custom_first_party_signer`：甲方联系人
- `doc.custom_first_party_signer_phone`：甲方联系电话
- `doc.custom_first_party_signer_email`：甲方邮箱
- `doc.custom_second_party_signer`：乙方联系人
- `doc.custom_second_party_signer_phone`：乙方联系电话
- `doc.custom_second_party_signer_email`：乙方邮箱
- `doc.address_display`：甲方地址
- `doc.company_address_display`：乙方地址

##### 附件信息（自定义字段）
- `doc.custom_first_party_law`：甲方单位名称
- `doc.custom_first_party_signer`：甲方签订代表
- `doc.custom_first_party_signer_phone`：甲方联系方式
- `doc.custom_payment_bank`：开户银行（双方共用）
- `doc.custom_payment_bank_account_no`：银行账号（双方共用）
- `doc.custom_first_party_tax_id`：甲方企业税号
- `doc.custom_second_party_law`：乙方单位名称
- `doc.custom_second_party_signer`：乙方签订代表
- `doc.custom_second_party_signer_phone`：乙方联系方式
- `doc.custom_second_party_tax_id`：乙方企业税号

##### 条件渲染
- `doc.custom_is_print_terms`：是否使用自定义条款（布尔值）
- `doc.terms`：自定义条款内容（Quill 编辑器输出的 HTML）

### 5. 重要信息

#### 合同编号格式
- 显示格式：编号：{doc.custom_contract_no or doc.name}
- 位置：标题下方居中
- 样式：无下划线，下边距 `mb-4`
- 优先级：优先使用 `doc.custom_contract_no`，如果不存在则使用 `doc.name`

#### 产品表格列
- 序号、名称、规格型号、数量、单位、单价（元）、总价（元）、备注
- 备注列：显示 `item.description`，使用 `striptags` 提取纯文本，左对齐，列宽较大以容纳内容

#### 付款方式表格列
- 序号、款项名称、付款条件、付款比例、付款金额（元）、结算方式
- 数据源：从 `doc.payment_schedule` 动态渲染

#### 通信信息表格列
- 通信方、联系人、通讯地址、联系电话、邮箱
- 数据源：使用自定义字段（`custom_first_party_signer`、`custom_second_party_signer` 等）
- 表格结构：使用 `data-row` 属性，符合 Quill 编辑器输出格式

#### 附件信息表格
- 左右两列：甲方、乙方（各占50%宽度）
- 每列包含：单位名称、单位地址、签订代表、联系方式、开户银行、银行账号、企业税号
- 布局：内容左对齐，垂直对齐顶部，标签宽度80px
- 样式：使用 `table-bordered` 边框，padding `20px !important`
- 数据源：全部使用自定义字段（`custom_first_party_law`、`custom_second_party_law` 等）

### 6. 特殊说明

#### 填充字段（下划线标记）
- **变更**：所有填充字段使用 `<u>` 标签替代 `.fill-field` 类，直接显示下划线
- 关键内容标记：违约金比例、逾期天数、质保期、调试天数等关键数值使用 `<u>` 标签标记
- 数值与单位分离：数值类型的单位（%、日、天、小时）不包含在下划线内，只对数字部分使用下划线
- 示例：`<u>0.05</u> %`、`<u>30</u> 天`、`<u>{{ doc.grand_total }}</u> 元`
- 空白填空：使用 `<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>` 或 `<u> </u>` 创建空白下划线区域

#### 布局和排版
- 条款内容使用 `.clause-content` 和 `.clause-item` 组织
- 子条款使用 `.indent` 类进行缩进
- 表格使用 `.item-table` 统一样式，单元格默认居中对齐
- 签名/附件信息使用 `.signature-table` 和 `.signature-info` 结构
- 防止换行：合同双方信息和签订信息使用 `white-space: nowrap` 防止打印时换行
- 垂直间距：章节标题、小节标题、条款内容使用统一的垂直间距系统

#### 数据渲染
- 付款方式：从 `doc.payment_schedule` 动态渲染
- 备注信息：使用 `striptags` 过滤器从富文本中提取纯文本
- 日期格式化：使用 `frappe.utils.format_date` 和字符串分割实现中文日期格式

#### 宏定义（Macros）
模板定义了三个宏用于表格渲染，可在 Quill 编辑器内容中通过占位符插入：
- `items_table()`：产品表格宏
- `payment_schedule_table()`：付款方式表格宏
- `communication_table()`：通信信息表格宏

#### 条件渲染逻辑
- **自定义条款支持**：当 `doc.custom_is_print_terms` 为 `true` 且 `doc.terms` 存在时，使用 Quill 编辑器输出的自定义条款内容
- **表格占位符**：在 Quill 内容中可以使用以下占位符插入表格：
  - `<p>[[ ITEMS_TABLE ]]</p>`：插入产品表格
  - `<p>[[ PAYMENT_SCHEDULE_TABLE ]]</p>`：插入付款方式表格
  - `<p>[[ COMMUNICATION_TABLE ]]</p>`：插入通信信息表格
- **默认内容**：当不使用自定义条款时，显示默认的合同条款内容（第四条至第十二条）

### 7. 样式实现

#### Bootstrap集成
- 模板已集成 **Bootstrap v3.3.1** CSS框架
- 使用Bootstrap的工具类进行布局和样式控制
- **兼容性**：Bootstrap v3.3.1 不包含 flex 相关样式，使用 `row`/`col-xs-*` 网格系统
- 自定义样式文件`styles.css`补充Bootstrap未覆盖的需求

#### 样式特点
- 响应式布局（使用Bootstrap v3的网格系统 `row`/`col-xs-*`）
- 统一的间距系统（使用Bootstrap的spacing工具类和CSS统一控制）
- 专业的表格样式（结合Bootstrap表格类和自定义样式，默认居中对齐）
- 打印和PDF导出优化（包含@media print规则）
- 防止换行（关键信息使用 `white-space: nowrap` 确保打印时不会换行）

### 8. 待完善项

#### 已实现的自定义字段
- ✅ 合同编号：`custom_contract_no`
- ✅ 签订时间：`custom_signing_date`
- ✅ 签订地点：`custom_signing_location`
- ✅ 通信信息：`custom_first_party_signer`、`custom_second_party_signer` 等
- ✅ 附件信息：`custom_first_party_law`、`custom_second_party_law`、`custom_payment_bank` 等

#### 待完善项
- 部分字段需要从自定义字段或配置中获取（如税率、质保期、调试天数、超期收费标准等）
- 交货期限需要从订单项或自定义字段获取（当前为空白 `<u>` 标签）
- 收货信息需要从地址或自定义字段获取（当前为空白 `<u>` 标签）
- 部分自定义字段可能需要从关联文档（如客户、公司）中自动填充
