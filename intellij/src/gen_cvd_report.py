#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
色觉缺陷（CVD）报告：列出正常色觉可分、但红/绿色盲模拟下塌陷的 token 配对。

报告项，不判失败 —— 官方靠发布 deuteranopia / protanopia 变体解决，
本项目暂未提供变体；这张表是后续设计变体的依据。
"""
import argparse
import datetime
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
sys.path.insert(0, str(ROOT / "shared" / "tools"))

from colorlib import de2000, simulate_cvd  # noqa: E402

PALETTE = ROOT / "shared" / "palette.json"
DEFAULT_OUT = INTELLIJ / "build" / "ref" / "cvd-report.md"
TOKENS = ["fg", "comment", "doc_comment", "keyword", "string", "number",
          "function", "constant", "annotation", "todo", "error", "doc_tag"]
MIN_DE = 12.0
KINDS = ("protanopia", "deuteranopia")


def collapse_pairs(colors):
    """返回 [(a, b, normal, protanopia, deuteranopia)]，按最差 CVD 排序。"""
    out = []
    for a, b in itertools.combinations(TOKENS, 2):
        if a not in colors or b not in colors:
            continue
        if colors[a].upper() == colors[b].upper():
            continue
        normal = de2000(colors[a], colors[b])
        if normal < MIN_DE:
            continue
        sim = {kind: de2000(simulate_cvd(colors[a], kind),
                            simulate_cvd(colors[b], kind))
               for kind in KINDS}
        if min(sim.values()) < MIN_DE:
            out.append((a, b, normal, sim["protanopia"], sim["deuteranopia"]))
    return sorted(out, key=lambda row: min(row[3], row[4]))


def build_report():
    import json
    data = json.loads(PALETTE.read_text(encoding="utf-8"))
    lines = [
        "# 色觉缺陷（CVD）报告（自动生成）",
        "",
        "生成时间：%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "",
        "规则：正常色觉下 ΔE2000 ≥ %.0f，但在 protanopia 或 deuteranopia "
        "模拟下 ΔE2000 < %.0f 的 token 配对。" % (MIN_DE, MIN_DE),
        "这是**报告项，不判失败**；官方靠发布 CVD 变体解决，本项目暂未提供。",
        "",
    ]
    counts = {}
    for theme in data["themes"]:
        pairs = collapse_pairs(theme["colors"])
        counts[theme["id"]] = len(pairs)
        lines.append("## %s「%s」" % (theme["name"], theme["label"]))
        lines.append("")
        lines.append("塌陷配对：**%d**" % len(pairs))
        lines.append("")
        if pairs:
            lines.append("| token A | token B | 正常 ΔE | protanopia ΔE | deuteranopia ΔE |")
            lines.append("|---|---|---|---|---|")
            for a, b, normal, prot, deut in pairs:
                lines.append("| `%s` | `%s` | %.1f | %.1f | %.1f |"
                             % (a, b, normal, prot, deut))
        else:
            lines.append("无。")
        lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append("两款主题分别有 %s 对塌陷。要关闭这个缺口，需要为每款主题生成"
                 " deuteranopia / protanopia 变体，或在变体中重新分配这些配对的色相；"
                 "当前版本不提供变体，因此本报告只做量化。"
                 % " / ".join("%d" % counts[k] for k in sorted(counts)))
    return "\n".join(lines) + "\n", counts


def main(argv=None):
    ap = argparse.ArgumentParser(description="生成色觉缺陷报告")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)
    text, counts = build_report()
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("写入 %s：%s" % (out, " / ".join(
        "%s=%d" % (k, counts[k]) for k in sorted(counts))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
