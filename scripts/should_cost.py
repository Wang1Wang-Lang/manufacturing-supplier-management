# -*- coding: utf-8 -*-
"""
制造业采购辅助：Should-Cost 成本拆解 + 招投标方式推荐
纯标准库，无第三方依赖。

子命令：
  cost    计算目标成本(Should-Cost)并对比供应商报价，给出差异率与预警
  tender  依据品类定位与商务条件推荐招投标方式

示例：
  python should_cost.py cost --elements "直接材料:1200,直接人工:300,制造费用:200,专项费用:150,管理费:200,利润:250" --quote 2300
  python should_cost.py cost --batch bom.csv --out cost_result.md
  python should_cost.py tender --position 杠杆型 --amount 80 --suppliers 4 --urgency 中
  python should_cost.py tender --batch tender.csv --out tender_result.md
"""
import argparse
import csv
import sys

# 推荐方式判定（与 SKILL.md / 模板 xlsx 公式逻辑保持一致）
def recommend_tender(position, amount, suppliers, urgency):
    position = (position or '').strip()
    urgency = (urgency or '').strip()
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0
    try:
        suppliers = int(suppliers)
    except (TypeError, ValueError):
        suppliers = 0

    if suppliers == 1:
        method = '单一来源'
        reason = '可选供应商仅 1 家，缺乏竞争，按单一来源采购（须做成本与合规审查）'
    elif urgency == '高':
        if suppliers >= 2:
            method = '竞争性谈判'
            reason = '紧急度高且有 ≥2 家可选，采用竞争性谈判快速定标'
        else:
            method = '单一来源'
            reason = '紧急但无竞争，单一来源（应急）'
    elif position == '战略型':
        method = '公开招标'
        reason = '战略型品类，需最大化竞争与透明，公开招标'
    elif position == '杠杆型' and amount >= 50:
        method = '邀请招标'
        reason = '杠杆型且金额≥50万，邀请招标平衡效率与竞争'
    elif position == '瓶颈型':
        method = '竞争性谈判'
        reason = '瓶颈型供应受限，以谈判锁定供应与条件'
    elif position == '非关键型' and amount < 50:
        method = '询价'
        reason = '非关键型且金额<50万，直接询价比价'
    else:
        method = '邀请招标'
        reason = '默认采用邀请招标（竞争适度、效率较高）'
    return method, reason


def cmd_tender(args):
    if args.batch:
        out = []
        with open(args.batch, encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                name = row.get('name') or row.get('品类') or '(未命名)'
                m, r = recommend_tender(row.get('position') or row.get('定位'),
                                        row.get('amount') or row.get('金额'),
                                        row.get('suppliers') or row.get('供应商数'),
                                        row.get('urgency') or row.get('紧急'))
                out.append(f"- **{name}** → {m}\n  - 理由：{r}")
        text = '## 招投标方式推荐（批量）\n\n' + '\n'.join(out) + '\n'
        if args.out:
            with open(args.out, 'w', encoding='utf-8') as fo:
                fo.write(text)
            print(f'已写入 {args.out}')
        else:
            print(text)
        return

    m, r = recommend_tender(args.position, args.amount, args.suppliers, args.urgency)
    print(f'推荐方式：{m}')
    print(f'选择理由：{r}')


def calc_should_cost(elements, quote=None):
    """elements: list of (name, amount). 返回 (should_total, breakdown)"""
    total = 0.0
    breakdown = []
    for name, amt in elements:
        try:
            amt = float(amt)
        except (TypeError, ValueError):
            amt = 0.0
        total += amt
        breakdown.append((name, amt))
    return total, breakdown


def parse_elements(s):
    """'直接材料:1200,直接人工:300' -> [('直接材料',1200), ...]"""
    out = []
    for part in s.split(','):
        if ':' in part:
            name, val = part.split(':', 1)
            out.append((name.strip(), val.strip()))
        elif part.strip():
            out.append((part.strip(), 0.0))
    return out


def cmd_cost(args):
    if args.batch:
        out = []
        with open(args.batch, encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                name = row.get('name') or row.get('品类') or '(未命名)'
                els = []
                for k, v in row.items():
                    if k in ('name', '品类', 'quote', '报价') or not v:
                        continue
                    els.append((k, v))
                q = row.get('quote') or row.get('报价') or None
                quote = float(q) if q not in (None, '') else None
                out.append(render_cost(name, els, quote))
        text = '## Should-Cost 成本拆解（批量）\n\n' + '\n\n'.join(out) + '\n'
        if args.out:
            with open(args.out, 'w', encoding='utf-8') as fo:
                fo.write(text)
            print(f'已写入 {args.out}')
        else:
            print(text)
        return

    elements = parse_elements(args.elements or '')
    quote = float(args.quote) if args.quote else None
    print(render_cost('单条计算', elements, quote))


def render_cost(name, elements, quote):
    if quote is not None:
        try:
            quote = float(quote)
        except (TypeError, ValueError):
            quote = None
    total, breakdown = calc_should_cost(elements)
    lines = [f'### {name}', '', '| 成本要素 | 金额(元) | 占比 |', '|---|---|---|']
    for n, a in breakdown:
        pct = (a / total * 100) if total else 0
        lines.append(f'| {n} | {a:,.2f} | {pct:.1f}% |')
    lines.append(f'| **Should-Cost 合计** | **{total:,.2f}** | 100.0% |')
    if quote is not None:
        diff = quote - total
        rate = (diff / total * 100) if total else 0
        level = '🟢 合理' if rate < 5 else ('🟡 偏高' if rate <= 15 else '🔴 严重偏高')
        lines.append('')
        lines.append(f'- 供应商报价：**{quote:,.2f} 元**')
        lines.append(f'- 绝对差异：{diff:,.2f} 元')
        lines.append(f'- 差异率：**{rate:+.1f}%**  {level}')
        if rate >= 15:
            lines.append('- ⚠️ 报价高于 Should-Cost 15% 以上，建议要求供应商拆分报价、谈判或引入备选。')
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description='Should-Cost 成本拆解与招投标方式推荐')
    sub = p.add_subparsers(dest='cmd', required=True)

    pc = sub.add_parser('cost', help='成本拆解与报价对比')
    pc.add_argument('--elements', help='成本要素串，如 "直接材料:1200,直接人工:300"')
    pc.add_argument('--quote', help='供应商实际报价(元)')
    pc.add_argument('--batch', help='批量 CSV（含 name/各要素列/quote 列）')
    pc.add_argument('--out', help='输出 markdown 路径')
    pc.set_defaults(func=cmd_cost)

    pt = sub.add_parser('tender', help='招投标方式推荐')
    pt.add_argument('--position', help='Kraljic 定位：战略型/杠杆型/瓶颈型/非关键型')
    pt.add_argument('--amount', help='预估金额(万元)')
    pt.add_argument('--suppliers', help='可选供应商数量')
    pt.add_argument('--urgency', help='紧急程度：高/中/低')
    pt.add_argument('--batch', help='批量 CSV（含 name/position/amount/suppliers/urgency）')
    pt.add_argument('--out', help='输出 markdown 路径')
    pt.set_defaults(func=cmd_tender)

    args = p.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
