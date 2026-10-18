#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真机走查 runner：解析 docs/manual-verification.md 的复选框，逐项记录结果。

用法:
    python3 green_eye.py manual --quick         # 8 项高信号快速检查
    python3 green_eye.py manual                 # 完整 39 项，y/n/u/s/q
    python3 green_eye.py manual --list          # 只列出检查项
    python3 green_eye.py manual --answers y,n,u,s # 非交互（测试/批处理）
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
CHECKLIST = ROOT / "docs" / "manual-verification.md"
DEFAULT_REPORT = INTELLIJ / "build" / "ref" / "manual-verification-report.md"
STATUS = {"y": "通过", "n": "失败", "u": "不确定", "s": "跳过"}
QUICK_MARKERS = (
    "里有**两款**",
    "波浪线",
    "Javadoc 的 `@param`",
    "断点行整行有底色",
    "当前执行行有明显底色",
    "新增行绿、删除行红、修改行蓝",
    "参数名内联提示",
    "选中一块代码是**青色**",
)
ITEM_RE = re.compile(r"^- \[[ xX]\] (.*)$")


def parse(path=None):
    path = Path(path or CHECKLIST)
    items, section, current = [], "", None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            if current:
                items.append((section, current))
                current = None
            section = line[3:].strip()
            continue
        match = ITEM_RE.match(line)
        if match:
            if current:
                items.append((section, current))
            current = match.group(1).strip()
            continue
        if current and raw.startswith("      ") and line.strip():
            current += " " + line.strip()
        elif current and not line.strip():
            items.append((section, current))
            current = None
    if current:
        items.append((section, current))
    return items


def quick_items(items):
    selected = [(section, text) for section, text in items
                if any(marker in text for marker in QUICK_MARKERS)]
    return selected or items


def collect(items, answers=None):
    results = []
    queue = [a.strip().lower() for a in answers] if answers is not None else None
    for index, (section, text) in enumerate(items, 1):
        if queue is not None:
            answer = queue[index - 1] if index - 1 < len(queue) else "s"
        else:
            print("\n[%d/%d] %s" % (index, len(items), section))
            print("  %s" % text)
            while True:
                answer = input("  [y]通过 [n]失败 [u]不确定 [s]跳过 [q]退出 > ").strip().lower()
                if answer in ("y", "n", "u", "s", "q"):
                    break
        if answer == "q":
            break
        note = ""
        if answer == "n" and queue is None:
            note = input("  备注（可空）: ").strip()
        results.append({"section": section, "text": text,
                        "status": STATUS.get(answer, "跳过"), "note": note})
    return results


def write_report(results, path=None):
    path = Path(path or DEFAULT_REPORT)
    path.parent.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for r in results if r["status"] == "通过")
    failed = sum(1 for r in results if r["status"] == "失败")
    skipped = sum(1 for r in results if r["status"] == "跳过")
    unknown = sum(1 for r in results if r["status"] == "不确定")
    lines = [
        "# 实机走查报告（自动生成）",
        "",
        "生成时间：%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "",
        "通过 **%d** · 失败 **%d** · 不确定 **%d** · 跳过 **%d** · 共 %d 项"
        % (passed, failed, unknown, skipped, len(results)),
        "",
    ]
    failed_rows = [r for r in results if r["status"] == "失败"]
    lines.append("## 失败项")
    lines.append("")
    if failed_rows:
        for row in failed_rows:
            note = "（备注：%s）" % row["note"] if row["note"] else ""
            lines.append("- **%s**：%s%s" % (row["section"], row["text"], note))
    else:
        lines.append("无。")
    lines.append("")
    lines.append("## 不确定项")
    lines.append("")
    unknown_rows = [r for r in results if r["status"] == "不确定"]
    if unknown_rows:
        for row in unknown_rows:
            lines.append("- **%s**：%s" % (row["section"], row["text"]))
    else:
        lines.append("无。")
    lines.append("")
    lines.append("## 全部")
    lines.append("")
    lines.append("| # | 区域 | 结果 | 检查项 |")
    lines.append("|---|---|---|---|")
    for index, row in enumerate(results, 1):
        lines.append("| %d | %s | %s | %s |"
                     % (index, row["section"].replace("|", "\\|"),
                        row["status"], row["text"].replace("|", "\\|")))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("写入 %s（通过 %d / 失败 %d / 不确定 %d / 跳过 %d）"
          % (path, passed, failed, unknown, skipped))
    return path


def run(list_only=False, answers=None, report=None, quick=False):
    items = parse()
    if quick:
        items = quick_items(items)
    if not items:
        print("清单为空：%s" % CHECKLIST, file=sys.stderr)
        return 1
    if list_only:
        if quick:
            print("快速检查（%d 项）" % len(items))
        section = None
        for index, (sec, text) in enumerate(items, 1):
            if sec != section:
                print("\n## %s" % sec)
                section = sec
            print("  %d. %s" % (index, text))
        return 0
    if answers is None and not sys.stdin.isatty():
        print("非交互环境：请用 --list 查看，或 --answers y,n,u,s 批处理。")
        return 1
    results = collect(items, answers=answers)
    write_report(results, report)
    failed = sum(1 for row in results if row["status"] == "失败")
    if failed:
        print("有 %d 项失败；详见报告。" % failed, file=sys.stderr)
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="真机走查 runner")
    ap.add_argument("--list", action="store_true", help="只列出检查项")
    ap.add_argument("--answers", help="逗号分隔的 y/n/u/s 序列（非交互）")
    ap.add_argument("--report", help="报告输出路径")
    ap.add_argument("--quick", action="store_true", help="只跑 8 项高信号检查")
    args = ap.parse_args(argv)
    answers = args.answers.split(",") if args.answers else None
    return run(list_only=args.list, answers=answers, report=args.report,
               quick=args.quick)


if __name__ == "__main__":
    sys.exit(main())
