#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把平台无关的 shared/palette.json 映射成 VS Code 主题。

原则与 IntelliJ 侧一致：
  · 彩色只留给语义（keyword/string/number/function/constant/annotation/todo）；
  · 不给 punctuation / operator / bracket 单独上色；
  · 底色、正文、选中、查找、diff 等直接取契约里的槽位，不重新调色。
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VSCODE = HERE.parent
ROOT = VSCODE.parent
PALETTE = ROOT / "shared" / "palette.json"
OUTDIR = VSCODE / "themes"


def _pick(pal, key):
    try:
        return pal[key]
    except KeyError as exc:
        raise SystemExit("palette 缺少槽位: %s" % key) from exc


def colors(pal):
    """语义槽位 → VS Code 工作台颜色键。"""
    p = lambda key: _pick(pal, key)  # noqa: E731
    return {
        "editor.background": p("bg_editor"),
        "editor.foreground": p("fg"),
        "foreground": p("fg"),
        "descriptionForeground": p("fg_dim"),
        "disabledForeground": p("fg_dim"),
        "widget.border": p("border"),
        "editorCursor.foreground": p("caret"),
        "editor.lineHighlightBackground": p("bg_caret_row"),
        "editor.selectionBackground": p("bg_selection"),
        "editor.selectionForeground": p("fg_sel"),
        "editor.inactiveSelectionBackground": p("bg_selection"),
        "editor.selectionHighlightBackground": p("bg_selection"),
        "editor.selectionHighlightBorder": p("search_border"),
        "editor.findMatchBackground": p("bg_search"),
        "editor.findMatchBorder": p("search_border"),
        "editor.findMatchHighlightBackground": p("bg_search_current"),
        "editor.findRangeHighlightBackground": p("bg_search_current"),
        "editor.wordHighlightBackground": p("bg_identifier_caret"),
        "editor.wordHighlightStrongBackground": p("bg_identifier_write"),
        "editorBracketMatch.background": p("bg_matched_brace"),
        "editorBracketMatch.border": p("border"),
        "editorLineNumber.foreground": p("line_numbers"),
        "editorLineNumber.activeForeground": p("line_numbers_active"),
        "editorGutter.background": p("bg_gutter"),
        "editorGutter.addedBackground": p("search_border"),
        "editorGutter.modifiedBackground": p("warning"),
        "editorGutter.deletedBackground": p("error"),
        "editorIndentGuide.background1": p("indent_guide"),
        "editorIndentGuide.activeBackground1": p("whitespace"),
        "editorWhitespace.foreground": p("whitespace"),
        "editorRuler.foreground": p("right_margin"),
        "editorOverviewRuler.border": p("separator"),
        "diffEditor.insertedTextBackground": p("bg_diff_add"),
        "diffEditor.removedTextBackground": p("bg_diff_del"),
        "diffEditor.diagonalFill": p("bg_diff_mod"),
        "diffEditor.border": p("separator"),
        "editorError.foreground": p("error"),
        "editorWarning.foreground": p("warning"),
        "editorInfo.foreground": p("info"),
        "editorHint.foreground": p("fg_dim"),
        "editorLink.activeForeground": p("hyperlink"),
        "sideBar.background": p("bg_panel"),
        "sideBar.foreground": p("fg_dim"),
        "sideBar.border": p("separator"),
        "sideBarSectionHeader.background": p("bg_panel"),
        "sideBarSectionHeader.foreground": p("fg"),
        "activityBar.background": p("ui_base"),
        "activityBar.foreground": p("fg"),
        "activityBar.inactiveForeground": p("fg_dim"),
        "activityBar.border": p("separator"),
        "activityBarBadge.background": p("accent"),
        "activityBarBadge.foreground": p("fg_sel"),
        "statusBar.background": p("ui_base"),
        "statusBar.foreground": p("fg"),
        "statusBarItem.hoverBackground": p("ui_hover"),
        "statusBarItem.activeBackground": p("ui_hover"),
        "statusBar.noFolderBackground": p("bg_panel"),
        "statusBar.border": p("separator"),
        "titleBar.activeBackground": p("ui_base"),
        "titleBar.activeForeground": p("fg"),
        "titleBar.inactiveBackground": p("ui_base"),
        "titleBar.inactiveForeground": p("fg_dim"),
        "titleBar.border": p("separator"),
        "panel.background": p("bg_panel"),
        "panel.border": p("border"),
        "panelTitle.activeForeground": p("fg"),
        "panelTitle.inactiveForeground": p("fg_dim"),
        "editorGroup.border": p("separator"),
        "editorGroupHeader.tabsBackground": p("bg_panel"),
        "editorGroupHeader.noTabsBackground": p("bg_editor"),
        "tab.activeBackground": p("bg_editor"),
        "tab.activeForeground": p("fg"),
        "tab.inactiveBackground": p("bg_panel"),
        "tab.inactiveForeground": p("fg_dim"),
        "tab.border": p("separator"),
        "tab.activeBorderTop": p("tab_underline"),
        "editorWidget.background": p("bg_raised"),
        "editorWidget.border": p("border"),
        "editorWidget.foreground": p("fg"),
        "quickInput.background": p("bg_raised"),
        "quickInput.foreground": p("fg"),
        "editorSuggestWidget.background": p("bg_raised"),
        "editorSuggestWidget.border": p("border"),
        "editorSuggestWidget.foreground": p("fg"),
        "editorSuggestWidget.selectedBackground": p("bg_selection"),
        "editorSuggestWidget.highlightForeground": p("accent"),
        "list.hoverBackground": p("ui_hover"),
        "list.activeSelectionBackground": p("bg_selection"),
        "list.activeSelectionForeground": p("fg_sel"),
        "list.inactiveSelectionBackground": p("bg_panel"),
        "list.inactiveSelectionForeground": p("fg"),
        "list.focusBackground": p("bg_selection"),
        "list.highlightForeground": p("accent"),
        "input.background": p("ui_surface"),
        "input.foreground": p("fg"),
        "input.border": p("border"),
        "input.placeholderForeground": p("fg_dim"),
        "focusBorder": p("accent"),
        "button.background": p("accent"),
        "button.foreground": p("fg_sel"),
        "button.hoverBackground": p("accent_hover"),
        "badge.background": p("accent"),
        "badge.foreground": p("fg_sel"),
        "progressBar.background": p("accent"),
        "scrollbarSlider.background": p("ui_hover"),
        "scrollbarSlider.hoverBackground": p("accent"),
        "scrollbarSlider.activeBackground": p("accent_hover"),
        "minimap.background": p("bg_editor"),
        "breadcrumb.background": p("bg_breadcrumb"),
        "breadcrumb.foreground": p("fg_dim"),
        "breadcrumb.focusForeground": p("fg"),
        "breadcrumb.activeSelectionForeground": p("fg"),
        "terminal.background": p("bg_console"),
        "terminal.foreground": p("fg"),
        "terminalCursor.foreground": p("caret"),
        "terminal.ansiBlack": p("con_black"),
        "terminal.ansiRed": p("con_red"),
        "terminal.ansiGreen": p("con_green"),
        "terminal.ansiYellow": p("con_yellow"),
        "terminal.ansiBlue": p("con_blue"),
        "terminal.ansiMagenta": p("con_magenta"),
        "terminal.ansiCyan": p("con_cyan"),
        "terminal.ansiWhite": p("con_white"),
        "terminal.ansiBrightBlack": p("con_darkgray"),
        "terminal.ansiBrightRed": p("con_lightred"),
        "terminal.ansiBrightGreen": p("con_lightgreen"),
        "terminal.ansiBrightYellow": p("con_lightyellow"),
        "terminal.ansiBrightBlue": p("con_lightblue"),
        "terminal.ansiBrightMagenta": p("con_lightmagenta"),
        "terminal.ansiBrightCyan": p("con_lightcyan"),
        "terminal.ansiBrightWhite": p("con_lightgray"),
        "gitDecoration.conflictingResourceForeground": p("vcs_conflict"),
        "gitDecoration.deletedResourceForeground": p("vcs_deleted"),
        "gitDecoration.modifiedResourceForeground": p("warning"),
        "gitDecoration.untrackedResourceForeground": p("string"),
        "gitDecoration.ignoredResourceForeground": p("fg_dim"),
        "gitDecoration.addedResourceForeground": p("string"),
        "gitDecoration.renamedResourceForeground": p("info"),
        "textLink.foreground": p("doc_link"),
        "textLink.activeForeground": p("hyperlink"),
        "notifications.background": p("bg_raised"),
        "notifications.border": p("border"),
        "notifications.foreground": p("fg"),
        "debugToolBar.background": p("bg_raised"),
        "debugConsole.infoForeground": p("info"),
        "debugConsole.errorForeground": p("error"),
        "debugConsole.warningForeground": p("warning"),
        "editorHoverWidget.background": p("bg_raised"),
        "editorHoverWidget.border": p("border"),
        "editorHoverWidget.foreground": p("fg"),
        "peekView.border": p("border"),
        "peekViewEditor.background": p("bg_editor"),
        "peekViewResult.background": p("bg_panel"),
        "peekViewTitle.background": p("bg_raised"),
    }


def token_colors(pal):
    """语义槽位 → TextMate scope。不要给 punctuation/operator/bracket 上色。"""
    def rule(scopes, key, style=""):
        settings = {"foreground": _pick(pal, key)}
        if style:
            settings["fontStyle"] = style
        return {"scope": scopes, "settings": settings}

    return [
        rule(["comment", "punctuation.definition.comment"], "comment"),
        rule(["comment.block.documentation",
              "comment.block.documentation.python"], "doc_comment", "italic"),
        rule(["comment.block.documentation keyword",
              "storage.type.class.jsdoc",
              "entity.name.tag.jsdoc"], "doc_tag", "underline"),
        rule(["keyword", "storage.type", "storage.modifier",
              "keyword.control"], "keyword"),
        rule(["string", "string.quoted", "string.template"], "string"),
        rule(["meta.tag.attributes string",
              "meta.attribute-selector string",
              "string.quoted.double.html",
              "string.quoted.single.css"], "attr_value"),
        rule(["constant.numeric"], "number"),
        rule(["variable.other.constant", "variable.other.enummember",
              "support.constant"], "constant", "italic"),
        rule(["entity.name.function", "support.function",
              "variable.function"], "function"),
        rule(["entity.name.type.annotation", "storage.type.annotation",
              "entity.name.function.decorator"], "annotation"),
        rule(["constant.character.escape"], "escape"),
        rule(["markup.underline.link", "string.other.link"], "doc_link"),
        rule(["invalid", "invalid.illegal"], "error"),
        rule(["invalid.deprecated", "invalid.broken"], "warning"),
        rule(["keyword.other.todo", "comment.line.todo",
              "comment.block.todo"], "todo", "italic"),
    ]


def theme_doc(theme):
    return {
        "name": "%s %s" % (theme["name"], theme["label"]),
        "type": "dark",
        "semanticHighlighting": True,
        "colors": colors(theme["colors"]),
        "tokenColors": token_colors(theme["colors"]),
    }


def generate(outdir=None):
    if not PALETTE.is_file():
        print("缺少 %s；先运行 green_eye.py palette。" % PALETTE, file=sys.stderr)
        return 1
    data = json.loads(PALETTE.read_text(encoding="utf-8"))
    out = Path(outdir).expanduser() if outdir else OUTDIR
    out.mkdir(parents=True, exist_ok=True)
    for theme in data["themes"]:
        path = out / ("green-eye-%s.json" % theme["id"])
        text = json.dumps(theme_doc(theme), ensure_ascii=False, indent=2) + "\n"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("写入 %s" % path)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="生成 VS Code 主题")
    ap.add_argument("--outdir")
    args = ap.parse_args(argv)
    return generate(args.outdir)


if __name__ == "__main__":
    sys.exit(main())
