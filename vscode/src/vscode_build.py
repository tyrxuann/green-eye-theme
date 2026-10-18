#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VS Code 构建入口：生成主题 JSON，并按需打包 .vsix。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import generate  # noqa: E402
import package_vsix  # noqa: E402


def build(package=True, outdir=None):
    if not package:
        return generate.generate()
    return package_vsix.package(outdir)


if __name__ == "__main__":
    sys.exit(build())
