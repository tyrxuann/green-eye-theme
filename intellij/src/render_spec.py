#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
与渲染器共享、但不依赖 Pillow 的纯数据。

单独拆出来的原因：`check_identity.py` 和 `check_render_styles.py` 只需要 Java
样例和样式映射，却曾经通过 `import render_java` 把 Pillow 一起拖进构建。
于是"不生成预览图"的构建仍然要求 Pillow —— 与"预览只是可选项"的设计矛盾。
这个模块只含字符串和字典，任何 Python 3.9+ 都能导入，不需要任何第三方包。
"""

JAVA = '''package com.greeneye.forest;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 碳汇估算器。
 *
 * @author greeneye
 */
public class CarbonCalculator implements Calculator<Plot> {

    /** 默认含碳系数。 */
    public static final double DEFAULT_COEFFICIENT = 0.48;

    private final double coefficient;
    private int calls;

    public CarbonCalculator(double coefficient) {
        this.coefficient = coefficient;
    }

    /**
     * 估算生物量。
     *
     * @param plots 样地列表
     * @param verbose 是否输出明细
     * @return 每公顷生物量 (t/ha)
     * @throws IllegalArgumentException 列表为空时
     */
    @Override
    public Map<String, Double> summarize(List<Plot> plots, boolean verbose) {
        if (Objects.isNull(plots) || plots.isEmpty()) {
            throw new IllegalArgumentException("样地列表不能为空: " + plots);
        }
        this.calls++;
        Map<String, Double> r = plots.stream().collect(
                Collectors.toMap(Plot::id, p -> p.biomass(coefficient)));
        double mean = r.values().stream().mapToDouble(Double::doubleValue)
                .average().orElse(0.0);   // TODO 空集合应返回 Optional
        if (verbose) {
            System.out.printf("样地 %d 块，均值 %.3f t/ha%n", r.size(), mean);
        }
        return r;
    }

    @Override
    public String toString() {
        return "CarbonCalculator[coef=" + coefficient + ", calls=" + calls + "]";
    }
}'''

# 渲染样式映射：与 themes/*.icls 里对应键的 FONT_TYPE 必须一致（由
# check_render_styles.py 强制校验，避免"渲染器和产物各说各话"）
STYLE_BY_KEY = {
    "doc_comment": "i",    # DEFAULT_DOC_COMMENT 官方斜体
    "todo": "i",           # 官方 TODO 斜体
    "constant": "i",       # 官方常量/静态成员斜体
}
# 说明：DEFAULT_STATIC_METHOD 官方是斜体，但 mock 的 tokenizer 分不清
# "静态方法调用"与"实例方法调用"，把全部方法名画成斜体是错的，所以这里不画；
# 这一条由 check_render_styles.py 记为"已知 mock 限制"。
