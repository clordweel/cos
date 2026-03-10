# 物料需求 - 外部

物料需求单的**外部版**打印格式，适用于对外（如供应商）展示场景。

## 与标准版差异

- **头信息**：去除「项目」「关联」字段，仅保留单号、日期、类型
- **表格**：去除「目标仓库」列
- **底部**：去除签字栏

## 同步到站点

```bash
bench --site <site> execute cos.scripts.sync_material_request_external.sync
```
