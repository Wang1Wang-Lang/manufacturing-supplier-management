# manufacturing-supplier-management

面向制造业采购/供应链的 **供应商管理专家技能（Agent Skill）**。把"选、评、比、查、管、执行、合规"做成可量化、可归档的本地闭环工具，输出统一固定表格模板，不靠感觉。

## 覆盖的十一步闭环

| # | 工作流 | 关键产出 |
|---|---|---|
| 1 | 品类策略（Kraljic） | 战略/杠杆/瓶颈/非关键型定位与差异化策略 |
| 2 | 供应商准入 | 资质合规一票否决 + 四维打分定级（A/B/C/D） |
| 3 | 供应商评估 | 质量/产能/交付/成本四维加权 100 分制 |
| 4 | 采购比价 | 加权单价 = 含税单价 ÷ 质量系数，综合排名 |
| 5 | 招投标与成本拆解 | 招投标方式推荐 + Should-Cost 差异率预警 |
| 6 | 绩效分级与配额 | 等级→角色→归一化份额 + PIP 改进闭环 |
| 7 | 公开风险核查 | 12 项公开风险核查清单 + 搜索词 |
| 8 | 持续风险监控 | 风险台账 + 过期(>90天)重查提醒 + 汇总看板 |
| 9 | 采购执行闭环 | PR→PO→收货→IQC→三单匹配，异常/延迟/不良率 |
| 10 | 合规审批与 KPI | 审批授权矩阵 + HHI 集中度/降本 KPI 看板 |
| 11 | 数据接入适配 | ERP/SRM 导出标准化为内部字段（离线） |

## 目录结构

```
manufacturing-supplier-management/
├── SKILL.md                    # 技能定义：触发词 / 工作流 / 输出纪律
├── references/                 # 8 个固定表格模板（xlsx）
│   ├── 供应商管理表格模板.xlsx
│   ├── 品类策略模板.xlsx
│   ├── 招标比价与成本拆解模板.xlsx
│   ├── 绩效配额与改进模板.xlsx
│   ├── 风险监控台账.xlsx
│   ├── 采购执行闭环.xlsx
│   ├── 合规审批与KPI.xlsx
│   └── 数据接入适配.xlsx
└── scripts/                    # 8 个纯标准库辅助脚本
    ├── risk_check.py           # 公开风险核查清单生成
    ├── kraljic_classify.py     # 品类 Kraljic 定位
    ├── should_cost.py          # Should-Cost 拆解 + 招投标推荐
    ├── perf_plan.py            # 绩效分级 / 配额 / PIP
    ├── risk_monitor.py         # 持续风险监控台账
    ├── po_tracker.py           # 三单匹配 / 交付
    ├── kpi_dashboard.py        # 集中度 HHI / 降本 KPI
    └── import_adapter.py       # ERP/SRM 数据标准化
```

## 安装

将整个目录复制到 Agent 技能的加载路径，例如：

- 用户级：`~/.workbuddy/skills/manufacturing-supplier-management/`
- 项目级：`<项目>/.workbuddy/skills/manufacturing-supplier-management/`

技能被触发后，会优先调用 `references/` 下的表格模板与 `scripts/` 下的脚本。

## 脚本用法（均仅依赖 Python 标准库，无需 pip install）

```bash
# 品类定位
python kraljic_classify.py --spend 1200 --risk 高
python kraljic_classify.py --batch categories.csv --out result.md

# Should-Cost / 招投标
python should_cost.py cost --elements "直接材料:1200,直接人工:300,制造费用:200,专项费用:150,管理费:200,利润:250" --quote 2300
python should_cost.py tender --position 杠杆型 --amount 80 --suppliers 3 --urgency 低

# 绩效 / 配额 / PIP
python perf_plan.py grade --q 5 --c 4 --d 5 --s 4
python perf_plan.py quota --grades "供应商A:A,供应商B:B,供应商C:C,供应商D:D"
python perf_plan.py pip --batch issues.csv --out pip.md

# 风险核查 / 监控
python risk_check.py --name "供应商全称"
python risk_monitor.py batch --batch ledger.csv --out dashboard.md

# 执行闭环 / KPI / 数据接入
python po_tracker.py match --batch gr.csv --out match.md
python kpi_dashboard.py concentration --batch spend.csv --out kpi.md
python import_adapter.py validate --file erp.csv
python import_adapter.py normalize --file erp.csv --out std.csv
```

## 说明与边界

- **离线工具**：脚本本身不联网；"风险核查""持续监控"需由 Agent 按脚本产出的搜索词执行 WebSearch 回填。
- **数据接入为离线适配层**：`import_adapter.py` 把 ERP/SRM 导出 CSV/JSON 标准化，不直连系统。
- 所有 xlsx 模板含公式、下拉校验与条件格式，可直接维护或二次开发。

## License

MIT（可自由使用、修改、再分发）。
