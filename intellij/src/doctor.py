#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Green Eye 预检（doctor）：在不启动 IDE 的前提下检查构建产物、字体、安装状态。

它不能替代真机目视走查（见 docs/manual-verification.md），但能把
"装没装、版本对不对、字体有没有、VSIX 在不在"这类问题先排除。
"""
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
sys.path.insert(0, str(HERE))

import install  # noqa: E402
from project_config import JAR_PREFIX, VERSION  # noqa: E402

OK, WARN, FAIL = "ok", "warn", "fail"
MARKS = {OK: "✅", WARN: "⚠️", FAIL: "❌"}


def check_palette(path):
    if not path.is_file():
        return FAIL, "palette.json", "缺失：%s" % path
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return FAIL, "palette.json", "无法解析：%s" % exc
    if data.get("schema") != "green-eye-palette/1":
        return FAIL, "palette.json", "schema 不是 green-eye-palette/1"
    themes = data.get("themes", [])
    if len(themes) != 2:
        return FAIL, "palette.json", "主题数 %d（应为 2）" % len(themes)
    return OK, "palette.json", "%d 款主题" % len(themes)


def check_jar(path):
    if not path.is_file():
        return FAIL, "插件 jar", "缺失：%s" % path.name
    if path.name != "%s%s.jar" % (JAR_PREFIX, VERSION):
        return WARN, "插件 jar", "文件名与版本不一致：%s" % path.name
    if not install.is_our_jar(path):
        return FAIL, "插件 jar", "不是本插件：%s" % path.name
    return OK, "插件 jar", path.name


def check_icls(path):
    if not path.is_file():
        return FAIL, "配色方案", "缺失：%s" % path.name
    if not install.is_our_icls(path):
        return FAIL, "配色方案", "方案名不匹配：%s" % path.name
    return OK, "配色方案", path.name


def check_license(path=None):
    path = Path(path) if path else ROOT / "LICENSE"
    if path.is_file():
        return OK, "LICENSE", path.name
    return WARN, "LICENSE", "未添加（发布前需选择 MIT/Apache/私有）"


def check_manual_report(path=None):
    path = Path(path) if path else (
        INTELLIJ / "build" / "ref" / "manual-verification-report.md")
    if not path.is_file():
        return WARN, "真机走查", "未生成（运行 green_eye.py manual）"
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"通过 \*\*(\d+)\*\* · 失败 \*\*(\d+)\*\* · 跳过 \*\*(\d+)\*\*",
                      text)
    if not match:
        return WARN, "真机走查", "报告格式无法识别"
    passed, failed, skipped = (int(x) for x in match.groups())
    detail = "通过 %d / 失败 %d / 跳过 %d" % (passed, failed, skipped)
    return (WARN if failed else OK), "真机走查", detail


def check_fonts():
    if importlib.util.find_spec("PIL") is None:
        return [(WARN, "Pillow", "未安装；只能 build --no-preview")]
    import PIL
    from render_preview import F
    return [
        (OK, "Pillow", PIL.__version__),
        (OK if F.mono else WARN, "等宽字体", F.mono or "未找到，将回退"),
        (OK if F.cjk else WARN, "CJK 字体", F.cjk or "未找到，将回退"),
    ]


def check_installed():
    try:
        configs = install.discover_targets(install.jetbrains_root(), None, False)
    except install.InstallError as exc:
        return [(WARN, "IntelliJ 安装", str(exc))]
    if not configs:
        return [(WARN, "IntelliJ 安装", "未找到 IntelliJIdea* 配置目录")]
    rows = []
    for config in configs:
        jar = config / "plugins" / ("%s%s.jar" % (JAR_PREFIX, VERSION))
        if jar.is_file() and install.is_our_jar(jar):
            rows.append((OK, "IntelliJ 插件", str(jar)))
        else:
            rows.append((WARN, "IntelliJ 插件", "未安装 %s" % jar.name))
        disabled = config / "disabled_plugins.txt"
        if install.disabled_has_plugin(disabled):
            rows.append((WARN, "禁用记录", "disabled_plugins.txt 仍含本插件"))
        icls = sorted((config / "colors").glob("Green-Eye-*.icls"))
        if icls:
            rows.append((OK, "手工配色副本", "%d 个" % len(icls)))
    return rows


def checks():
    rows = [
        (OK if sys.version_info >= (3, 9) else FAIL, "Python",
         sys.version.split()[0]),
        (OK if shutil.which("uv") else WARN, "uv",
         shutil.which("uv") or "未安装（可选）"),
        check_palette(ROOT / "shared" / "palette.json"),
        check_license(),
        check_manual_report(),
        check_jar(INTELLIJ / "dist" / ("%s%s.jar" % (JAR_PREFIX, VERSION))),
    ]
    for name in ("Green-Eye-Dark.icls", "Green-Eye-Mineral.icls"):
        rows.append(check_icls(INTELLIJ / "themes" / name))
    vsix = ROOT / "vscode" / "dist" / ("green-eye-theme-%s.vsix" % VERSION)
    if vsix.is_file():
        rows.append((OK, "VS Code VSIX", vsix.name))
    else:
        rows.append((WARN, "VS Code VSIX", "未生成（运行 green_eye.py vscode）"))
    code = shutil.which("code")
    rows.append((OK if code else WARN, "VS Code CLI", code or "未安装 code"))
    rows += check_fonts()
    rows += check_installed()
    return rows


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Green Eye 预检")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)
    rows = checks()
    if args.json:
        payload = {
            "checks": [{"status": s, "label": l, "detail": d} for s, l, d in rows],
            "summary": {
                "ok": sum(1 for s, _, _ in rows if s == OK),
                "warn": sum(1 for s, _, _ in rows if s == WARN),
                "fail": sum(1 for s, _, _ in rows if s == FAIL),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if payload["summary"]["fail"] else 0
    print("Green Eye Doctor")
    for status, label, detail in rows:
        print("  %s %-16s %s" % (MARKS[status], label, detail))
    fails = sum(1 for status, _, _ in rows if status == FAIL)
    warns = sum(1 for status, _, _ in rows if status == WARN)
    oks = sum(1 for status, _, _ in rows if status == OK)
    print("\n自动检查：%d 通过，%d 警告，%d 失败" % (oks, warns, fails))
    if fails:
        print("有失败项，先按提示修复；然后重跑 green_eye.py doctor。")
        return 1
    print("静态预检通过；仍需按 docs/manual-verification.md 做目视走查。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
