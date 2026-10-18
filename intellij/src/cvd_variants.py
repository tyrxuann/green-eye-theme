#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A+「CVD Improved」变体：只改少量 token，尽量降低红/绿色盲下的塌陷。

这是"改善版"，不是 CVD 安全版：
  · 松林 18 → 13 对塌陷（protanopia 11 / deuteranopia 12）
  · 矿彩 20 → 14 对塌陷（protanopia 10 / deuteranopia 12）
残余配对会写进 cvd-variants-report.md，不隐瞒。

产物：
  intellij/themes/variants/Green-Eye-*-CVD.icls
  vscode/themes/variants/green-eye-*-cvd.json
  vscode/dist/green-eye-cvd-variants-<version>.vsix
  release/green-eye-<version>-cvd.zip
"""
import argparse
import hashlib
import itertools
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
VSCODE = ROOT / "vscode"
REF = INTELLIJ / "build" / "ref"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(VSCODE / "src"))
sys.path.insert(0, str(ROOT / "shared" / "tools"))

import build_pipeline  # noqa: E402
import gen_icls  # noqa: E402
import generate  # noqa: E402
import package_vsix  # noqa: E402
from project_config import VERSION  # noqa: E402
from colorlib import contrast, de2000, simulate_cvd  # noqa: E402
from gen_cvd_report import TOKENS, collapse_pairs  # noqa: E402

PALETTE = ROOT / "shared" / "palette.json"
ICLS_DIR = INTELLIJ / "themes" / "variants"
VSCODE_DIR = VSCODE / "themes" / "variants"
VSCODE_DIST = VSCODE / "dist"
REF_REPORT = REF / "cvd-variants-report.md"

OVERRIDES = {
    "dark": {"string": "#6BC087", "doc_tag": "#91AFB6",
             "doc_comment": "#577F87"},
    "mineral": {"annotation": "#D2AD9B", "doc_tag": "#899BC0",
                "doc_comment": "#707A8F"},
}
FLOORS = {"fg": 9.0, "comment": 3.5, "doc_comment": 3.0, "keyword": 6.0,
          "string": 6.0, "number": 6.0, "function": 6.0, "constant": 4.0,
          "annotation": 6.0, "todo": 6.0, "error": 4.5, "doc_tag": 4.5}
KINDS = ("protanopia", "deuteranopia")


def _load():
    if not PALETTE.is_file():
        raise SystemExit("缺少 %s；先运行 green_eye.py palette。" % PALETTE)
    return json.loads(PALETTE.read_text(encoding="utf-8"))


def variant_colors(base, overrides):
    colors = dict(base)
    colors.update(overrides)
    return colors


def _names():
    names = set(gen_icls.FALLBACK_NAMES)
    for path in build_pipeline.NAMES:
        if path.is_file():
            names |= {line.strip() for line in
                      path.read_text(encoding="utf-8").splitlines()
                      if line.strip() and not line.startswith("#")}
    for name in ("Green-Eye-Dark.icls", "Green-Eye-Mineral.icls"):
        path = INTELLIJ / "themes" / name
        if path.is_file():
            root = ET.parse(path).getroot()
            names |= {opt.get("name") for opt in
                      root.findall("./attributes/option") if opt.get("name")}
    chrome = []
    for path in build_pipeline.CHROME:
        if path.is_file():
            chrome += [line.strip() for line in
                       path.read_text(encoding="utf-8").splitlines()
                       if line.strip()]
    return names, chrome


def _write_icls(pal, path, names, chrome):
    scheme = gen_icls.build_icls(pal, names, chrome)
    gen_icls.indent(scheme)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           + gen_icls.ET.tostring(scheme, encoding="unicode") + "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(xml)


def _write_vscode(base, colors, path):
    theme = {"name": base["name"], "label": "(CVD Improved)",
             "colors": colors}
    text = json.dumps(generate.theme_doc(theme), ensure_ascii=False,
                      indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _readme():
    return """# Green Eye · CVD Improved

这是 A+ 改善版，不是 CVD 安全版：

- 松林：18 → 13 对塌陷
- 矿彩：20 → 14 对塌陷

残余配对照实记录在 cvd-variants-report.md。

## IntelliJ IDEA

Settings -> Editor -> Color Scheme -> 齿轮 -> Import Scheme...
选择 intellij/Green-Eye-Dark-CVD.icls 或 Green-Eye-Mineral-CVD.icls。

## VS Code

Extensions -> ... -> Install from VSIX...
选择 vscode/green-eye-cvd-variants-%s.vsix，然后在 Color Theme 里选
「Green Eye Dark (CVD Improved)」或「Green Eye Mineral (CVD Improved)」。
""" % VERSION


def report_text():
    lines = [
        "# CVD Improved 变体报告（自动生成）",
        "",
        "这是 A+「只改少量 token」的改善版，**不是 CVD 安全版**。",
        "",
    ]
    for theme in _load()["themes"]:
        base = theme["colors"]
        overrides = OVERRIDES[theme["id"]]
        colors = variant_colors(base, overrides)
        pairs = collapse_pairs(colors)
        normal_min = min(de2000(colors[a], colors[b])
                         for a, b in itertools.combinations(TOKENS, 2))
        lines += [
            "## %s「%s」" % (theme["name"], theme["label"]),
            "",
            "| 槽位 | 原值 | CVD Improved | 对比度 |",
            "|---|---|---|---|",
        ]
        for key, value in overrides.items():
            lines.append("| `%s` | `%s` | `%s` | %.2f:1 |"
                         % (key, base[key], value,
                            contrast(value, colors["bg_editor"])))
        lines += [
            "",
            "塌陷配对：**%d**（正常色觉最小 ΔE %.1f）" % (len(pairs), normal_min),
            "",
            "| 配对 | 正常 | protanopia | deuteranopia |",
            "|---|---|---|---|",
        ]
        for a, b, normal, prot, deut in pairs:
            lines.append("| `%s` ↔ `%s` | %.1f | %.1f | %.1f |"
                         % (a, b, normal, prot, deut))
        lines.append("")
    return "\n".join(lines) + "\n"


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _build_vsix(target, themes):
    pkg = {
        "name": "green-eye-cvd-variants",
        "displayName": "Green Eye CVD Improved",
        "description": "Green Eye 松林/矿彩的 CVD 改善版（A+）。",
        "version": VERSION,
        "publisher": "green-eye",
        "license": "MIT",
        "engines": {"vscode": "^1.80.0"},
        "categories": ["Themes"],
        "contributes": {"themes": [
            {"label": "Green Eye Dark (CVD Improved)", "uiTheme": "vs-dark",
             "path": "./themes/green-eye-dark-cvd.json"},
            {"label": "Green Eye Mineral (CVD Improved)", "uiTheme": "vs-dark",
             "path": "./themes/green-eye-mineral-cvd.json"},
        ]},
    }
    license_path = ROOT / "LICENSE"
    content_types = package_vsix.CONTENT_TYPES
    if license_path.is_file():
        content_types = content_types.replace(
            "</Types>",
            '  <Override PartName="/extension/LICENSE" ContentType="text/plain"/>\n</Types>')
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("extension.vsixmanifest", package_vsix.manifest(pkg))
        zf.writestr("extension/package.json",
                    json.dumps(pkg, ensure_ascii=False, indent=2) + "\n")
        zf.writestr("extension/README.md", _readme())
        for path in themes:
            zf.writestr("extension/themes/%s" % path.name,
                        path.read_bytes())
        if license_path.is_file():
            zf.writestr("extension/LICENSE", license_path.read_bytes())


def _build_zip(target, icls, vsix, report):
    entries = []
    for path in icls:
        entries.append(("intellij/%s" % path.name, path.read_bytes()))
    entries.append(("vscode/%s" % vsix.name, vsix.read_bytes()))
    entries.append(("INSTALL.txt", _readme().encode("utf-8")))
    entries.append(("cvd-variants-report.md", report.encode("utf-8")))
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        path = ROOT / name
        if path.is_file():
            entries.append((name, path.read_bytes()))
    sums = ["%s  %s" % (_sha(data), arc.rsplit("/", 1)[-1])
            for arc, data in entries]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, data in entries:
            zf.writestr(arc, data)
        zf.writestr("SHA256SUMS", "\n".join(sums) + "\n")


def build(package=True, outdir=None):
    data = _load()
    names, chrome = _names()
    icls = []
    vscode = []
    for theme in data["themes"]:
        colors = variant_colors(theme["colors"], OVERRIDES[theme["id"]])
        icls_path = ICLS_DIR / ("Green-Eye-%s-CVD.icls" % theme["id"].title())
        _write_icls(dict(colors, name="%s (CVD Improved)" % theme["name"],
                         label="CVD Improved", parent=theme["parent"],
                         dark=True), icls_path, names, chrome)
        icls.append(icls_path)
        json_path = VSCODE_DIR / ("green-eye-%s-cvd.json" % theme["id"])
        _write_vscode(theme, colors, json_path)
        vscode.append(json_path)
        print("写入 %s / %s" % (icls_path, json_path))

    report = report_text()
    REF_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REF_REPORT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(report)
    if not package:
        print("写入 %s" % REF_REPORT)
        return 0

    VSCODE_DIST.mkdir(parents=True, exist_ok=True)
    vsix = VSCODE_DIST / ("green-eye-cvd-variants-%s.vsix" % VERSION)
    _build_vsix(vsix, vscode)
    release = Path(outdir).expanduser() if outdir else ROOT / "release"
    release.mkdir(parents=True, exist_ok=True)
    target = release / ("green-eye-%s-cvd.zip" % VERSION)
    _build_zip(target, icls, vsix, report)
    print("写入 %s（%d 字节）" % (vsix, vsix.stat().st_size))
    print("写入 %s（%d 字节）" % (target, target.stat().st_size))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="生成 CVD Improved 改善版")
    ap.add_argument("--no-package", action="store_true")
    ap.add_argument("--outdir")
    args = ap.parse_args(argv)
    return build(package=not args.no_package, outdir=args.outdir)


if __name__ == "__main__":
    sys.exit(main())
