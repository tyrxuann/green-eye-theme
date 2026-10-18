#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量格式守门（不需要 black/ruff，环境里也没有）。

起因：`palette.py` 被手工编辑多次后出现"合并/复制滑移"——一个键缩进顶格、
两行注释被并到同一行尾巴上。语法仍然合法，reviewer 是靠肉眼看出来的。
这类问题的共同特征是**同一个字典里的键缩进不一致**，所以按结构查而不是按风格查。

三类检查：
  1. 所有 src/*.py 能被 py_compile 编译（语法）
  2. 同一个字典字面量里的键必须缩进到同一列
  3. 键值对尾巴上不允许堆叠多个 `#` 注释（合并滑移的特征）
"""
import ast
import io
import os
import py_compile
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_LEN = 118


def check_compile(path, src):
    try:
        compile(src, path, "exec")
        return []
    except SyntaxError as e:
        return ["%s:%s 语法错误 %s" % (os.path.basename(path), e.lineno, e.msg)]


def check_dict_indent(path, src):
    """同一个字典里，各"键所在行"的行首缩进必须一致。

    这才是"合并/复制滑移"的结构特征（某个键被顶格）。之前按 key.col_offset
    比较是错的：多行字典里值的续行本来就会落在不同列。
    """
    bad = []
    lines = src.splitlines()
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Dict) or len(node.keys) < 3:
            continue
        # 内联字典（同一行有多个键）的续行缩进本来就不一致，不参与检查
        key_lines = [k.lineno for k in node.keys if isinstance(k, ast.Constant)]
        if len(key_lines) != len(set(key_lines)):
            continue
        indents = set()
        for k in node.keys:
            if not isinstance(k, ast.Constant) or k.lineno - 1 >= len(lines):
                continue
            indents.add(len(lines[k.lineno - 1]) - len(lines[k.lineno - 1].lstrip()))
        if len(indents) > 1:
            bad.append("%s:%d 字典里键所在行的缩进不一致 %s（疑似合并/复制滑移）"
                       % (os.path.basename(path), node.lineno, sorted(indents)))
    return bad


def check_stacked_comments(path, src):
    """注释里出现 `  #`（两个空格后跟井号）= 两行注释被合并到一行。

    不能简单地数 `#`：十六进制色值本身就含 `#`（如 `# 官方 #402929`）。
    """
    bad = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT and "  #" in tok.string:
            bad.append("%s:%d 注释里出现第二个 `#`（疑似两行注释被合并）：%s"
                       % (os.path.basename(path), tok.start[0], tok.string[:70]))
    return bad


def check_length(path, src):
    return ["%s:%d 行过长（%d > %d）" % (os.path.basename(path), i, len(line), MAX_LEN)
            for i, line in enumerate(src.splitlines(), 1) if len(line) > MAX_LEN]


def main():
    problems = []
    paths = [os.path.join(HERE, f)
             for f in sorted(os.listdir(HERE)) if f.endswith(".py")]
    root_cli = os.path.abspath(os.path.join(HERE, "..", "..", "green_eye.py"))
    if os.path.isfile(root_cli):
        paths.append(root_cli)
    for sub in ("shared", "tests"):
        base = os.path.abspath(os.path.join(HERE, "..", "..", sub))
        for dirpath, _, names in os.walk(base):
            for name in sorted(names):
                if name.endswith(".py"):
                    paths.append(os.path.join(dirpath, name))
    paths = sorted(set(paths))
    for path in paths:
        src = open(path, encoding="utf-8").read()
        problems += check_compile(path, src)
        problems += check_dict_indent(path, src)
        problems += check_stacked_comments(path, src)
        problems += check_length(path, src)
    print("格式守门：%d 个源文件" % len(paths))
    if problems:
        print("  ❌ 发现 %d 处：" % len(problems))
        for p in problems:
            print("     - %s" % p)
        return 1
    print("  ✅ 语法可编译 · 字典键缩进一致 · 无堆叠注释 · 无超长行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
