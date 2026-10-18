#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 README 的状态色口径段，避免手写数字再次漂移。

数字来自 `check_collisions.summary()`，与构建时跑的是同一套判据。
用法: python3 gen_status_metrics.py [README 路径]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from check_collisions import summary  # noqa: E402

B = "<!-- STATUS-METRICS:BEGIN -->"
E = "<!-- STATUS-METRICS:END -->"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        HERE, "..", "README.md")
    s = summary()
    block = B + "\n" + (
        "现在的结论：**状态色两两可分性不劣于官方**。检查 **%d 对**；"
        "官方标尺未达阈值 **%d 对**（覆盖 %d/%d 个状态块键）；"
        "两款合计未达阈值 **%d 对**，其中 **%d 对**官方同一对也未达（基线噪声），"
        "其余已在例外表写明理由；**未豁免 %d 对**。"
        % (s["total_pairs"], s["official_fail"], s["official_cov"], s["ours_cov"],
           s["current_fail"], s["official_overlap"], s["extra"])
    ) + "\n" + E
    text = open(path, encoding="utf-8").read()
    if B not in text:
        print("README 缺少 %s 标记" % B)
        return 1
    text = re.sub(re.escape(B) + r".*?" + re.escape(E), block, text,
                  count=1, flags=re.S)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("README 状态色口径已生成（%d/%d）"
          % (s["current_fail"], s["total_pairs"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
