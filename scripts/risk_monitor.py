# -*- coding: utf-8 -*-
"""持续风险监控辅助脚本（纯标准库）。

用法：
  单条：
    python risk_monitor.py --supplier "某公司" --date 2026-05-01 --result 低 --item "经营异常" --source "公示系统"
  批量（CSV 台账）：
    python risk_monitor.py --batch ledger.csv --out dashboard.md

CSV 台账列（含表头）：supplier,item,last_check_date,result,source
  result 取值：无/低/中/高
说明：脚本不联网，仅按台账计算时效与汇总；实际核查仍由 Agent 用 WebSearch 回填。
"""
import argparse, csv, sys, datetime

SEV = {"无": 0, "低": 1, "中": 2, "高": 3}
STALE_DAYS = 90


def days_since(dstr):
    try:
        d = datetime.datetime.strptime(dstr.strip(), "%Y-%m-%d").date()
    except Exception:
        return None
    return (datetime.date.today() - d).days


def need_recheck(days):
    return days is not None and days > STALE_DAYS


def overall(sevs):
    if not sevs:
        return "低风险"
    m = max(sevs)
    return {3: "高风险", 2: "中风险", 1: "低风险", 0: "低风险"}[m]


def render_single(supplier, item, date, result, source=""):
    days = days_since(date)
    nr = "是" if need_recheck(days) else ("否" if days is not None else "未知")
    return (f"- 供应商：{supplier}\n"
            f"  - 监控项：{item or '(未指定)'}\n"
            f"  - 最近核查：{date}（{days} 天前）\n"
            f"  - 核查结果：{result}\n"
            f"  - 信息来源：{source or '(未填)'}\n"
            f"  - 需重查(>90天)：{nr}")


def cmd_single(a):
    print(render_single(a.supplier, a.item, a.date, a.result, a.source))


def cmd_batch(a):
    rows = []
    with open(a.batch, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    # 逐行明细
    lines = ["# 供应商风险监控明细", "", "| 供应商 | 监控项 | 最近核查 | 距今天数 | 结果 | 需重查 | 来源 |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        sup = r.get("supplier") or r.get("供应商") or ""
        item = r.get("item") or r.get("监控项") or ""
        dstr = r.get("last_check_date") or r.get("最近核查日期") or ""
        res = r.get("result") or r.get("核查结果") or ""
        src = r.get("source") or r.get("来源") or ""
        days = days_since(dstr)
        nr = "是" if need_recheck(days) else ("否" if days is not None else "未知")
        lines.append(f"| {sup} | {item} | {dstr} | {days} | {res} | {nr} | {src} |")
    # 汇总
    agg = {}
    for r in rows:
        sup = r.get("supplier") or r.get("供应商") or "(未命名)"
        res = r.get("result") or r.get("核查结果") or "无"
        agg.setdefault(sup, []).append(SEV.get(res, 0))
    lines += ["", "# 供应商风险汇总", "", "| 供应商 | 高风险项 | 中风险项 | 整体状态 |", "|---|---|---|---|"]
    for sup, sevs in agg.items():
        hi = sum(1 for s in sevs if s == 3)
        md = sum(1 for s in sevs if s == 2)
        lines.append(f"| {sup} | {hi} | {md} | {overall(sevs)} |")
    out = "\n".join(lines)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"已写出：{a.out}")
    else:
        print(out)


def main():
    p = argparse.ArgumentParser(description="供应商持续风险监控")
    sub = p.add_subparsers(dest="cmd")
    s1 = sub.add_parser("single", help="单条录入示例")
    s1.add_argument("--supplier", required=True)
    s1.add_argument("--date", required=True, help="YYYY-MM-DD")
    s1.add_argument("--result", required=True, choices=["无", "低", "中", "高"])
    s1.add_argument("--item", default="")
    s1.add_argument("--source", default="")
    s2 = sub.add_parser("batch", help="批量台账→看板")
    s2.add_argument("--batch", required=True)
    s2.add_argument("--out", default="")
    args = p.parse_args()
    if args.cmd == "single":
        cmd_single(args)
    elif args.cmd == "batch":
        cmd_batch(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
