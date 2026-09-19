# -*- coding: utf-8 -*-
"""
品类 Kraljic 定位分类辅助脚本（纯标准库，无第三方依赖）

功能：
  输入品类的「年采购金额」与「供应风险(高/低)」，输出 Kraljic 定位与对应的标准采购策略。
  支持单条(--spend / --risk)与批量(--batch CSV -> --out)。

Kraljic 二维模型：
  X 轴 = 采购金额（高 / 低）
  Y 轴 = 供应风险（高 / 低：稀缺性、替代难度、供应商集中度、断料影响）
  四象限：
    战略型 Strategic    : 金额高 + 风险高
    杠杆型 Leverage     : 金额高 + 风险低
    瓶颈型 Bottleneck   : 金额低 + 风险高
    非关键型 Non-critical: 金额低 + 风险低

用法：
  python kraljic_classify.py --spend 1200 --risk 高 [--threshold 500]
  python kraljic_classify.py --batch categories.csv --out result.md
  CSV 列：name,spend,risk[,threshold]  （risk 取值：高/低 或 high/low）
"""
import argparse
import csv
import sys

# 各定位对应的标准采购策略
STRATEGY = {
    "战略型": "建立战略伙伴关系、联合开发/VAVE、双源备份、高层定期回顾、JIT/VMI 协同",
    "杠杆型": "集中采购、招标比价压价、标准化、多家竞争、年降目标、合同价锁定期",
    "瓶颈型": "多源/替代料开发、安全库存、供应商扶持、长期保供协议、动态风险监控",
    "非关键型": "流程简化、系统/电商化采购、缩减供应商数、低管理成本、按需采购",
}


def classify(spend, risk, threshold):
    risk = "高" if str(risk).strip() in ("高", "high", "H", "1") else "低"
    amt = "高" if spend >= threshold else "低"
    if amt == "高" and risk == "高":
        return "战略型", amt, risk
    if amt == "高" and risk == "低":
        return "杠杆型", amt, risk
    if amt == "低" and risk == "高":
        return "瓶颈型", amt, risk
    return "非关键型", amt, risk


def render_single(name, spend, risk, threshold):
    pos, amt, rsk = classify(spend, risk, threshold)
    lines = []
    lines.append(f"## 品类：{name}")
    lines.append(f"- 年采购金额：{spend} 万元（阈值 {threshold} → 金额档：{amt}）")
    lines.append(f"- 供应风险：{rsk}")
    lines.append(f"- **Kraljic 定位：{pos}**")
    lines.append(f"- 推荐策略：{STRATEGY[pos]}")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Kraljic 品类定位分类")
    ap.add_argument("--name", default="(未命名品类)")
    ap.add_argument("--spend", type=float, help="年采购金额(万元)")
    ap.add_argument("--risk", help="供应风险: 高/低")
    ap.add_argument("--threshold", type=float, default=500, help="金额高/低判定阈值(万元), 默认500")
    ap.add_argument("--batch", help="批量 CSV 路径(name,spend,risk[,threshold])")
    ap.add_argument("--out", help="批量结果输出文件(.md)")
    args = ap.parse_args()

    if args.batch:
        out = []
        with open(args.batch, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                name = row.get("name") or row.get("品类") or "(未命名)"
                spend = float(row.get("spend") or row.get("年采购金额") or 0)
                risk = row.get("risk") or row.get("供应风险") or "低"
                thr = float(row.get("threshold") or row.get("阈值") or args.threshold)
                out.append(render_single(name, spend, risk, thr))
        text = "# Kraljic 品类定位批量结果\n\n" + "\n".join(out)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"已写出 {args.out}（{len(out)} 条）")
        else:
            print(text)
        return

    if args.spend is None or not args.risk:
        print("单条模式需同时提供 --spend 与 --risk，或用 --batch 批量。", file=sys.stderr)
        sys.exit(2)
    print(render_single(args.name, args.spend, args.risk, args.threshold))


if __name__ == "__main__":
    main()
