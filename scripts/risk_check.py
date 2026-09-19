# -*- coding: utf-8 -*-
"""
制造业供应商公开风险核查辅助脚本（仅依赖 Python 标准库）。

作用：
    输入供应商名称（及统一社会信用代码），生成「公开风险核查搜索词清单」与
    「空白风险核查表(markdown)」。实际联网核查由 Agent 按输出的搜索词逐项执行
    WebSearch，并把结果回填到核查表中。

用法一（单条）：
    python risk_check.py --name "东莞市精成精密模具有限公司" [--credit-code "91441900MAxxxxxxx"]

用法二（批量，读 CSV 输出 markdown）：
    python risk_check.py --batch suppliers.csv --out risk_queries.md
    CSV 表头须含：name[, credit_code]

判定规则（供回填参考）：
    高风险(一票否决)：失信被执行人、限制消费令、破产、股权冻结、重大行政处罚
    中风险：经营异常、多起买卖纠纷、劳动仲裁、欠税
    低风险：零星纠纷、已整改的异常
    无风险：以上均查无
"""

import argparse
import csv
import sys

# 标准核查项：(核查项, 信息来源, 关键词模板)
CHECK_ITEMS = [
    ("失信被执行人", "中国执行信息公开网", "{name} 失信被执行人"),
    ("限制消费令", "中国执行信息公开网", "{name} 限制消费令"),
    ("经营异常名录", "国家企业信用信息公示系统", "{name} 经营异常名录"),
    ("行政处罚", "信用中国 / 市场监管", "{name} 行政处罚"),
    ("股权冻结 / 司法冻结", "企查查 / 天眼查 / 裁判文书网", "{name} 股权冻结 司法冻结"),
    ("裁判文书(买卖纠纷)", "中国裁判文书网", "{name} 裁判文书 买卖合同纠纷"),
    ("破产重整 / 清算", "全国企业破产重整案件信息网", "{name} 破产重整 破产清算"),
    ("环保 / 安全生产处罚", "信用中国 / 生态环境局", "{name} 环保处罚 安全生产处罚"),
    ("欠税公告", "国家税务总局", "{name} 欠税公告"),
    ("劳动仲裁 / 社保欠缴", "裁判文书网 / 人社局", "{name} 劳动仲裁 社保欠缴"),
    ("招投标黑名单", "信用中国 / 公共资源交易", "{name} 招投标 黑名单"),
    ("重大负面舆情", "综合搜索", "{name} 负面舆情 跑路 停工"),
]

HIGH_RISK = ("失信被执行人", "限制消费令", "破产重整 / 清算", "股权冻结 / 司法冻结", "环保 / 安全生产处罚")  # 高风险（一票否决）


def build_queries(name: str, credit_code: str = "") -> list:
    out = []
    for item, src, kw_tpl in CHECK_ITEMS:
        kw = kw_tpl.format(name=name)
        if credit_code:
            kw += f" {credit_code}"
        out.append((item, src, kw))
    return out


def render_single(name: str, credit_code: str = "") -> str:
    lines = []
    lines.append(f"# 供应商公开风险核查表 —— {name}")
    if credit_code:
        lines.append(f"> 统一社会信用代码：{credit_code}")
    lines.append("")
    lines.append("## 一、待执行搜索词清单（逐项用 WebSearch 核查）")
    lines.append("")
    for i, (item, src, kw) in enumerate(build_queries(name, credit_code), 1):
        lines.append(f"{i}. **{item}**（来源：{src}）")
        lines.append(f"   - 搜索词：`{kw}`")
    lines.append("")
    lines.append("## 二、风险核查表（WebSearch 结果回填）")
    lines.append("")
    lines.append("| 核查项 | 信息来源 | 查询关键词 | 核查结果(无/有) | 风险等级(无/低/中/高) | 详情/链接 | 核查日期 |")
    lines.append("|---|---|---|---|---|---|---|")
    for item, src, kw in build_queries(name, credit_code):
        lines.append(f"| {item} | {src} | {kw} |  |  |  |  |")
    lines.append("")
    lines.append("## 三、综合判定")
    lines.append("")
    lines.append("- 高风险项（一票否决）：" + " / ".join(HIGH_RISK))
    lines.append("- 中风险项：经营异常 / 多起买卖纠纷 / 劳动仲裁 / 欠税")
    lines.append("- 低风险项：零星纠纷 / 已整改异常")
    lines.append("- 无风险：以上均查无")
    lines.append("")
    lines.append(f"> 核查日期：____ ｜ 信息来源：公开网络检索 ｜ 陈旧信息(>90天)需重新核查")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="制造业供应商公开风险核查辅助脚本")
    ap.add_argument("--name", help="供应商全称")
    ap.add_argument("--credit-code", default="", help="统一社会信用代码（可选，提升检索精度）")
    ap.add_argument("--batch", help="批量模式：供应商 CSV 路径（表头含 name[,credit_code]）")
    ap.add_argument("--out", help="批量模式输出 markdown 文件路径")
    args = ap.parse_args()

    if args.batch:
        try:
            with open(args.batch, encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                blocks = []
                for row in reader:
                    nm = (row.get("name") or "").strip()
                    if not nm:
                        continue
                    cc = (row.get("credit_code") or row.get("credit") or "").strip()
                    blocks.append(render_single(nm, cc))
                md = "\n\n---\n\n".join(blocks)
        except FileNotFoundError:
            sys.stderr.write(f"找不到文件：{args.batch}\n")
            sys.exit(1)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"已写出：{args.out}（含 {len(blocks)} 家供应商核查清单）")
        else:
            print(md)
        return

    if not args.name:
        sys.stderr.write("单条模式需提供 --name；批量模式需提供 --batch。\n")
        sys.exit(1)

    print(render_single(args.name, args.credit_code or ""))


if __name__ == "__main__":
    main()
