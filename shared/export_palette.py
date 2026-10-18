#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 IntelliJ 侧的调色板导出为**平台无关契约** `shared/palette.json`。

为什么要这一步：色值是平台无关的资产，而 `.icls` / `theme.json` 是 IntelliJ 的实现细节。
把色值抽成 JSON 之后，新增平台（VS Code / Vim / 终端…）只要消费这个文件，
不必读 Python、也不必理解 IntelliJ 的 475 个属性键。

来源（单一真相）：`intellij/src/palette.py`。导入方向是
    intellij/src/palette.py  →  shared/palette.json  →  各平台生成器
所以 shared 不反向依赖任何平台目录。改色调色板后由 `make build` 自动重导，
并有 `--check` 用于断言"JSON 与 palette.py 一致"。
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INTELLIJ_SRC = os.path.join(ROOT, "intellij", "src")
sys.path.insert(0, INTELLIJ_SRC)

# 非色值的元数据键（不导出到 colors）
META_KEYS = {"label", "name", "parent", "dark"}

# 语义角色表：让新平台知道"这个槽位是干什么用的"，而不是只知道一个十六进制
ROLE = {
    "fg": "正文/标识符/类名/括号/运算符/标签（全部同色）",
    "fg_dim": "次要文字（inlay hint、面包屑、被弃用）",
    "comment": "普通注释", "doc_comment": "文档注释（斜体）", "doc_tag": "Javadoc 标签",
    "keyword": "关键字", "string": "字符串", "attr_value": "属性值",
    "number": "数字", "constant": "常量/静态字段（斜体）",
    "function": "函数/方法", "annotation": "注解", "escape": "字符串转义",
    "todo": "TODO（斜体）", "error": "错误", "warning": "警告",
    "line_numbers": "行号", "caret": "光标",
    "bg_editor": "编辑器底色（★ 主题锚点）", "bg_panel": "工具窗/面板底",
    "bg_raised": "浮层底（弹窗/补全/提示芯片）", "bg_selection": "选中",
    "bg_search": "查找命中", "bg_caret_row": "当前行",
    "bg_diff_add": "diff 新增行", "bg_diff_del": "diff 删除行", "bg_diff_mod": "diff 修改行",
    "border": "浮层轮廓", "separator": "窗口内发丝线",
    "accent": "品牌按钮/焦点环", "accent_hover": "品牌按钮悬停态",
    "ui_base": "IDEA 工作台底色", "ui_surface": "IDEA 控件/弹窗表面",
    "ui_hover": "IDEA 控件悬停底色",
}


def collect_exceptions():
    """把"已记录的例外"导出进契约，任何平台的检查器都能读到 ——
    否则新平台会拿一个不知道例外的检查器去判，必然会误报。"""
    same, accepted, ref_tokens = [], [], {}
    try:
        from check_collisions import SAME_BY_DESIGN, _accepted_pairs, de2000
        # 必须排序：SAME_BY_DESIGN 是 set，迭代顺序在不同进程间不稳定，
        # 会让导出文本每次不同 → --check 永远失败（第一次就踩到了）
        same = sorted(sorted(p) for p in SAME_BY_DESIGN)
        accepted = sorted(({"pair": sorted(p), "reason": why}
                           for p, why in _accepted_pairs().items()),
                          key=lambda a: a["pair"])
    except Exception as e:                        # 允许单独导出（无检查器依赖时）
        print("  （未收集撞色例外：%s）" % e)
    try:
        from check_collisions import de2000
        from check_token_separation import TOKENS, dmap
        from official_palette import OFFICIAL
        for pair, d in dmap(OFFICIAL, TOKENS).items():
            if d < 12.0:                          # 参考自己也贴得近的配对
                ref_tokens["|".join(sorted(pair))] = round(d, 1)
    except Exception as e:
        print("  （未收集 token 参考基线：%s）" % e)
    return {
        "same_by_design": same,
        "accepted_pairs": accepted,
        "reference_token_de": ref_tokens,
    }


def build_doc():
    from palette import PALETTES, contrast
    themes = []
    for key, pal in sorted(PALETTES.items()):
        colors = {k: v for k, v in pal.items()
                  if k not in META_KEYS and isinstance(v, str) and v.startswith("#")}
        themes.append({
            "id": key,
            "name": pal["name"],            # ASCII 方案名（IntelliJ 用作 bundledColorScheme id）
            "label": pal["label"],          # 中文显示名
            "dark": bool(pal["dark"]),
            "parent": pal.get("parent"),    # 本平台概念，其他平台可忽略
            "bg_editor": pal["bg_editor"],
            "colors": dict(sorted(colors.items())),
            "contrast": {k: round(contrast(v, pal["bg_editor"]), 2)
                         for k, v in sorted(colors.items())},
        })
    return {
        "schema": "green-eye-palette/1",
        "brand": "Green Eye",
        "note": "平台无关的色值契约。生成来源：intellij/src/palette.py（单一真相）。",
        "anchor": "两款主题共用同一块底色 #1F3027；换平台时底色与对比度标准不变，"
                  "变的是'色相如何分配给语义'。",
        "roles": ROLE,
        "exceptions": collect_exceptions(),
        "themes": themes,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "palette.json"))
    ap.add_argument("--check", action="store_true",
                    help="只校验 JSON 与 palette.py 是否一致（不一致则 exit 1）")
    a = ap.parse_args()
    doc = build_doc()
    text = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    if a.check:
        if not os.path.exists(a.out):
            print("❌ 缺少 %s（先跑 make build 或本脚本不带 --check）" % a.out)
            return 1
        old = open(a.out, encoding="utf-8").read()
        if old != text:
            print("❌ shared/palette.json 与 intellij/src/palette.py 不一致 —— 重新导出")
            return 1
        print("✅ shared/palette.json 与调色板一致（%d 款主题）" % len(doc["themes"]))
        return 0
    open(a.out, "w", encoding="utf-8").write(text)
    n = sum(len(t["colors"]) for t in doc["themes"])
    print("写入 %s：%d 款主题、共 %d 个色值" % (os.path.relpath(a.out, ROOT), len(doc["themes"]), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
