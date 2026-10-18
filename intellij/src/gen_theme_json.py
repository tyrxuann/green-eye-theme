#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 IntelliJ IDEA 2026.2 的整站 UI 主题（.theme.json）并打包成可安装插件 jar。

要点（都是踩过坑之后定下的）：
  1. 方案放在 themes/ 下，用官方同款写法注册：
       <bundledColorScheme id="方案名" path="/themes/xxx.xml"/>
     主题 JSON 用**方案名**引用 editorScheme，**不用路径**
     （1.0.0 用路径引用 + 父方案名用了尚未注册的 "Light"，导致启动抛
       PluginException: InvalidDataException: Light）。
  2. parent_scheme 只能用核心平台内置名：官方浅色一律 Default、深色一律 Darcula。
  3. 面板/弹窗染色不能只靠继承父主题，否则大量控件还是官方色。
     这里把 Islands 的语义 token 全部按调色板重写，并额外写一张显式的 ui 覆盖表。
"""
import argparse
import colorsys
import json
import os
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES  # noqa: E402
from project_config import JAR_PREFIX, PLUGIN_ID, PLUGIN_NAME, THEME_SPECS, VERSION  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "build", "ref", "ide2026", "themes", "islands")
# 官方 Islands 的灰阶是"深→浅"的绝对色阶。
# 把 gray-* 做"保持明度、换成低饱和绿"的迁移，整个界面就会自然带绿。
RAMP_RULES = {
    "gray": (148.0, 0.075, 1.00),
    "blue": (168.0, None, 0.60),
    "teal": (168.0, None, 0.80),
    "green": (110.0, None, 0.85),
    "red": (8.0, None, 0.80),
    "yellow": (45.0, None, 0.80),
    "orange": (28.0, None, 0.80),
    "purple": (315.0, None, 0.80),
}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c * 255))) for c in rgb)


def shift_ramp(value, family):
    rule = RAMP_RULES.get(family)
    if not rule or not value or not value.startswith("#") or len(value) != 7:
        return value
    hue, target_sat, sat_scale = rule
    r, g, b = hex_to_rgb(value)
    _, l, s = colorsys.rgb_to_hls(r, g, b)
    new_s = target_sat if target_sat is not None else min(1.0, s * sat_scale)
    rr, gg, bb = colorsys.hls_to_rgb(hue / 360.0, l, new_s)
    return rgb_to_hex((rr, gg, bb))


def semantic_colors(pal):
    """把官方 Islands 的语义 token 全部映射到本主题调色板。"""
    accent = pal["accent"]
    accent_hover = pal["accent_hover"]
    return {
        "editor-bg": pal["bg_editor"], "editor-bg-inline": pal["bg_raised"],
        "editor-border": pal["separator"], "editor-border-alt": pal["separator"],
        "editor-border-inline": pal["separator"], "editor-text": pal["fg"],
        "main-window-bg": pal["ui_base"], "main-window-bg-alt": pal["bg_editor"],
        "main-window-border": pal["separator"],
        "tool-window-bg": pal["ui_base"], "tool-window-bg-alt": pal["bg_editor"],
        "tool-window-bg-inline": pal["bg_editor"],
        "tool-window-border": pal["separator"],
        "tool-window-border-inline": pal["separator"],
        "layer-0-bg": pal["bg_editor"], "layer-0-bg-inline": pal["bg_editor"],
        "layer-0-border": pal["separator"], "layer-0-border-inline": pal["separator"],
        "layer-1-bg": pal["ui_base"], "layer-1-bg-inline": pal["ui_base"],
        "layer-1-border": pal["separator"], "layer-1-border-inline": pal["separator"],
        "layer-2-bg": pal["ui_surface"], "layer-2-bg-inline": pal["ui_surface"],
        "layer-2-border": pal["border"], "layer-2-border-inline": pal["separator"],
        "popup-bg": pal["ui_surface"], "popup-bg-inline": pal["ui_surface"],
        "popup-border": pal["border"], "popup-border-inline": pal["border"],
        "dialog-bg": pal["ui_surface"], "dialog-bg-inline": pal["ui_surface"],
        "dialog-border": pal["border"],
        "text-default": pal["fg"], "text-secondary": pal["fg_dim"],
        "text-muted": pal["fg_dim"], "text-disabled": pal["line_numbers"],
        "text-link": pal["hyperlink"], "text-error": pal["error"],
        "text-warning": pal["warning"], "text-success": pal["string"],
        "text-over-accent": pal["fg_sel"], "text-over-accent-inverted": pal["bg_panel"],
        "selection-bg-active": pal["bg_selection"],
        "selection-bg-active-muted": pal["bg_caret_row"],
        "selection-bg-inactive": pal["ui_surface"],
        "selection-bg-hovered": pal["ui_hover"],
        "search-match-bg": pal["bg_search"],
        "popup-completion-match-text": pal["string"],
        "control-bg": pal["ui_surface"], "control-bg-raised": pal["ui_surface"],
        "control-bg-small": pal["ui_surface"], "control-bg-disabled": pal["ui_base"],
        "control-border": pal["border"], "control-border-raised": pal["border"],
        "control-border-small": pal["border"],
        "control-border-disabled": pal["right_margin"],
        "control-border-over-accent": pal["fg_sel"],
        "search-match-border": pal["search_border"],
        "control-brand-bg": accent, "control-brand-border": accent,
        "accent-brand-bg": accent, "accent-brand-bg-secondary": accent_hover,
        "accent-brand-border": accent, "accent-brand-border-secondary": accent_hover,
        "accent-neutral-bg": pal["ui_surface"],
        "accent-success-bg": pal["bg_diff_add"], "accent-success-bg-secondary": pal["bg_diff_add"],
        "accent-success-border": pal["string"], "accent-success-border-secondary": pal["string"],
        "accent-error-bg": pal["bg_diff_del"], "accent-error-bg-secondary": pal["bg_diff_del"],
        "accent-error-border": pal["error"], "accent-error-border-secondary": pal["error"],
        "accent-warning-bg": "#3A3524", "accent-warning-bg-secondary": "#3A3524",
        "accent-warning-border": pal["warning"], "accent-warning-border-secondary": pal["warning"],
        "accent-ai-bg": pal["ui_surface"], "accent-ai-border": pal["indent_guide"],
        "inlay-bg": pal["ui_surface"], "inlay-border": pal["border"],
        "tab-selected-bg-active": pal["bg_editor"],
        "tab-selected-bg-inactive": pal["bg_panel"],
        "tab-selected-border-active": pal["tab_underline"],
        "tab-selected-border-inactive": pal["indent_guide"],
        "tab-bg-hovered": pal["ui_hover"], "tab-file-color-mask-bg": pal["ui_surface"],
        "toolbar-bg-hovered": pal["ui_hover"], "toolbar-bg-pressed": pal["bg_selection"],
        "toolbar-border": pal["separator"], "toolbar-selected-bg": pal["bg_selection"],
        "toolbar-selected-bg-active": pal["bg_selection"],
        "toolbar-selected-bg-hovered": pal["bg_selection"],
        "toolbar-run-bg": accent, "toolbar-run-bg-hovered": accent_hover,
        "toolbar-stop-bg": pal["error"], "toolbar-stop-bg-hovered": "#FB9AA3",
        "feedback-bg": pal["ui_surface"], "feedback-bg-inline": pal["ui_surface"],
        "feedback-border": pal["border"],
        "feedback-error-bg": pal["bg_diff_del"], "feedback-error-border": pal["error"],
        "feedback-success-bg": pal["bg_diff_add"], "feedback-success-border": pal["string"],
        "feedback-warning-bg": "#3A3524", "feedback-warning-border": pal["warning"],
        "feedback-brand-bg": pal["bg_diff_add"], "feedback-brand-border": accent,
        "feedback-ai-bg": "#2C3A44", "feedback-ai-border": pal["indent_guide"],
        "got-it-bg": pal["ui_surface"], "got-it-border": pal["border"],
        "got-it-code-border": pal["indent_guide"], "got-it-text-link": pal["hyperlink"],
        "got-it-text-step": pal["string"], "got-it-shortcut-bg": pal["bg_selection"],
        "got-it-contrast-button-bg": pal["fg_sel"],
        "icon-default-stroke": pal["fg_dim"], "icon-over-accent": pal["fg_sel"],
        "icon-green-stroke": pal["string"],
        "tree-indent-guide-border": pal["separator"],
        "core-bg-transparent-hovered": "#FFFFFF12", "core-bg-transparent-pressed": "#FFFFFF1C",
        "core-border-transparent": "#FFFFFF00",
        "toggle-button-bg": pal["ui_surface"], "toggle-border": pal["indent_guide"],
        "toggle-off-bg": pal["ui_base"],
        # 只用官方主题里真实存在的命名色；此前自造的 blue/green/red… 属于无效 token
        "black": pal["bg_panel"], "white": pal["fg_sel"],
        "transparent": "#00000000",
    }


def ui_block(pal):
    """显式覆盖各大控件的界面色 —— 这是"面板/弹窗不再残留官方色"的关键。"""
    b, r, e = pal["ui_base"], pal["ui_surface"], pal["bg_editor"]
    bd, fg, dim = pal["separator"], pal["fg"], pal["fg_dim"]
    fl = pal["border"]   # 只用于浮层轮廓
    accent = pal["accent"]
    sel, selfg, dimmest = pal["bg_selection"], pal["fg_sel"], pal["line_numbers"]
    recent_project = {
        "Color%d" % i: {"MainToolbarGradientStart": b}
        for i in range(1, 10)
    }
    return {
        "*": {"background": r, "foreground": fg, "borderColor": bd,
              "disabledText": dimmest, "disabledForeground": dimmest,
              "inactiveForeground": dim, "selectionBackground": sel,
              "selectionForeground": selfg, "lightSelectionBackground": pal["bg_caret_row"],
              "selectionInactiveBackground": r, "selectionInactiveForeground": fg,
              "hoverBackground": pal["ui_hover"], "separatorColor": bd,
              "infoForeground": pal["hyperlink"], "acceleratorForeground": dim,
              "disabledBackground": b, "disabledBorderColor": pal["right_margin"]},
        "MainWindow.background": b,
        "MainWindow.Tab": {
            "background": b, "selectedBackground": e,
            "hoverBackground": pal["ui_hover"], "separatorColor": bd,
            "foreground": dim,
        },
        "Borders": {"color": bd, "ContrastBorderColor": bd},
        "Panel.background": b,
        "ToolWindow": {"background": b, "borderColor": bd,
                       "Header": {"background": b, "inactiveBackground": b, "borderColor": bd},
                       "HeaderTab": {"hoverBackground": pal["ui_hover"],
                                     "hoverInactiveBackground": pal["ui_hover"]},
                       "Stripe": {"background": b, "borderColor": bd, "separatorColor": bd},
                       "Button": {"foreground": dim, "hoverBackground": pal["ui_hover"],
                                  "selectedBackground": sel,
                                  "selectedForeground": selfg}},
        "ToolWindow.Button.foreground": dim,
        "ToolWindow.Button.hoverBackground": pal["ui_hover"],
        "ToolWindow.Button.selectedBackground": sel,
        "ToolWindow.Button.selectedForeground": selfg,
        "ToolWindow.HeaderTab.selectedBackground": e,
        "ToolWindow.HeaderTab.selectedInactiveBackground": b,
        "ToolWindow.Stripe.background": b,
        "ToolWindow.Stripe.borderColor": bd,
        "ToolWindow.Stripe.separatorColor": bd,
        "EditorTabs": {"background": b, "underlineColor": pal["tab_underline"],
                       "underTabsBorderColor": bd, "borderColor": bd,
                       "hoverBackground": r, "hoverInactiveBackground": r,
                       "inactiveColoredFileBackground": r,
                       "underlinedBorderColor": accent,
                       "underlinedTabBackground": pal["ui_hover"],
                       "underlinedTabBorderColor": pal["tab_underline"],  # 标签指示线
                       "inactiveUnderlinedTabBackground": b,
                       "inactiveUnderlinedTabBorderColor": bd},
        "Editor": {"background": e, "foreground": fg},
        "MainToolbar": {
            "background": b, "inactiveBackground": b, "borderColor": bd,
            "separatorColor": bd,
            "Dropdown.transparentHoverBackground": "#FFFFFF0C",
            "Icon.background": b, "Icon.pressedBackground": pal["ui_hover"],
        },
        "StatusBar": {
            "background": b, "borderColor": bd, "topBorderWidth": 0,
            "Breadcrumbs.foreground": dim, "Widget.foreground": dim,
            "Breadcrumbs.hoverBackground": pal["ui_hover"],
            "Breadcrumbs.selectionBackground": pal["ui_hover"],
            "Breadcrumbs.selectionInactiveBackground": pal["ui_hover"],
            "Widget.hoverBackground": pal["ui_hover"],
        },
        "TitlePane": {
            "background": b, "inactiveBackground": b,
            "infoForeground": fg, "inactiveInfoForeground": dim,
            "Button.hoverBackground": pal["ui_hover"],
        },
        "PopupMenu": {"background": r, "borderColor": fl, "separatorColor": bd},
        "Popup": {"background": r, "borderColor": fl},
        "Tree": {"background": r, "foreground": fg, "selectionBackground": sel,
                 "selectionForeground": selfg, "borderColor": bd,
                       "hoverBackground": pal["ui_hover"]},
        "List": {"background": r, "foreground": fg, "selectionBackground": sel,
                 "selectionForeground": selfg,
                     "selectionInactiveBackground": pal["ui_hover"],
                 "borderColor": bd, "hoverBackground": pal["bg_caret_row"]},
        "Table": {"background": r, "foreground": fg, "selectionBackground": sel,
                  "selectionForeground": selfg, "gridColor": bd, "borderColor": bd,
                  "stripeColor": "#1E2C27", "lightSelectionBackground": sel,
                  "lightSelectionForeground": selfg},
        "TextField": {"background": r, "foreground": fg, "borderColor": bd,
                      "caretColor": pal["fg"], "selectionBackground": sel,
                      "selectionForeground": selfg, "placeholderForeground": dim},
        "TextArea": {"background": r, "foreground": fg, "caretColor": pal["fg"],
                     "selectionBackground": sel, "selectionForeground": selfg},
        "ComboBox": {"background": r, "foreground": fg, "borderColor": bd,
                     "nonEditableBackground": r, "selectionBackground": sel,
                     "ArrowButton": {"iconColor": fg, "disabledIconColor": dim,
                                     "background": r, "nonEditableBackground": r}},
        "Button": {"foreground": fg, "startBackground": r, "endBackground": r,
                   "startBorderColor": bd, "endBorderColor": bd,
                   "default": {"foreground": selfg, "startBackground": accent,
                               "endBackground": accent, "startBorderColor": accent,
                               "endBorderColor": accent, "focusedBorderColor": selfg}},
        "CheckBox": {"background": b, "foreground": fg},
        "RadioButton": {"background": b, "foreground": fg},
        "Slider": {"background": r},
        "ProgressBar": {"background": r, "foreground": pal["string"],
                        "indeterminateStartColor": pal["string"],
                        "indeterminateEndColor": pal["function"]},
        "ScrollBar": {"background": r, "thumbColor": pal["line_numbers"],
                      "hoverThumbColor": dim, "trackColor": b,
                      "thumbBorderColor": b, "hoverTrackColor": b},
        "ScrollPane": {"background": r, "borderColor": bd},
        "Notification": {"background": r, "borderColor": bd, "foreground": fg},
        "SearchEverywhere": {"background": r, "borderColor": bd},
        "CompletionPopup": {"background": r, "borderColor": bd, "foreground": fg,
                            "selectionBackground": sel, "selectionForeground": selfg},
        "Breadcrumbs": {"background": b, "foreground": dim},
        "Menu": {"background": r, "foreground": fg, "borderColor": bd,
                 "selectionBackground": sel, "selectionForeground": selfg,
                 "separatorColor": bd},
        "MenuBar": {"background": b, "foreground": fg, "borderColor": bd},
        "MenuItem": {"background": r, "foreground": fg, "selectionBackground": sel,
                     "selectionForeground": selfg, "acceleratorForeground": dim},
        "Toolbar": {"background": b, "borderColor": bd},
        "Toolbar.Floating": {"background": r, "borderColor": bd},
        "Link": {"activeForeground": pal["hyperlink"], "hoverForeground": pal["hyperlink"],
                 "pressedForeground": pal["hyperlink"],
                 "visitedForeground": pal["hyperlink"]},
        "Label": {"background": b, "foreground": fg},
        "Separator": {"separatorColor": bd, "foreground": bd},
        "MemoryIndicator": {"allocatedBackground": r, "usedBackground": pal["line_numbers"]},
        "FileColor": {"Yellow": "#3A3524", "Green": pal["bg_diff_add"],
                      "Blue": pal["bg_diff_mod"], "Violet": "#382C3E",
                      "Orange": "#3A3325", "Rose": pal["bg_diff_del"]},
        "Counter": {"background": sel, "foreground": selfg},
        "TabbedPane": {"background": b, "foreground": fg, "borderColor": bd,
                       "selectionBackground": e, "selectionForeground": fg},
        "Debugger": {"background": e},
        # 下面这些键名都经过"官方主题里真实出现过"校验
        "AlertDialog.background": r,
        "Component": {"background": b, "foreground": fg},
        "WelcomeScreen": {
            "background": b, "headerBackground": b, "headerForeground": fg,
            "SidePanel.background": b, "Projects.background": b,
            "Projects.selectionBackground": sel,
            "Projects.selectionInactiveBackground": pal["ui_hover"],
            "Projects.actions.background": r,
            "Projects.actions.selectionBackground": sel,
            "Projects.actions.selectionBorderColor": accent,
            "separatorColor": bd,
        },
        "WelcomeScreen.Banner.background": r,
        "WelcomeScreen.Details.background": b,
        "WelcomeScreen.Projects.actions.background": r,
        "WelcomeScreen.Projects.actions.selectionBackground": sel,
        "WelcomeScreen.Projects.actions.selectionBorderColor": accent,
        "WelcomeScreen.Frame.DisclosureButton": {
            "defaultBackground": r,
            "hoverOverlay": "#FFFFFF0C",
            "pressedOverlay": "#FFFFFF14",
        },
        "RecentProject": recent_project,
        "SearchField": {"background": r, "borderColor": bd, "foreground": fg,
                        "errorBackground": pal["bg_diff_del"],
                        "errorForeground": pal["error"],
                        "infoForeground": pal["hyperlink"]},
        "PackageSearch": {"background": r, "borderColor": bd},
        "ComplexPopup": {"background": r, "borderColor": bd},
        "FindPopup": {"background": r, "borderColor": bd},
        "MarkerPopup": {"background": r, "borderColor": bd},
        "InplaceRefactoringPopup": {"background": r, "borderColor": bd},
    }


def icon_palette(pal):
    """图标调色板必须**随主题走** —— 否则另一款主题的 UI 图标会用着被淘汰的颜色。

    这些名字是 IDEA 图标体系的语义槽（Actions.Red / Objects.Green …），
    所以映射到当前主题的**同语义** token，而不是写死十六进制。
    """
    return {
        "Actions.Grey": pal["fg_dim"], "Actions.Red": pal["error"],
        "Actions.Yellow": pal["con_yellow"], "Actions.Green": pal["string"],
        "Actions.Blue": pal["function"],
        "Objects.Grey": pal["fg_dim"], "Objects.Red": pal["error"],
        "Objects.RedStatus": pal["error"], "Objects.Yellow": pal["con_yellow"],
        "Objects.Green": pal["string"], "Objects.Blue": pal["function"],
        "Objects.Purple": pal["annotation"], "Objects.Pink": pal["annotation"],
        "Objects.BlackText": pal["bg_panel"], "Objects.YellowDark": pal["info_stripe"],
        "Objects.GreenAndroid": pal["string"],
    }


def plugin_xml(entries):
    """entries: [(theme_id, theme_stem, scheme_name, scheme_stem), ...]

    照抄 JetBrains 官方做法（见 intellij.idea.ultimate.customization.jar 的 plugin.xml）：
      <bundledColorScheme id="Islands Dark" path="/themes/islands/IslandSchemeDark.xml"/>
      <themeProvider id="..." path="/themes/...theme.json"/>
    """
    providers = "\n".join(
        '    <bundledColorScheme id="%s" path="/themes/%s.xml"/>\n'
        '    <themeProvider id="%s" path="/themes/%s.theme.json"/>'
        % (scheme_name, scheme_stem, theme_id, theme_stem)
        for theme_id, theme_stem, scheme_name, scheme_stem in entries)
    return """<idea-plugin>
  <id>%s</id>
  <name>%s</name>
  <version>%s</version>
  <vendor>Green Eye（本地生成）</vendor>

  <description><![CDATA[
    绿色护眼主题，同一块苔绿底（#1F3027）上有两套设计语言：<br/>
    · <b>松林</b>：色相/饱和度照 JetBrains 官方 Islands Dark，只按对比度重解明度；<br/>
    · <b>矿彩</b>：以底色为中心的原创设计 —— 暖极（金黄→赭石→玫瑰）与
      冷极（冰青→紫晶→玉青）两支极色，正文层保持暖中性墨。<br/>
    编辑器配色方案已通过 &lt;bundledColorScheme&gt; 注册，装完即可在
    Theme 与 Color Scheme 两个下拉框里选到。
  ]]></description>

  <idea-version since-build="253"/>

  <depends>com.intellij.modules.platform</depends>

  <extensions defaultExtensionNs="com.intellij">
%s
  </extensions>
</idea-plugin>
""" % (PLUGIN_ID, PLUGIN_NAME, VERSION, providers)


def theme_json(pal, ref_path, editor_scheme):
    ref = json.load(open(ref_path, encoding="utf-8"))
    colors = {}
    for key, val in ref.get("colors", {}).items():
        family = key.split("-")[0]
        colors[key] = shift_ramp(val, family) if ("-" in key and family in RAMP_RULES) else val
    colors.update(semantic_colors(pal))
    return {
        # Theme 下拉框显示名带中文便于辨认；配色方案名（bundledColorScheme 的 id）
        # 保持 ASCII，避免被用作文本键/文件名时的编码问题
        "name": "%s %s" % (pal["name"], pal["label"]),
        "dark": bool(pal["dark"]),
        "author": "Green Eye",
        "parentTheme": ref["name"],
        "editorScheme": editor_scheme,
        "colors": colors,
        "ui": ui_block(pal),
        "iconColorsOnSelection": {"#767a8a": "#ffffff", "#6e6e6e": "#afb1b3"},
        "icons": {"ColorPalette": icon_palette(pal)},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iclsdir", default=os.path.join(HERE, "..", "themes"))
    ap.add_argument("--outdir", default=os.path.join(HERE, "..", "themes"))
    ap.add_argument("--dist", default=os.path.join(HERE, "..", "dist"))
    args = ap.parse_args()
    iclsdir, outdir, dist = (os.path.abspath(p) for p in
                             (args.iclsdir, args.outdir, args.dist))
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(dist, exist_ok=True)

    # 两款主题共用同一块苔绿底（#1F3027），但语义配色是两套设计语言：
    #   dark    「松林」 = 照官方色相/饱和度、只按对比度重解明度（"改皮不改骨"）
    #   mineral 「矿彩」 = 以底色为中心重新设计：暖极(金黄/赭石/玫瑰) + 冷极(冰青/紫晶/玉青)
    specs = [(key, os.path.join(REF, "ManyIslandsDark.theme.json"),
              theme_stem, scheme_stem, icls)
             for key, theme_stem, scheme_stem, icls in THEME_SPECS]
    stage = os.path.join(dist, "_stage")
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    os.makedirs(os.path.join(stage, "META-INF"))
    os.makedirs(os.path.join(stage, "themes"))

    providers = []
    for key, ref_path, stem, scheme_stem, icls in specs:
        pal = PALETTES[key]
        doc = theme_json(pal, ref_path, pal["name"])
        p = os.path.join(outdir, "%s.theme.json" % stem)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print("写入 %s  (colors=%d, ui 键=%d)"
              % (os.path.relpath(p), len(doc["colors"]), len(doc["ui"])))
        shutil.copy2(os.path.join(iclsdir, icls),
                     os.path.join(outdir, "%s.xml" % scheme_stem))
        shutil.copy2(os.path.join(iclsdir, icls),
                     os.path.join(stage, "themes", "%s.xml" % scheme_stem))
        shutil.copy2(p, os.path.join(stage, "themes", "%s.theme.json" % stem))
        providers.append(("green-eye-" + key, stem, pal["name"], scheme_stem))

    with open(os.path.join(stage, "META-INF", "plugin.xml"), "w",
              encoding="utf-8") as fh:
        fh.write(plugin_xml(providers))
    with open(os.path.join(stage, "META-INF", "pluginIcon.svg"), "w",
              encoding="utf-8") as fh:
        fh.write('<svg width="40" height="40" viewBox="0 0 40 40" '
                 'xmlns="http://www.w3.org/2000/svg">\n'
                 '  <rect width="40" height="40" rx="8" fill="#1F302B"/>\n'
                 '  <path d="M20 6c6 4 10 9 10 15a10 10 0 0 1-20 0c0-6 4-11 10-15z" '
                 'fill="#89BC90"/>\n'
                 '  <path d="M20 12v20" stroke="#1F302B" stroke-width="2" '
                 'stroke-linecap="round"/>\n</svg>\n')

    jar = os.path.join(dist, "%s%s.jar" % (JAR_PREFIX, VERSION))
    for old in os.listdir(dist):
        if old.startswith("GreenEye-Theme-") and old.endswith(".jar"):
            os.remove(os.path.join(dist, old))
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as zf:
        for base, _, files in os.walk(stage):
            for f in files:
                full = os.path.join(base, f)
                zf.write(full, os.path.relpath(full, stage))
    print("打包 %s  (%d 字节)" % (os.path.relpath(jar), os.path.getsize(jar)))
    shutil.rmtree(stage)
    return 0


if __name__ == "__main__":
    sys.exit(main())
