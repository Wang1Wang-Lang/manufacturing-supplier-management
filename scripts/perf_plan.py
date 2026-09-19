# -*- coding: utf-8 -*-
"""
制造业供应商绩效与配额辅助：评分定级 / 配额分配 / PIP 改进计划
纯标准库，无第三方依赖。

子命令：
  grade   输入 Q/C/D/S 四维 1-5 分，输出加权综合分(100)与等级(A/B/C/D)
  quota  输入若干 供应商:等级，按等级归一化分配采购配额(%)，并给角色
  pip    输入问题清单 CSV，生成 PIP 改进计划 markdown 表

示例：
  python perf_plan.py grade --q 5 --c 4 --d 5 --s 4
  python perf_plan.py quota --grades "供应商A:A,供应商B:B,供应商C:C,供应商D:D"
  python perf_plan.py quota --batch grades.csv --out quota.md
  python perf_plan.py pip --batch issues.csv --out pip.md
"""
import argparse
import csv
import sys

# 评分权重（绩效阶段：质量/成本/交付/服务）
W = {'q': 0.30, 'c': 0.20, 'd': 0.25, 's': 0.25}
BASE_SHARE = {'A': 50, 'B': 30, 'C': 15, 'D': 0}
ROLE = {'A': '战略/优选', 'B': '合格', 'C': '限制(帮扶)', 'D': '淘汰'}


def grade(q, c, d, s):
    for name, v in (('q', q), ('c', c), ('d', d), ('s', s)):
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = 0.0
        if v < 1 or v > 5:
            raise ValueError(f'{name} 评分需在 1~5 之间，收到: {v}')
        locals()[name] = v
    # 用字典安全取值（避免 locals 写入限制）
    qv, cv, dv, sv = float(q), float(c), float(d), float(s)
    score = (qv * W['q'] + cv * W['c'] + dv * W['d'] + sv * W['s']) * 20
    g = 'A' if score >= 85 else ('B' if score >= 70 else ('C' if score >= 60 else 'D'))
    return round(score, 1), g


def role_of(g):
    return ROLE.get(g, '未知')


def quota(suppliers):
    """suppliers: list of (name, grade). 返回 list of (name, grade, role, share%)"""
    raw = [BASE_SHARE.get(g, 0) for _, g in suppliers]
    total = sum(raw)
    out = []
    for (name, g), r in zip(suppliers, raw):
        share = round(r / total * 100, 1) if total else 0.0
        out.append((name, g, role_of(g), share))
    return out


def render_quota(suppliers, title='采购配额分配'):
    res = quota(suppliers)
    s = sum(x[3] for x in res)
    lines = [f'## {title}', '',
             '| 供应商 | 等级 | 角色 | 建议份额(%) |', '|---|---|---|---|']
    for name, g, role, share in res:
        lines.append(f'| {name} | {g} | {role} | {share} |')
    lines.append(f'| **合计** | — | — | **{round(s,1)}** |')
    if abs(s - 100) > 0.5:
        lines.append('')
        lines.append('⚠️ 合计非 100%，请按角色（A≈主供/战略、B≈备选、C≤15%、D=0）微调至 100%。')
    return '\n'.join(lines)


def render_pip(rows):
    lines = ['## PIP 改进计划', '',
             '| 编号 | 供应商 | 问题/短板 | 根因 | 改进措施 | 责任 | 计划完成 | 状态 |',
             '|---|---|---|---|---|---|---|---|']
    for i, r in enumerate(rows, 1):
        lines.append(
            f'| PIP-{i:03d} | {r.get("供应商","")} | {r.get("问题","")} | '
            f'{r.get("根因","")} | {r.get("措施","")} | {r.get("责任","")} | '
            f'{r.get("计划完成","")} | {r.get("状态","进行中")} |')
    return '\n'.join(lines)


def cmd_grade(args):
    score, g = grade(args.q, args.c, args.d, args.s)
    print(f'综合得分：{score} / 100')
    print(f'等级：{g}（{role_of(g)}）')
    if g == 'D':
        print('⚠️ D 级：启动淘汰或帮扶，并寻找替代源。')
    elif g == 'C':
        print('⚠️ C 级：发黄牌，须制定 PIP 改进计划。')


def cmd_quota(args):
    if args.batch:
        out = []
        with open(args.batch, encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                name = row.get('name') or row.get('供应商') or '(未命名)'
                g = row.get('grade') or row.get('等级') or ''
                out.append((name, g.strip().upper()))
        text = render_quota(out) + '\n'
        if args.out:
            with open(args.out, 'w', encoding='utf-8') as fo:
                fo.write(text)
            print(f'已写入 {args.out}')
        else:
            print(text)
        return
    suppliers = []
    for item in (args.grades or '').split(','):
        if ':' in item:
            n, g = item.split(':', 1)
            suppliers.append((n.strip(), g.strip().upper()))
    print(render_quota(suppliers))


def cmd_pip(args):
    rows = []
    with open(args.batch, encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            rows.append(row)
    text = render_pip(rows) + '\n'
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as fo:
            fo.write(text)
        print(f'已写入 {args.out}')
    else:
        print(text)


def main():
    p = argparse.ArgumentParser(description='供应商绩效评分 / 配额分配 / PIP 改进计划')
    sub = p.add_subparsers(dest='cmd', required=True)

    pg = sub.add_parser('grade', help='四维评分定级')
    pg.add_argument('--q', required=True, help='质量分 1-5')
    pg.add_argument('--c', required=True, help='成本分 1-5')
    pg.add_argument('--d', required=True, help='交付分 1-5')
    pg.add_argument('--s', required=True, help='服务分 1-5')
    pg.set_defaults(func=cmd_grade)

    pq = sub.add_parser('quota', help='配额分配')
    pq.add_argument('--grades', help='"供应商A:A,供应商B:B"')
    pq.add_argument('--batch', help='CSV（name/供应商, grade/等级）')
    pq.add_argument('--out', help='输出 markdown')
    pq.set_defaults(func=cmd_quota)

    pp = sub.add_parser('pip', help='PIP 改进计划')
    pp.add_argument('--batch', required=True, help='CSV（供应商,问题,根因,措施,责任,计划完成,状态）')
    pp.add_argument('--out', help='输出 markdown')
    pp.set_defaults(func=cmd_pip)

    args = p.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
