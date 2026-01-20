# 销售订单合同打印格式模板

## 模板概述

本模板用于生成"销售订单合同"（Sales Order Contract），适用于销售业务场景的正式合同文档打印格式。该模板遵循《中华人民共和国民法典》等相关法律法规，提供完整的购销合同条款。

## 模板特点

### 1. 文档结构

- **文档类型**：购销合同（Sales Order Contract）
- **合同头部**：合同编号、标题、买卖双方信息、签订日期和地点
- **标的物表格**：序号、名称、规格型号、单位、数量、单价、总额、交货期限、备注
- **合同条款**：包含十九个主要条款章节
- **签名区域**：买卖双方签名盖章区域，包含统一社会信用代码、法定代表人等信息

### 2. 主要功能

#### 合同头部信息
- **合同编号**：显示文档编号（`doc.name`）
- **标题**：显示"购销合同"
- **买受人**：显示客户名称（`doc.customer_name`）
- **出卖人**：显示公司名称（`doc.company`）
- **签订日期**：显示交易日期（`doc.transaction_date`），格式化为中文日期格式
- **签订地点**：空白填写区域

#### 标的物表格
- **序号**：自动编号（`loop.index`）
- **名称**：显示物料名称（`item.item_name`）
- **规格型号**：显示物料规格（`item.custom_specification` 或从 Item 表获取）
- **单位**：显示单位（`item.uom`）
- **数量**：显示数量（`item.qty`），整数显示为整数，小数显示两位小数
- **单价**：显示单价（`item.rate`），格式化为两位小数
- **总额**：显示金额（`item.amount`），格式化为两位小数
- **交货期限**：显示交货日期（`item.delivery_date`），如果存在
- **备注**：空白填写区域
- **合计行**：显示总数量和总金额
- **总计行**：显示金额大写（`doc.in_words`）

#### 合同条款
模板包含以下十九个主要条款章节：

1. **一、标的物**：标的物明细表格
2. **二、质量标准、技术要求**：质量标准和技术要求选项
3. **三、费用**：送货费、安装费等费用承担方式
4. **四、包装标准、包装物的提供与回收**：包装相关条款
5. **五、附随必备品、配件、工具的的名称、规格、数量、交付方式**：附随物品说明
6. **六、结算方式及期限**：一次性支付、分期付款、预付款、定金等选项
7. **七、发票**：发票开具相关条款
8. **八、合理损耗标准及计算方法**：损耗标准说明
9. **九、交付**：交付方式、交付批次、运输方式、交货时间和地点
10. **十、检验**：检验标准、检验期限、检验地点等
11. **十一、标的物所有权转移**：所有权转移条件
12. **十二、标的物的毁损、灭失的风险承担**：风险承担说明
13. **十三、成套设备的安装与调试**：安装调试相关条款
14. **十四、担保方式**：担保方式说明
15. **十五、质量保证期**：质量保证期和服务响应时间
16. **十六、违约责任**：包含出卖人违约和买受人违约两个子章节
17. **十七、争议解决**：争议解决方式（诉讼或仲裁）
18. **十八、其他约定事项**：其他约定事项填写区域
19. **十九、其他**：合同生效条件、语言版本、合同份数等

#### 条款显示逻辑
- 如果 `doc.custom_is_print_terms` 为真且 `doc.terms` 存在，则显示自定义条款（`doc.terms`）
- 否则显示标准合同条款（二至十九章节）

#### 签名区域
- **买受人（盖章/签名）**：包含统一社会信用代码、法定代表人、委托代表人、地址、电话、开户银行、账号
- **出卖人（盖章/签名）**：包含统一社会信用代码、法定代表人、委托代表人、地址、电话、开户银行、账号

### 3. HTML结构特点

#### 样式框架
- **独立CSS文件**：样式提取到 `styles.css` 文件中
- **Flexbox布局**：使用 Flexbox 进行灵活的布局控制
- **打印优化**：包含 `@media print` 规则和 `@page` 规则

#### 主要容器
- `.print-format`：主容器
- `.contract-number`：合同编号区域
- `.header-title`：合同标题
- `.contract-parties`：买卖双方信息区域
- `.contract-date-location`：签订日期和地点区域
- `.item-table`：标的物表格
- `.section-title`：章节标题
- `.section-subtitle`：子章节标题
- `.clause-content`：条款内容
- `.signature-table`：签名表格

#### 关键元素类名
- `.party-line`：买卖双方信息行
- `.party-label`：标签（如"买受人："）
- `.party-value`：值（带下划线）
- `.date-location-item`：日期/地点项
- `.date-location-label`：日期/地点标签
- `.date-location-value`：日期/地点值（带下划线）
- `.checkbox-item`：复选框项
- `.checkbox`：复选框
- `.checkbox-label`：复选框标签
- `.fill-field`：填写字段（带下划线）
- `.signature-info`：签名信息行
- `.signature-label`：签名标签
- `.signature-value`：签名值（带下划线）

### 4. 数据字段映射

#### 从doc对象获取的字段

##### 基础字段
- `doc.name`：文档编号（合同编号）
- `doc.transaction_date`：交易日期（签订日期）
- `doc.customer_name`：客户名称（买受人）
- `doc.company`：公司名称（出卖人）
- `doc.grand_total`：订单总计
- `doc.in_words`：金额大写
- `doc.custom_is_print_terms`：是否打印自定义条款（自定义字段）
- `doc.terms`：自定义条款（富文本）

##### 关联字段
- `doc.items`：物料明细列表
  - `item.item_code`：物料代码
  - `item.item_name`：物料名称
  - `item.custom_specification`：物料规格（自定义字段）
  - `item.uom`：单位
  - `item.qty`：数量
  - `item.rate`：单价
  - `item.amount`：金额
  - `item.delivery_date`：交货日期

##### 计算字段
- `specification`：物料规格（优先使用 `item.custom_specification`，否则从 Item 表获取）
- `total_qty_sum`：总数量（所有物料数量之和）
- `date_parts`：日期部分（年、月、日）

### 5. 重要信息

#### 日期格式化
- 使用 `frappe.utils.format_date(doc.transaction_date, "yyyy-mm-dd")` 格式化日期
- 将日期拆分为年、月、日三部分
- 显示格式：`YYYY年MM月DD日`

#### 数量格式化
- 如果数量为整数：显示为整数格式（`{:,.0f}`）
- 如果数量为小数：显示为两位小数格式（`{:,.2f}`）

#### 金额格式化
- 单价和金额：使用两位小数格式（`{:,.2f}`）
- 总金额：使用两位小数格式（`{:,.2f}`）
- 金额大写：使用 `doc.in_words` 字段

#### 物料规格获取
1. **优先级1**：从物料明细行获取（`item.custom_specification`）
2. **优先级2**：从 Item 表获取（`frappe.db.get_value("Item", item.item_code, "custom_specification")`）
3. **默认值**：空字符串

#### 条款显示逻辑
- **条件**：`doc.custom_is_print_terms` 为真且 `doc.terms` 存在
- **显示**：自定义条款（`doc.terms | safe`）
- **否则**：显示标准合同条款（二至十九章节）

### 6. 特殊说明

#### 表格样式
- 标的物表格：固定表格布局（`table-layout: fixed`）
- 表头：浅灰色背景（`#f0f0f0`）
- 边框：黑色单边框（`1px solid #000`）
- 单元格内边距：`6px 4px`（打印时：`5px 3px`）

#### 填写字段
- `.fill-field`：带下划线的填写字段
- `.party-value`：带下划线的值字段
- `.date-location-value`：带下划线的日期/地点值字段
- `.signature-value`：带下划线的签名值字段
- 空字段自动显示空格（使用 `:empty::after` 伪元素）

#### 复选框
- 使用 `.checkbox` 类创建复选框样式
- 覆盖 Bootstrap 的 checkbox 样式干扰
- 复选框尺寸：`14px × 14px`

#### 打印优化
- 使用 `@media print` 规则优化打印效果
- 使用 `@page` 规则设置页面边距（`8mm 10mm`）
- 页面大小：A4
- 颜色精确打印（`print-color-adjust: exact`）
- 章节标题避免分页（`page-break-after: avoid`）
- 通知区域避免分页（`page-break-inside: avoid`）

### 7. 样式实现

#### 布局特点
- **Flexbox布局**：使用 Flexbox 进行灵活的布局控制
- **固定表格布局**：标的物表格使用固定表格布局（`table-layout: fixed`）
- **响应式设计**：支持不同屏幕尺寸的显示

#### 样式特点
- 专业的合同文档样式
- 清晰的章节结构
- 易于填写的表单字段
- 打印和PDF导出优化
- 符合法律文档规范

### 8. 文件结构

```
sale-order-contract/
├── template.html      # 主模板文件
├── styles.css         # 样式文件
└── README.md          # 文档说明
```

### 9. 使用说明

1. **模板位置**：`print_format/sale-order-contract/template.html`
2. **样式文件**：`print_format/sale-order-contract/styles.css`
3. **在Frappe中配置**：
   - 创建或编辑打印格式
   - 选择"HTML"类型
   - 将 `template.html` 的内容复制到模板编辑器
   - 确保样式文件 `styles.css` 被正确引用

### 10. 注意事项

#### 自定义字段
- `doc.custom_is_print_terms`：控制是否显示自定义条款
- `item.custom_specification`：物料规格自定义字段

#### 数据完整性
- 确保 `doc.items` 存在且不为空
- 确保 `doc.customer_name` 和 `doc.company` 存在
- 确保 `doc.transaction_date` 存在

#### 条款自定义
- 如果需要在合同中显示自定义条款，设置 `doc.custom_is_print_terms = 1` 并填写 `doc.terms`
- 自定义条款支持富文本格式（使用 `| safe` 过滤器）

### 11. 待完善项

- 可能需要支持更多自定义字段
- 可能需要添加合同附件功能
- 可能需要支持多语言版本
- 可能需要添加合同模板选择功能
