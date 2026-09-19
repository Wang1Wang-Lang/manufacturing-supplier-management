# -*- coding: utf-8 -*-
"""采购执行闭环辅助脚本（纯标准库）：三单匹配 + 交付/质量。

用法：
  三单匹配：
    python po_tracker.py match --batch gr.csv --out match.md
    CSV 列：po,recv_qty,unit_price,invoice_amount,tol
  交付与质量：
    python po_tracker.py delivery --batch del.csv --out del.md
    CSV 列：po,plan_date,actual_date,recv_qty,ok_qty

说明：数据来自 ERP/WMS/QMS 导出（经 import_adapter 标准化后喂入），脚本做校验与异常标注。
"""
import argparse, csv, sys, datetime


def parse_date(s):
    try:
        return datetime.datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def cmd_match(a):
    rows = []
    with open(a.batch, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    lines = ["# 三单匹配（PO × 收货 × 发票）", "",
             "| PO | 收货数量 | 单价 | 应付基准 | 发票金额 | 差异 | 容差 | 匹配状态 |",
             "|---|---|---|---|---|---|---|---|"]
    exceptions = 0
    for r in rows:
        po = r.get("po") or r.get("PO编号") or ""
        try:
            recv = float(r.get("recv_qty") or 0)
            price = float(r.get("unit_price") or 0)
            inv = float(r.get("invoice_amount") or 0)
            tol = float(r.get("tol") or 0.01)
        except ValueError:
            lines.append(f"| {po} | 数据错误 | | | | | | |")
            continue
        base = recv * price
        diff = inv - base
        status = "通过" if abs(diff) <= tol else "异常"
        if status == "异常":
            exceptions += 1
        lines.append(f"| {po} | {recv} | {price} | {base:.2f} | {inv:.2f} | {diff:.2f} | {tol} | {status} |")
    lines += ["" , f"**异常单数：{exceptions} / 共 {len(rows)} 单**"]
    if exceptions:
        lines.append("⚠️ 存在三单不匹配，需挂起付款并核对发票与收货记录。")
    out = "\n".join(lines)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(out); print(f"已写出：{a.out}")
    else:
        print(out)


def cmd_delivery(a):
    rows = []
    with open(a.batch, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    lines = ["# 交付与质量看板", "",
             "| PO | 计划到货 | 实际到货 | 准时 | 收货数 | 合格数 | 不良率 |",
             "|---|---|---|---|---|---|---|"]
    late = 0
    for r in rows:
        po = r.get("po") or r.get("PO编号") or ""
        pd = parse_date(r.get("plan_date") or "")
        ad = parse_date(r.get("actual_date") or "")
        try:
            recv = float(r.get("recv_qty") or 0)
            ok = float(r.get("ok_qty") or 0)
        except ValueError:
            lines.append(f"| {po} | {pd} | {ad} | | 数据错误 | | |"); continue
        on_time = "—" if (pd is None or ad is None) else ("准时" if ad <= pd else "延迟")
        if on_time == "延迟":
            late += 1
        defect = (1 - ok / recv) if recv else 0
        lines.append(f"| {po} | {pd} | {ad} | {on_time} | {recv} | {ok} | {defect*100:.1f}% |")
    lines += ["", f"**延迟单数：{late} / 共 {len(rows)} 单**"]
    out = "\n".join(lines)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(out); print(f"已写出：{a.out}")
    else:
        print(out)


def main():
    p = argparse.ArgumentParser(description="采购执行闭环：三单匹配/交付质量")
    sub = p.add_subparsers(dest="cmd")
    m = sub.add_parser("match", help="三单匹配")
    m.add_argument("--batch", required=True); m.add_argument("--out", default="")
    d = sub.add_parser("delivery", help="交付与质量")
    d.add_argument("--batch", required=True); d.add_argument("--out", default="")
    args = p.parse_args()
    if args.cmd == "match":
        cmd_match(args)
    elif args.cmd == "delivery":
        cmd_delivery(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
