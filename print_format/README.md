# 打印格式帮助文档

## 简介

打印格式是使用 Jinja 模板语言在服务器端渲染的。所有表单都可以访问 `doc` 对象，该对象包含正在格式化的文档的相关信息。你还可以通过 `frappe` 模块访问常用工具。

在样式设计方面，我们提供了 Bootstrap CSS 框架，你可以使用全部的类。

## 自定义 CSS 帮助

### 字段属性说明

- 所有字段组（标签 + 值）都设置了属性 `data-fieldtype` 和 `data-fieldname`
- 所有值都有类 `value`
- 所有分隔段均为 `section-break` 类
- 所有分隔列均为 `column-break` 类

### CSS 示例

#### 1. 左对齐整数字段

```css
[data-fieldtype="Int"] .value {
    text-align: left;
}
```

#### 2. 为除最后一节外的各节添加边框

```css
.section-break {
    padding: 30px 0px;
    border-bottom: 1px solid #eee;
}

.section-break:last-child {
    padding-bottom: 0px;
    border-bottom: 0px;
}
```

## 模板示例

### 基本结构示例

```html
<h3>{{ doc.select_print_heading or "Invoice" }}</h3>

<div class="row">
    <div class="col-md-3 text-right">客户姓名</div>
    <div class="col-md-9">{{ doc.customer_name }}</div>
</div>

<div class="row">
    <div class="col-md-3 text-right">Date</div>
    <div class="col-md-9">{{ doc.get_formatted("invoice_date") }}</div>
</div>
```

### 表格示例

```html
<table class="table table-bordered">
    <tbody>
        <tr>
            <th>Sr</th>
            <th>Item Name</th>
            <th>Description</th>
            <th class="text-right">Qty</th>
            <th class="text-right">Rate</th>
            <th class="text-right">Amount</th>
        </tr>
        {%- for row in doc.items -%}
        <tr>
            <td style="width: 3%;">{{ row.idx }}</td>
            <td style="width: 20%;">
                {{ row.item_name }}
                {% if row.item_code != row.item_name -%}
                <br>项目代码：{{ row.item_code }}
                {%- endif %}
            </td>
            <td style="width: 37%;">
                <div style="border: 0px;">{{ row.description }}</div>
            </td>
            <td style="width: 10%; text-align: right;">
                {{ row.qty }} {{ row.uom or row.stock_uom }}
            </td>
            <td style="width: 15%; text-align: right;">
                {{ row.get_formatted("rate", doc) }}
            </td>
            <td style="width: 15%; text-align: right;">
                {{ row.get_formatted("amount", doc) }}
            </td>
        </tr>
        {%- endfor -%}
    </tbody>
</table>
```

## 常用函数

### doc.get_formatted()

获取格式化为日期、货币等的文档值。对于货币类型字段，请传递父 doc。

**语法：**
```python
doc.get_formatted("[fieldname]", [parent_doc])
```

**示例：**
```html
{{ doc.get_formatted("invoice_date") }}
{{ row.get_formatted("rate", doc) }}
```

### frappe.db.get_value()

从另一个文档获取值。

**语法：**
```python
frappe.db.get_value("[doctype]", "[name]", "fieldname")
```

**示例：**
```html
{{ frappe.db.get_value("User", doc.owner, "full_name") }}
```

## 采购订单 · 代发货单 / 直发单（`采购订单 - 代发货单`）

用于供应商**直发现场**或采购方委托发货时的**物流交接**：不含单价/金额/条款/签字；**不作为合同或结算依据**（页脚有声明）。

- **标题**：打印标题为「**直发单**」。
- **委托方**：显示 `Company.company_name`（缺省为公司简称字段），对应采购公司。
- **收货信息**：优先取 `shipping_address` 对应 `Address.custom_address_display`，否则用 `shipping_address_display`；联系人与电话取自 `custom_shipping_contact_person`、`custom_shipping_contact_phone`（无则整块「收货信息」不显示）。
- **项目客户**：有关联项目时，从 `Project.customer` 解析客户名称，在「关联项目」下单独一行「项目客户」。
- **物料行仓库**：取自采购订单明细 `warehouse`，展示 `Warehouse.warehouse_name`。
- **数量**：整数量不显示小数，否则保留两位小数。
- **仓库源文件**：`print_format/purchase-order-proxy-delivery/`；更新后可执行 `cos.scripts.sync_purchase_order_proxy_delivery_print_format.sync`，或通过迁移补丁将模板写入站点。

## 参考资料

- [Jinja 模板语言](https://jinja.palletsprojects.com/)
- [Bootstrap CSS 框架](https://getbootstrap.com/)
