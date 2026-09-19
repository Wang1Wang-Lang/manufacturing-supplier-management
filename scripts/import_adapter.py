# -*- coding: utf-8 -*-
"""ERP/SRM 数据接入适配器（纯标准库，离线）。

把 ERP/SRM/WMS/QMS 导出的 CSV 按『数据接入适配.xlsx』映射规范标准化为内部字段，
供 po_tracker / kpi_dashboard / risk_monitor 等脚本直接消费。

用法：
  校验 + 标准化：
    python import_adapter.py normalize --file erp.csv --out std.csv
  仅校验列：
    python import_adapter.py validate --file erp.csv
  支持 JSON：
    python import_adapter.py normalize --file erp.json --out std.csv

映射表（CSV 导出列名 → 内部字段）：键为「常见导出列名」，命中任一即映射。
"""
import argparse, csv, json, sys

# 内部字段及类型
FIELDS = ["po_no", "supplier", "material", "qty", "unit_price",
          "po_amount", "plan_date", "actual_date", "recv_qty", "ok_qty",
          "invoice_amount", "credit_code"]

# 导出列名 → 内部字段（模糊匹配，小写去空格）
MAP = {
    "采购订单号": "po_no", "订单号": "po_no", "po_no": "po_no", "pono": "po_no",
    "供应商名称": "supplier", "供应商": "supplier", "supplier": "supplier",
    "物料编码": "material", "物料": "material", "material": "material",
    "订单数量": "qty", "数量": "qty", "qty": "qty",
    "单价": "unit_price", "unit_price": "unit_price",
    "订单金额": "po_amount", "金额": "po_amount", "po_amount": "po_amount",
    "计划到货日": "plan_date", "计划到货": "plan_date", "plan_date": "plan_date",
    "实际到货日": "actual_date", "实际到货": "actual_date", "actual_date": "actual_date",
    "收货数量": "recv_qty", "收货": "recv_qty", "recv_qty": "recv_qty",
    "合格数量": "ok_qty", "合格": "ok_qty", "ok_qty": "ok_qty",
    "发票金额": "invoice_amount", "invoice_amount": "invoice_amount",
    "统一信用代码": "credit_code", "信用代码": "credit_code", "credit_code": "credit_code",
}

REQUIRED = ["po_no", "supplier", "qty"]


def norm_key(k):
    return (k or "").strip().lower().replace(" ", "")


def read_rows(path):
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("rows", data.get("data", []))
        return [{str(k): v for k, v in row.items()} for row in data]
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def adapt(rows):
    out = []
    unmapped_warn = False
    for row in rows:
        new = {f: "" for f in FIELDS}
        for k, v in row.items():
            key = norm_key(k)
            if key in MAP:
                new[MAP[key]] = v
            elif key not in ("",):
                unmapped_warn = True
        # 派生：po_amount = qty*unit_price（若缺失）
        try:
            if not new["po_amount"]:
                q = float(new["qty"] or 0); p = float(new["unit_price"] or 0)
                if q and p:
                    new["po_amount"] = f"{q*p:.2f}"
        except ValueError:
            pass
        out.append(new)
    return out, unmapped_warn


def cmd_validate(a):
    rows = read_rows(a.file)
    if not rows:
        print("空文件或无数据"); return
    cols = set()
    for r in rows:
        cols.update(norm_key(k) for k in r.keys())
    present = {MAP[c] for c in cols if c in MAP}
    missing = [f for f in REQUIRED if f not in present]
    print(f"读取 {len(rows)} 行；识别内部字段：{sorted(present)}")
    if missing:
        print(f"❌ 缺少必填字段：{missing}")
        sys.exit(1)
    print("✅ 必填字段齐全，可通过 normalize 标准化。")


def cmd_normalize(a):
    rows = read_rows(a.file)
    out, warn = adapt(rows)
    with open(a.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in out:
            w.writerow(r)
    print(f"已标准化写出：{a.out}（{len(out)} 行）")
    if warn:
        print("⚠️ 存在未识别的列名，已忽略（详见映射规范表）。")


def main():
    p = argparse.ArgumentParser(description="ERP/SRM 数据接入适配器")
    sub = p.add_subparsers(dest="cmd")
    v = sub.add_parser("validate", help="校验导出列")
    v.add_argument("--file", required=True)
    n = sub.add_parser("normalize", help="标准化为内部格式")
    n.add_argument("--file", required=True); n.add_argument("--out", required=True)
    args = p.parse_args()
    if args.cmd == "validate":
        cmd_validate(args)
    elif args.cmd == "normalize":
        cmd_normalize(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
