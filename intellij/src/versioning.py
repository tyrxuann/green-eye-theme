#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一更新版本号：`intellij/src/project_config.py` + `vscode/package.json`。

只改这两个源文件；CHANGELOG、发布包、jar 名都由后续 build/package 重新生成。
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

TARGETS = (
    ("intellij/src/project_config.py",
     re.compile(r'^VERSION\s*=\s*"[^"]+"', re.M),
     'VERSION = "%s"'),
    ("vscode/package.json",
     re.compile(r'("version"\s*:\s*")[^"]+(")'),
     r'\g<1>%s\g<2>'),
)


def current_version(root=None):
    root = Path(root or ROOT)
    text = (root / "intellij" / "src" / "project_config.py").read_text(
        encoding="utf-8")
    match = re.search(r'^VERSION\s*=\s*"([^"]+)"', text, re.M)
    if not match:
        raise ValueError("project_config.py 里找不到 VERSION")
    return match.group(1)


def bump(new_version, root=None, dry_run=False):
    root = Path(root or ROOT)
    if not SEMVER.match(new_version):
        raise ValueError("版本号必须是 X.Y.Z：%s" % new_version)
    old = current_version(root)
    if old == new_version:
        print("版本号已经是 %s，无需改动。" % old)
        return 0

    changes = []
    for rel, pattern, replacement in TARGETS:
        path = root / rel
        if not path.is_file():
            raise ValueError("缺少文件：%s" % path)
        text = path.read_text(encoding="utf-8")
        new_text, count = pattern.subn(replacement % new_version, text, count=1)
        if count != 1:
            raise ValueError("%s 里找不到可替换的版本号" % rel)
        changes.append((path, new_text))

    for path, _ in changes:
        print("%s %s" % ("将更新" if dry_run else "更新", path))
    if dry_run:
        return 0
    for path, text in changes:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        if path.name == "project_config.py":
            cache = path.parent / "__pycache__"
            for pyc in cache.glob("project_config.*.pyc"):
                pyc.unlink()
    print("版本号：%s → %s；下次 build 会生成新文件名。" % (old, new_version))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="统一更新版本号")
    ap.add_argument("version", help="新版本号，例如 1.2.0")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        return bump(args.version, dry_run=args.dry_run)
    except ValueError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
