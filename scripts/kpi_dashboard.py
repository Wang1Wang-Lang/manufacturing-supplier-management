# -*- coding: utf-8 -*-
"""采购 KPI 与支出集中度分析（纯标准库）。

用法：
  支出集中度：
    python kpi_dashboard.py concentration --batch spend.csv --out kpi.md
    CSV 列：supplier,amount
  降本测算：
    python kpi_dashboard.py costdown --batch items.csv --out cd.md
    CSV 列：item,baseline,current,qty

输出：HHI 指数、最大供应商占比、供应商数、单源/高集中预警；降本总额与降本率。
"""
import argparse, csv, math


def cmd_concentration(a):
    total = 0.0
    spend = {}
    with open(a.batch, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            sup = r.get("supplier") or r.get("供应商") or "(未命名)"
            try:
                amt = float(r.get("amount") or r.get("金额") or 0)
            except ValueError:
                continue
            spend[sup] = spend.get(sup, 0.0) + amt
            total += amt
    if total <= 0:
        print("无有效支出数据"); return
    shares = {s: v / total for s, v in spend.items()}
    hhi = sum(sh * sh for sh in shares.values())
    top1 = max(shares.values())
    n = len(spend)
    single_src = sum(1 for s, v in spend.items() if v == total)  # 唯一供应商
    lines = ["# 支出集中度分析", "",
             f"- 支出总额：{total:,.2f}",
             f"- 供应商数：{n}",
             f"- HHI 指数：{hhi:.4f}  （>0.25 预警）",
             f"- 最大供应商占比：{top1*100:.1f}%",
             f"- 单源（唯一供应商）数：{single_src}"]
    if hhi > 0.25:
        lines.append("⚠️ 支出高度集中（HHI>0.25），建议开发备选/引入竞争。")
    if top1 >= 0.5:
        lines.append("⚠️ 单一供应商占比≥50%，存在单源风险，须有备选或应急方案。")
    # 明细
    lines += ["", "| 供应商 | 金额 | 占比 |", "|---|---|---|"]
    for s, v in sorted(spend.items(), key=lambda x: -x[1]):
        lines.append(f"| {s} | {v:,.2f} | {shares[s]*100:.1f}% |")
    out = "\n".join(lines)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(out); print(f"已写出：{a.out}")
    else:
        print(out)


def cmd_costdown(a):
    total_base = 0.0
    total_cur = 0.0
    lines = ["# 降本测算", "", "| 物料 | 基准单价 | 当前单价 | 数量 | 节降额 |", "|---|---|---|---|---|"]
    with open(a.batch, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            try:
                b = float(r.get("baseline") or r.get("基准") or 0)
                c = float(r.get("current") or r.get("当前") or 0)
                q = float(r.get("qty") or r.get("数量") or 0)
            except ValueError:
                continue
            save = (b - c) * q
            total_base += b * q
            total_cur += c * q
            lines.append(f"| {r.get('item') or r.get('物料')} | {b} | {c} | {q} | {save:,.2f} |")
    total_save = total_base - total_cur
    rate = (total_save / total_base * 100) if total_base else 0
    lines += ["", f"- 基线金额：{total_base:,.2f}",
              f"- 当前金额：{total_cur:,.2f}",
              f"- **节降总额：{total_save:,.2f}（{rate:.1f}%）**"]
    out = "\n".join(lines)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(out); print(f"已写出：{a.out}")
    else:
        print(out)


def main():
    p = argparse.ArgumentParser(description="采购 KPI 与降本分析")
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("concentration", help="支出集中度")
    c.add_argument("--batch", required=True); c.add_argument("--out", default="")
    d = sub.add_parser("costdown", help="降本测算")
    d.add_argument("--batch", required=True); d.add_argument("--out", default="")
    args = p.parse_args()
    if args.cmd == "concentration":
        cmd_concentration(args)
    elif args.cmd == "costdown":
        cmd_costdown(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
