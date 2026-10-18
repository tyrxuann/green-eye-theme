#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VS Code 构建入口：生成主题 JSON，并按需打包 .vsix。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VSCODE = HERE.parent
ROOT = VSCODE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "intellij" / "src"))

import generate  # noqa: E402
import package_vsix  # noqa: E402
from project_config import VERSION  # noqa: E402


def check_freshness(package=True, outdir=None):
    """主题/VSIX 的 mtime 必须不早于 palette.json、生成器与 package.json。"""
    inputs = [ROOT / "shared" / "palette.json", VSCODE / "package.json"]
    inputs += sorted(HERE.glob("*.py"))
    newest = max((p.stat().st_mtime for p in inputs if p.is_file()), default=0)
    outputs = sorted((VSCODE / "themes").glob("*.json"))
    if package:
        vsix_dir = Path(outdir).expanduser() if outdir else VSCODE / "dist"
        outputs += sorted(vsix_dir.glob("green-eye-theme-%s.vsix" % VERSION))
    if not outputs:
        print("缺少 VS Code 产物；先运行 green_eye.py vscode。", file=sys.stderr)
        return 1
    stale = [p for p in outputs if p.stat().st_mtime < newest - 1]
    if stale:
        print("VS Code 产物比输入旧：", file=sys.stderr)
        for path in stale:
            print("  - %s" % path, file=sys.stderr)
        return 1
    print("VS Code 产物新鲜度：✅（%d 个文件）" % len(outputs))
    return 0


def build(package=True, outdir=None):
    rc = generate.generate() if not package else package_vsix.package(outdir)
    if rc:
        return rc
    return check_freshness(package=package, outdir=outdir)


if __name__ == "__main__":
    sys.exit(build())
