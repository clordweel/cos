# COS 仓库结构化整理方案（去冗余）

**日期**：2026-03-19  
**目标**：去除冗余、统一结构、便于维护

---

## 一、已识别的冗余项

### 1. 明确冗余（建议删除）

| 项 | 路径 | 说明 |
|----|------|------|
| **patch_hooks_revenue.py** | 仓库根目录 | 一次性 patch 脚本，hooks.py 已包含 Delivery Note 等配置，脚本已过时 |
| **cos/report/balance_sheet_china/** | cos/report/ | 与 cos_accounts/report/balance_sheet_china 完全重复，后者归属 COS Accounts 模块更合理 |
| **v16_link_hotfix.js** | cos/public/js/ | hooks.py 中已注释，未加载；若 v16 不再需要 /app/→/desk/ 修复可删除 |

### 2. 可考虑优化（需确认）

| 项 | 路径 | 说明 |
|----|------|------|
| **public/worker_portal/** | cos/public/worker_portal/ | 构建产物（index.html、worker-portal.css、worker-portal.js）当前纳入版本控制。可加入 .gitignore，在 deploy 时执行 `cd worker_portal && npm run build` |
| **cos/backfill_item_base_name.py** | cos 包根目录 | 建议移至 cos/scripts/ 与其他 bench execute 脚本统一 |

### 3. 非冗余（保留）

| 项 | 说明 |
|----|------|
| print_format/ | 打印模板源文件，sync 脚本从此读取 |
| cos/scripts/ | 各 sync 脚本职责清晰，sync_all_standard_print_formats 为统一入口 |
| importable_data/ | 与 fixtures 互补，用于 Data Import 初始化 |
| chart_of_accounts/custom/*.json | 多个科目表（cn_norm、cn_smes 等）均被 coa_setup 使用 |
| worker_portal 源码 vs www | 源码在 worker_portal/，www/ 为不同路由的 HTML 入口，均需保留 |

---

## 二、目录结构建议

```
cos/                          # Frappe app 根
├── cos/                      # Python 包
│   ├── scripts/              # 所有 bench execute 脚本（含 backfill 等）
│   ├── report/               # 删除，仅保留 cos_accounts/report/
│   ├── cos_accounts/
│   │   └── report/           # 财务类报表
│   └── ...
├── print_format/             # 打印模板源
├── importable_data/          # 可导入 CSV
├── chart_of_accounts/        # 科目表 JSON
├── docs/                     # 文档
├── scripts/                  # 仓库级脚本（outline、test）
└── ...
```

---

## 三、执行清单

- [x] 删除 `patch_hooks_revenue.py` ✓
- [x] 删除 `cos/report/balance_sheet_china/`（保留 cos_accounts 版本）✓
- [x] 删除 `cos/public/js/v16_link_hotfix.js` 并移除 hooks 中的注释 ✓
- [x] 将 `cos/backfill_item_base_name.py` 移至 `cos/scripts/`，并更新 ai_cos_ops run_backfill_item_base_name_on_server.py ✓
- [x] `public/worker_portal/` 加入 .gitignore，deploy 脚本增加 worker_portal build ✓

**worker_portal 本地开发**：首次 clone 或 pull 后需执行 `cd cos/worker_portal && npm install && npm run build` 生成构建产物。

---

## 四、回滚与验证

- **回滚**：git revert 对应提交
- **验证**：
  - `bench migrate` 无报错
  - Balance Sheet China 报表可正常打开
  - worker_portal 页面可访问（若改动 public/worker_portal）
