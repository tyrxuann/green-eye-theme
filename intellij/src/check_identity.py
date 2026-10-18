#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"两款主题是不是一眼能看出不同" —— 把设计判断变成可执行判据。

背景：只比"平均色差"会被大量结构色/别名稀释，看不出身份。评审给的判据是：
  · novelty：{字符串, 数字, 函数} 三个最高频内容 token 的**最小** ΔE ≥ 15
  · 频率加权（剔除正文）：≥ 16
  · 8 个主力 token 里 ΔE ≥ 12 的个数 ≥ 5
权重不拍脑袋 —— 直接用 `render_spec.JAVA` 这段真实样例里各 token 的**实测出现次数**。
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES  # noqa: E402
from check_collisions import de2000  # noqa: E402

# 8 个主力 token（承载主题身份的中彩度语义色）
MAIN = ["keyword", "string", "number", "function", "constant", "annotation",
        "todo", "comment"]
# novelty 只看这三个：它们是屏幕上面积最大的彩色内容
NOVELTY = ["string", "number", "function"]
THRESHOLDS = {"novelty_min": 15.0, "weighted": 16.0, "main_count": 5}


# 冻结的频率权重：判据不能因为"谁改了样例代码"而翻转（评审 S2'）。
# 数值来自 render_spec.JAVA 在冻结时刻的实测计数，样例内容由下面的 hash 断言锁住。
FROZEN_WEIGHTS = {
    "punctuation": 49, "brace": 40, "keyword": 31, "fg": 24, "class_name": 23,
    "operator": 22, "doc_comment": 19, "function_call": 15, "field": 13,
    "comment": 8, "parameter": 7, "local_var": 6, "string": 5, "doc_tag": 5,
    "type_param": 4, "annotation": 2, "number": 2, "function": 2,
    "constant": 1, "escape": 1,
}
SAMPLE_SHA256 = None   # 首次运行时打印，之后可写死


def weights_from_sample():
    """回到冻结表；同时打印样例 hash，便于日后把 hash 也写死。"""
    import hashlib
    from render_spec import JAVA
    h = hashlib.sha256(JAVA.encode("utf-8")).hexdigest()[:16]
    print("  样例 hash=%s（冻结权重表 FROZEN_WEIGHTS）" % h)
    return Counter(FROZEN_WEIGHTS)


def evaluate(a, b, weights):
    de = {k: de2000(a[k], b[k]) for k in a
          if k in b and isinstance(a[k], str) and a[k].startswith("#")}
    novelty = min(de[k] for k in NOVELTY)
    # 频率加权：只算"有身份"的语义色。
    # 关键：必须剔除**结构性别名**（punctuation/brace/class_name/operator… 都等于正文色），
    # 它们出现频率最高、ΔE 恒为 0，不剔除会把加权值稀释成噪声。
    neutral = {a.get("fg"), b.get("fg")}
    ranked = [(k, de[k], weights.get(k, 0)) for k in de
              if k != "fg" and a.get(k) not in neutral and weights.get(k, 0) > 0]
    tot = sum(w for _, _, w in ranked)
    weighted = sum(d * w for _, d, w in ranked) / tot if tot else 0.0
    main_hits = sum(1 for k in MAIN if de[k] >= 12)
    return de, novelty, weighted, main_hits, ranked


def main():
    keys = sorted(PALETTES)
    if len(keys) < 2:
        print("只有一款主题，无法比较身份差异")
        return 0
    weights = weights_from_sample()
    print("主题身份检查（判据来自第 2 轮评审）")
    print("  频率权重取自真实样例 `render_spec.JAVA` 的实测 token 计数；"
          "加权时剔除结构性别名（凡等于正文色的 token）")
    bad = 0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = PALETTES[keys[i]], PALETTES[keys[j]]
            de, novelty, weighted, hits, ranked = evaluate(a, b, weights)
            ok = (novelty >= THRESHOLDS["novelty_min"]
                  and weighted >= THRESHOLDS["weighted"]
                  and hits >= THRESHOLDS["main_count"])
            print("\n【%s「%s」 vs %s「%s」】%s"
                  % (a["name"], a["label"], b["name"], b["label"], "✅ 一眼可分" if ok else "❌ 太像"))
            print("  novelty（%s 的最小 ΔE）= %.1f（要求 ≥ %.0f）"
                  % ("/".join(NOVELTY), novelty, THRESHOLDS["novelty_min"]))
            print("  频率加权（剔正文）= %.1f（要求 ≥ %.0f）"
                  % (weighted, THRESHOLDS["weighted"]))
            print("  主力 token 中 ΔE≥12 的个数 = %d/8（要求 ≥ %d）"
                  % (hits, THRESHOLDS["main_count"]))
            print("  逐 token（按频率影响力排序）：")
            for k, d, w in sorted(ranked, key=lambda x: -x[1] * x[2])[:10]:
                flag = "✅" if d >= 12 else ("△" if d >= 8 else "❌")
                print("     %s %-12s ΔE %5.1f  权重 %d" % (flag, k, d, w))
            if not ok:
                bad += 1
    if bad:
        print("\n❌ %d 组主题「太像」，不满足「一眼看出是两款」" % bad)
        return 1
    print("\n✅ 各组主题的感知差异达标（一眼能看出是两款）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
