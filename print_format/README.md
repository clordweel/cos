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

## 参考资料

- [Jinja 模板语言](https://jinja.palletsprojects.com/)
- [Bootstrap CSS 框架](https://getbootstrap.com/)
