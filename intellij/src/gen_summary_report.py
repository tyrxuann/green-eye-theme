#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成单页发布前汇总：doctor 预检 + 验收报告 + CVD + 真机走查 + 产物。

输出 build/ref/report.md（自动生成，不提交）。适合发版前快速扫一眼。
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
REF = INTELLIJ / "build" / "ref"
sys.path.insert(0, str(HERE))

import doctor  # noqa: E402
from check_collisions import summary  # noqa: E402
from project_config import JAR_PREFIX, VERSION  # noqa: E402

DEFAULT_OUT = REF / "report.md"
MARKS = {"ok": "✅", "warn": "⚠️", "fail": "❌"}


def _verification():
    path = REF / "verification.md"
    if not path.is_file():
        return "未生成（先运行 build）"
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"检查结果：(\d+) 项通过，(\d+) 项失败", text)
    return match.group(0) if match else "无法解析"


def _manual():
    path = REF / "manual-verification-report.md"
    if not path.is_file():
        return "未生成（运行 green_eye.py manual）"
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r"通过 \*\*(\d+)\*\* · 失败 \*\*(\d+)\*\*"
        r"(?: · 不确定 \*\*(\d+)\*\*)? · 跳过 \*\*(\d+)\*\*", text)
    if not match:
        return "无法解析"
    passed, failed, unknown, skipped = match.groups()
    return "通过 %s / 失败 %s / 不确定 %s / 跳过 %s" % (
        passed, failed, unknown or 0, skipped)


def _cvd_variant():
    path = ROOT / "release" / ("green-eye-%s-cvd.zip" % VERSION)
    if path.is_file():
        return "已生成 `%s`（A+ 改善版，非 CVD 安全）" % path.name
    return "未生成（运行 `green_eye.py cvd-variants`）"


def _artifacts():
    rows = []
    jar = INTELLIJ / "dist" / ("%s%s.jar" % (JAR_PREFIX, VERSION))
    vsix = ROOT / "vscode" / "dist" / ("green-eye-theme-%s.vsix" % VERSION)
    for label, path in [("IntelliJ jar", jar), ("VS Code VSIX", vsix)]:
        if path.is_file():
            rows.append((label, path.name, path.stat().st_size))
        else:
            rows.append((label, "未生成", 0))
    for path in sorted((ROOT / "release").glob("*.zip")):
        rows.append(("Release", path.name, path.stat().st_size))
    return rows


def build_report():
    rows = doctor.checks()
    counts = {"ok": 0, "warn": 0, "fail": 0}
    for status, _, _ in rows:
        counts[status] += 1
    cvd = summary()
    lines = [
        "# Green Eye 发布前汇总（自动生成）",
        "",
        "生成时间：%s　版本：%s" % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), VERSION),
        "",
        "## Doctor",
        "",
        "通过 **%d** · 警告 **%d** · 失败 **%d**" % (
            counts["ok"], counts["warn"], counts["fail"]),
        "",
        "| 状态 | 检查 | 详情 |",
        "|---|---|---|",
    ]
    for status, label, detail in rows:
        lines.append("| %s | %s | %s |" % (
            MARKS[status], label, str(detail).replace("|", "\\|")))
    lines += [
        "",
        "## 验收",
        "",
        "- %s" % _verification(),
        "",
        "## CVD",
        "",
        "- 检查 %d 对；官方标尺未达阈值 %d 对；两款合计未达阈值 %d 对；未豁免 %d 对。"
        % (cvd["total_pairs"], cvd["official_fail"], cvd["current_fail"],
           cvd["extra"]),
        "- CVD Improved：%s；残余见 `build/ref/cvd-variants-report.md`。"
        % _cvd_variant(),
        "",
        "## 真机走查",
        "",
        "- %s" % _manual(),
        "",
        "## 产物",
        "",
        "| 产物 | 文件名 | 大小 |",
        "|---|---|---|",
    ]
    for label, name, size in _artifacts():
        lines.append("| %s | `%s` | %d 字节 |" % (label, name, size))
    lines += [
        "",
        "## 仍需处理",
        "",
    ]
    pending = []
    if not (ROOT / "LICENSE").is_file():
        pending.append("添加 LICENSE（MIT / Apache-2.0 / 私有）")
    if not (REF / "manual-verification-report.md").is_file():
        pending.append("运行 `green_eye.py manual` 完成真机走查")
    if not (ROOT / "release" / ("green-eye-%s-cvd.zip" % VERSION)).is_file():
        pending.append("运行 `green_eye.py cvd-variants` 生成 A+ 改善版")
    lines += ["- %s" % item for item in pending]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="生成发布前汇总")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_report())
    print("写入 %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
