#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 IntelliJ IDEA 的 .icls 编辑器配色方案（护眼绿色系）。

用法:
    python3 gen_icls.py --names ../build/ref/all_reference_attribute_names.txt \
                        --outdir ../themes --check

属性名清单来自真实主题（Everforest for JetBrains / JetBrains GitHub Theme）抽取的
TextAttributesKey 外部名集合，因此覆盖率高、名字均为真实存在的键。
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES, contrast, scheme_stem  # noqa: E402

# ---------------------------------------------------------------------------
# 兜底属性名清单（无参考清单时使用）
# ---------------------------------------------------------------------------
FALLBACK_NAMES = """
TEXT DEFAULT_IDENTIFIER DEFAULT_KEYWORD DEFAULT_STRING DEFAULT_NUMBER
DEFAULT_LINE_COMMENT DEFAULT_BLOCK_COMMENT DEFAULT_DOC_COMMENT
DEFAULT_DOC_COMMENT_TAG DEFAULT_DOC_COMMENT_TAG_VALUE DEFAULT_DOC_MARKUP
DEFAULT_OPERATION_SIGN DEFAULT_BRACES DEFAULT_BRACKETS DEFAULT_PARENTHS
DEFAULT_SEMICOLON DEFAULT_COMMA DEFAULT_DOT
DEFAULT_CLASS_NAME DEFAULT_INTERFACE_NAME DEFAULT_CLASS_REFERENCE
DEFAULT_FUNCTION_DECLARATION DEFAULT_FUNCTION_CALL DEFAULT_PARAMETER
DEFAULT_LOCAL_VARIABLE DEFAULT_GLOBAL_VARIABLE DEFAULT_INSTANCE_FIELD
DEFAULT_STATIC_FIELD DEFAULT_CONSTANT DEFAULT_METADATA
DEFAULT_TAG DEFAULT_ATTRIBUTE DEFAULT_ENTITY
DEFAULT_VALID_STRING_ESCAPE DEFAULT_INVALID_STRING_ESCAPE
ERRORS_ATTRIBUTES WARNING_ATTRIBUTES WEAK_WARNING_ATTRIBUTES INFO_ATTRIBUTES
TODO_DEFAULT_ATTRIBUTES SEARCH_RESULT_ATTRIBUTES TEXT_SEARCH_RESULT_ATTRIBUTES
IDENTIFIER_UNDER_CARET_ATTRIBUTES MATCHED_BRACE_ATTRIBUTES
UNMATCHED_BRACE_ATTRIBUTES FOLDED_TEXT_ATTRIBUTES HYPERLINK_ATTRIBUTES
BOOKMARKS_ATTRIBUTES CONSOLE_NORMAL_OUTPUT CONSOLE_ERROR_OUTPUT
CONSOLE_USER_INPUT CONSOLE_SYSTEM_OUTPUT DIFF_INSERTED DIFF_DELETED
DIFF_MODIFIED DIFF_CONFLICT BAD_CHARACTER RUNTIME_ERROR GRAMMAR_ERROR
""".split()

# ---------------------------------------------------------------------------
# 显式指定（优先级最高）：名字 -> (前景键, 样式, 背景键)
# 样式: b=加粗, i=斜体, s=删除线, u=下划线, w=波浪线, box=方框
# ---------------------------------------------------------------------------
EXPLICIT = {
    "TEXT": ("fg", "", "bg_editor"),
    "DEFAULT_IDENTIFIER": ("fg", ""),
    "DEFAULT_KEYWORD": ("keyword", ""),        # 官方不加粗
    "DEFAULT_STRING": ("string", ""),
    "DEFAULT_NUMBER": ("number", ""),
    "DEFAULT_LINE_COMMENT": ("comment", ""),  # 官方行注释不斜体
    "DEFAULT_BLOCK_COMMENT": ("comment", ""), # 官方块注释不斜体
    "DEFAULT_DOC_COMMENT": ("doc_comment", "i"),
    "DEFAULT_DOC_COMMENT_TAG_VALUE": ("string", ""),
    "DEFAULT_DOC_MARKUP": ("comment", ""),
    "DEFAULT_OPERATION_SIGN": ("operator", ""),
    "DEFAULT_BRACES": ("brace", ""),
    "DEFAULT_BRACKETS": ("brace", ""),
    "DEFAULT_PARENTHS": ("brace", ""),
    "DEFAULT_SEMICOLON": ("punctuation", ""),
    "DEFAULT_COMMA": ("punctuation", ""),
    "DEFAULT_DOT": ("punctuation", ""),
    "DEFAULT_CLASS_NAME": ("class_name", ""),
    "DEFAULT_INTERFACE_NAME": ("interface_name", ""),
    "DEFAULT_CLASS_REFERENCE": ("class_name", ""),
    "DEFAULT_FUNCTION_DECLARATION": ("function", ""),
    "DEFAULT_FUNCTION_CALL": ("function_call", ""),
    "DEFAULT_INSTANCE_METHOD": ("function", ""),
    "DEFAULT_STATIC_METHOD": ("function", "i"),   # 官方静态方法斜体
    "STATIC_METHOD_ATTRIBUTES": ("function", "i"),   # 与规范键同族，必须同斜体
    # 按参考（Darcula）保真优先，与通用族的排版不同 —— 已在族规则里写明豁免
    "VELOCITY_KEYWORD": ("keyword", "b"),
    "HAML_TAG": ("tag", ""),
    "DEBUGGER_INLINED_VALUES": ("fg", "i"),
    "PHP_STATIC_METHOD": ("function", "i"),
    "PHP_STATIC_FIELD": ("static_field", "i"),
    "DEFAULT_PARAMETER": ("parameter", ""),
    "DEFAULT_LOCAL_VARIABLE": ("local_var", ""),
    "DEFAULT_GLOBAL_VARIABLE": ("local_var", ""),
    "DEFAULT_REASSIGNED_LOCAL_VARIABLE": ("fg", "u"),
    "DEFAULT_REASSIGNED_PARAMETER": ("fg", "u"),
    "DEFAULT_INSTANCE_FIELD": ("field", ""),
    "DEFAULT_STATIC_FIELD": ("static_field", "i"),
    "DEFAULT_CONSTANT": ("constant", "i"),       # 官方常量斜体
    "DEFAULT_METADATA": ("annotation", ""),
    "DEFAULT_TAG": ("tag", "b"),
    "DEFAULT_ATTRIBUTE": ("attr_name", ""),
    "DEFAULT_ENTITY": ("constant", ""),
    "DEFAULT_LABEL": ("con_cyan", ""),
    "DEFAULT_PREDEFINED_SYMBOL": ("constant", ""),
    "DEFAULT_VALID_STRING_ESCAPE": ("escape", ""),
    "DEFAULT_INVALID_STRING_ESCAPE": ("error", "w"),
    # 语义状态
    "ERRORS_ATTRIBUTES": ("error", "w"),
    "WARNING_ATTRIBUTES": ("warning", "w"),
    "WEAK_WARNING_ATTRIBUTES": ("warning", "w"),
    "INFO_ATTRIBUTES": ("info", "w"),
    "GENERIC_SERVER_ERROR_OR_WARNING": ("warning", "u"),
    "TEXT_STYLE_ERROR": ("error", "box"),
    "TEXT_STYLE_WARNING": ("warning", "box"),
    "TEXT_STYLE_SUGGESTION": ("info", "w"),
    "DEPRECATED_ATTRIBUTES": ("deprecated", "s"),
    "MARKED_FOR_REMOVAL_ATTRIBUTES": ("deprecated", "s"),
    "NOT_USED_ELEMENT_ATTRIBUTES": ("deprecated", ""),
    "WRONG_REFERENCES_ATTRIBUTES": ("error", "w"),
    "DUPLICATE_FROM_SERVER": ("error", "w"),
    "TODO_DEFAULT_ATTRIBUTES": ("todo", "i"), # 官方 TODO 是斜体
    "UNMATCHED_BRACE_ATTRIBUTES": ("error", "w", "bg_matched_brace"),
    "MATCHED_BRACE_ATTRIBUTES": ("fg", "b", "bg_matched_brace"),
    "FOLDED_TEXT_ATTRIBUTES": ("fg_dim", "b", "bg_folded_text"),
    "HYPERLINK_ATTRIBUTES": ("hyperlink", "u"),
    "FOLLOWED_HYPERLINK_ATTRIBUTES": ("followed_link", "u"),
    "BOOKMARKS_ATTRIBUTES": ("bookmark", "b", "bg_folded"),
    "SEARCH_RESULT_ATTRIBUTES": ("fg_search", "", "bg_search"),
    "TEXT_SEARCH_RESULT_ATTRIBUTES": ("fg_search", "", "bg_search_current"),
    "WRITE_SEARCH_RESULT_ATTRIBUTES": ("fg_search", "b", "bg_search"),
    "LIVE_TEMPLATE_ATTRIBUTES": ("fg", "", "bg_matched_brace"),
    "LIVE_TEMPLATE_INACTIVE_SEGMENT": ("fg_dim", "box", "bg_matched_brace"),
    "TEMPLATE_VARIABLE_ATTRIBUTES": ("fg", "", "bg_matched_brace"),  # 官方该键无 FONT_TYPE
    "DELETED_TEXT_ATTRIBUTES": ("fg", "s", "bg_diff_del"),   # 原为红上红 3.69:1；官方用中性灰
    # 控制台输出流（必须显式指定，否则会被通用 CONSOLE 规则截获）
    "CONSOLE_NORMAL_OUTPUT": ("fg", ""),
    "CONSOLE_ERROR_OUTPUT": ("con_red", ""),
    "CONSOLE_USER_INPUT": ("keyword", "i"),   # 官方该键斜体
    "CONSOLE_SYSTEM_OUTPUT": ("con_cyan", ""),
    "LOG_ERROR_OUTPUT": ("con_red", ""),
    "LOG_WARNING_OUTPUT": ("con_yellow", ""),
    "LOG_INFO_OUTPUT": ("fg_dim", ""),
    "LOG_VERBOSE_OUTPUT": ("fg_dim", ""),
    "LOG_DEBUG_OUTPUT": ("fg_dim", ""),
    "LOG_EXPIRED_ENTRY": ("fg_dim", "s"),
    # ---- 官方定义了 BACKGROUND 而我们缺失的键（17 个，含调试器 3 个关键项）----
    "IDENTIFIER_UNDER_CARET_ATTRIBUTES": ("fg", "u", "bg_identifier_caret"),
    "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES": ("fg", "u", "bg_identifier_write"),
    "READ_IDENTIFIER_UNDER_CARET_ATTRIBUTES": ("fg", "u", "bg_identifier_caret"),
    "EXECUTIONPOINT_ATTRIBUTES": ("fg", "", "bg_execution_point"),
    "BREAKPOINT_ATTRIBUTES": ("fg", "", "bg_breakpoint"),
    "NOT_TOP_FRAME_ATTRIBUTES": ("fg", "", "bg_not_top_frame"),
    "DOC_CODE_INLINE": ("doc_tag", "", "bg_doc_code"),
    "DOC_CODE_BLOCK": ("doc_comment", "", "bg_doc_code_block"),
    "BREADCRUMBS_CURRENT": ("fg", "", "bg_breadcrumb"),
    "BREADCRUMBS_HOVERED": ("fg", "", "bg_breadcrumb"),
    "INLAY_DEFAULT": ("fg_dim", "", "bg_inlay_hint"),
    "INJECTED_LANGUAGE_FRAGMENT": ("fg", "", "bg_injected"),
    "KOTLIN_SMART_CAST_RECEIVER": ("fg", "", "bg_smart_cast"),
    "KOTLIN_SMART_CAST_VALUE": ("fg", "", "bg_smart_cast"),
    "KOTLIN_SMART_CONSTANT": ("doc_tag", "", "bg_smart_cast"),
    "MATCHED_TAG_NAME": ("fg", "b", "bg_matched_tag"),
    "QUTE_BACKGROUND": ("fg", "", "bg_panel"),
    "DEFAULT_TEMPLATE_LANGUAGE_COLOR": ("fg", "", "bg_panel"),
    # ---- 官方用可读键名（含空格）的键：早先被我的采集脚本过滤掉了 ----
    "Unresolved reference access": ("fg_dim", "box"),   # 官方 ET=5 + EC=#6a707a
    "Static method access": ("function", "i"),
    "Static property reference ID": ("constant", "i"),
    "List/map to object conversion": ("fg", ""),
    # ---- 官方用 ET=1（实线下划线）的键：少一个都会在真机里丢掉下划线 ----
    "DEFAULT_DOC_COMMENT_TAG": ("doc_tag", "u"),          # 官方 FG=#67a37c + 下划线，不是注解橄榄
    "PROPERTIES.KEY": ("keyword", "u"),                    # 官方 FG=#cf8e6d + 下划线
    "CTRL_CLICKABLE": ("hyperlink", "u"),
    "DEFAULT_HIGHLIGHTED_REFERENCE": ("fg", "u"),
    "ANNOTATION_ATTRIBUTE_NAME_ATTRIBUTES": ("fg", "u"),
    "CUSTOM_KEYWORD4_ATTRIBUTES": ("annotation", "u"),
    "KOTLIN_MUTABLE_VARIABLE": ("fg", "u"),
    "IMPLICIT_ANONYMOUS_CLASS_PARAMETER_ATTRIBUTES": ("constant", "u"),
    "INACTIVE_HYPERLINK_ATTRIBUTES": ("fg_dim", "u"),
    # inlay hint（参数名提示）：官方给了底色，否则提示会直接压在代码上
    "INLINE_PARAMETER_HINT": ("fg_dim", "", "bg_inlay_hint"),
    "INLINE_PARAMETER_HINT_HIGHLIGHTED": ("fg", "", "bg_inlay_hint_highlighted"),
    "INLINE_PARAMETER_HINT_CURRENT": ("hint_current", "", "bg_inlay_hint_current"),
    "InlayHints.text.attributes": ("fg_dim", "", "bg_inlay_hint"),
    # Java 类成员
    "ABSTRACT_CLASS_NAME_ATTRIBUTES": ("class_name", "i"),
    "ENUM_NAME_ATTRIBUTES": ("enum_name", ""),
    "INTERFACE_NAME_ATTRIBUTES": ("interface_name", ""),
    "TYPE_PARAMETER_NAME_ATTRIBUTES": ("type_param", ""),
    "STATIC_FINAL_FIELD_ATTRIBUTES": ("static_field", "i"),
    "STATIC_FIELD_ATTRIBUTES": ("static_field", "i"),
    "INSTANCE_FIELD_ATTRIBUTES": ("field", ""),
    "CLASS_NAME_ATTRIBUTES": ("class_name", ""),
    "ANNOTATION_NAME_ATTRIBUTES": ("annotation", ""),
    "LOCAL_VARIABLE_ATTRIBUTES": ("local_var", ""),
    "PARAMETER_ATTRIBUTES": ("parameter", ""),
    # 标记语言
    "XML_TAG": ("keyword", ""),
    "XML_TAG_NAME": ("keyword", ""),
    "XML_TAG_DATA": ("fg", ""),
    "XML_ATTRIBUTE_NAME": ("annotation", ""),
    "XML_ATTRIBUTE_VALUE": ("string", ""),
    "XML_ENTITY_REFERENCE": ("constant", ""),
    "XML_COMMENT": ("comment", ""),
    "XML_PROLOGUE": ("fg_dim", ""),
    "XML_NS_PREFIX": ("constant", ""),
    "XML_CUSTOM_TAG_NAME": ("keyword", ""),
    "HTML_TAG": ("keyword", ""),
    "HTML_TAG_NAME": ("keyword", ""),
    "HTML_ATTRIBUTE_NAME": ("annotation", ""),
    "HTML_CUSTOM_TAG_NAME": ("keyword", ""),
    "HTML_ENTITY_REFERENCE": ("constant", ""),
    "HTML_CODE": ("escape", ""),
    "MARKDOWN_TEXT": ("fg", ""),
    "MARKDOWN_HEADER_LEVEL_1": ("keyword", ""),
    "MARKDOWN_HEADER_LEVEL_2": ("keyword", ""),
    "MARKDOWN_HEADER_LEVEL_3": ("keyword", ""),
    "MARKDOWN_HEADER_LEVEL_4": ("keyword", ""),
    "MARKDOWN_HEADER_LEVEL_5": ("keyword", ""),
    "MARKDOWN_HEADER_LEVEL_6": ("keyword", ""),
    "MARKDOWN_HEADER_MARKER": ("punctuation", ""),
    "MARKDOWN_BOLD": ("fg", "b"),
    "MARKDOWN_BOLD_MARKER": ("punctuation", ""),
    "MARKDOWN_ITALIC": ("fg", "i"),
    "MARKDOWN_ITALIC_MARKER": ("punctuation", ""),
    "MARKDOWN_STRIKE_THROUGH": ("deprecated", "s"),
    "MARKDOWN_CODE_SPAN": ("string", ""),
    "MARKDOWN_CODE_BLOCK": ("string", ""),
    "MARKDOWN_CODE_FENCE": ("punctuation", ""),
    "MARKDOWN_CODE_SPAN_MARKER": ("punctuation", ""),
    "MARKDOWN_LINK_TEXT": ("hyperlink", "u"),
    "MARKDOWN_AUTO_LINK": ("hyperlink", "u"),
    "MARKDOWN_EXPLICIT_LINK": ("hyperlink", "u"),
    "MARKDOWN_REFERENCE_LINK": ("hyperlink", "u"),
    "MARKDOWN_LINK_DESTINATION": ("string", ""),
    "MARKDOWN_LINK_TITLE": ("string", "i"),
    "MARKDOWN_LINK_LABEL": ("attr_name", ""),
    "MARKDOWN_BLOCK_QUOTE": ("comment", "i"),
    "MARKDOWN_BLOCK_QUOTE_MARKER": ("comment", "i"),
    "MARKDOWN_LIST_MARKER": ("punctuation", ""),
    "MARKDOWN_LIST_ITEM": ("fg", ""),
    "MARKDOWN_ORDERED_LIST": ("fg", ""),
    "MARKDOWN_UNORDERED_LIST": ("fg", ""),
    "MARKDOWN_HRULE": ("punctuation", ""),
    "MARKDOWN_TABLE_SEPARATOR": ("punctuation", ""),
    "MARKDOWN_IMAGE": ("tag", ""),
    "MARKDOWN_HTML_BLOCK": ("tag", ""),
    "MARKDOWN_INLINE_HTML": ("tag", ""),
}

# ---------------------------------------------------------------------------
# 正则规则（按顺序匹配，先命中先用）
# ---------------------------------------------------------------------------
RULES = [
    # 注释 / 文档
    (r"DOC.*COMMENT.*TAG|DOC_COMMENT_TAG|COMMENT.*TAG", "annotation", "b", None),
    (r"DOC.*COMMENT|DOCUMENTATION", "doc_comment", "", None),
    (r"^IGNORE\.", "comment", "i", None),
    (r"SHEBANG", "comment", "i", None),
    (r"COMMENT", "comment", "", None),
    (r"TODO|FIXME", "todo", "b", None),
    # 版本控制 / 差异
    (r"DIFF_INSERTED|INSERTED|_ADDED$|ADDED_LINES", "con_green", "", "bg_diff_add"),
    (r"DIFF_DELETED|_DELETED$|DELETED_LINES", "con_red", "", "bg_diff_del"),
    (r"DIFF_MODIFIED|MODIFIED", "con_blue", "", "bg_diff_mod"),
    (r"DIFF_CONFLICT|CONFLICT", "warning", "b", "bg_diff_mod"),
    (r"DIFF_SEPARATOR|SEPARATOR", "fg_dim", "", None),
    (r"^FILESTATUS_ADDED|addedOutside", "con_green", "", None),
    (r"^FILESTATUS_DELETED|DELETED_FROM_FILE_SYSTEM", "con_red", "", None),
    (r"^FILESTATUS_MODIFIED|modifiedOutside", "con_blue", "", None),
    (r"^FILESTATUS_MERGED|MERGED_WITH", "con_magenta", "", None),
    (r"FILESTATUS.*CONFLICT", "warning", "b", None),
    (r"^FILESTATUS_|^VCS_ANNOTATIONS", "fg_dim", "", None),
    # 错误 / 警告
    (r"UNMATCHED.*BRACE", "error", "w", "bg_matched_brace"),
    (r"MATCHED.*BRACE", "fg", "b", "bg_matched_brace"),
    (r"BAD_CHARACTER|BADCHARACTER|TYPO|GRAMMAR", "error", "w", None),
    (r"RUNTIME_ERROR", "error", "box", None),
    (r"INVALID|WRONG|_ERROR$", "error", "w", None),
    (r"WARN", "warning", "w", None),
    (r"SUGGESTION", "info", "w", None),
    (r"DEPRECATED|OBSOLETE|STRUCK|STRIKEOUT", "deprecated", "s", None),
    # 查找 / 高亮
    (r"SEARCH|FIND_MATCH|MATCHED_TEXT|OCCURRENCE", "fg_search", "", "bg_search"),
    # 提示类
    (r"LIVE_TEMPLATE|TEMPLATE_VARIABLE", "fg", "b", "bg_matched_brace"),
    (r"INJECTED_LANGUAGE_FRAGMENT|INJECTED", "fg", "", None),
    (r"CODE_LENS|INLAY|PARAMETER_HINT|HINT", "fg_dim", "i", None),
    (r"HYPERLINK|URL|LINK", "hyperlink", "u", None),
    (r"BOOKMARK", "bookmark", "b", "bg_folded"),
    (r"BREAKPOINT|EXECUTIONPOINT", "breakpoint", "b", None),
    (r"FOLDED", "fg_dim", "b", "bg_folded"),
    (r"UNDER_CARET", "fg", "", "bg_matched_brace"),
    # Markdown
    (r"^MARKDOWN_(HEADER|BOLD|ITALIC)", "keyword", "b", None),
    (r"^MARKDOWN_(CODE|IMAGE|HRULE|TABLE)", "string", "", None),
    (r"^MARKDOWN_(AUTO_LINK|EXPLICIT_LINK|REFERENCE_LINK|LINK)", "hyperlink", "u", None),
    (r"^MARKDOWN_BLOCK_QUOTE", "comment", "i", None),
    (r"^MARKDOWN_", "fg", "", None),
    # 控制台
    (r"CONSOLE_BLACK", "con_black", "", None),
    (r"CONSOLE_RED_BRIGHT", "con_lightred", "", None),
    (r"CONSOLE_RED", "con_red", "", None),
    (r"CONSOLE_GREEN_BRIGHT", "con_lightgreen", "", None),
    (r"CONSOLE_GREEN", "con_green", "", None),
    (r"CONSOLE_YELLOW_BRIGHT", "con_lightyellow", "", None),
    (r"CONSOLE_YELLOW", "con_yellow", "", None),
    (r"CONSOLE_BLUE_BRIGHT", "con_lightblue", "", None),
    (r"CONSOLE_BLUE", "con_blue", "", None),
    (r"CONSOLE_MAGENTA_BRIGHT", "con_lightmagenta", "", None),
    (r"CONSOLE_MAGENTA", "con_magenta", "", None),
    (r"CONSOLE_CYAN_BRIGHT", "con_lightcyan", "", None),
    (r"CONSOLE_CYAN", "con_cyan", "", None),
    (r"CONSOLE_DARKGRAY", "con_darkgray", "", None),
    (r"CONSOLE_GRAY", "con_gray", "", None),
    (r"CONSOLE_WHITE", "con_white", "", None),
    (r"CONSOLE_SYSTEM", "con_cyan", "", None),
    (r"CONSOLE_USER_INPUT", "con_green", "b", None),
    (r"CONSOLE", "fg", "", None),
    # 日志
    (r"^LOG_ERROR|_ERROR_OUTPUT", "con_red", "", None),
    (r"^LOG_WARNING", "con_yellow", "", None),
    (r"^LOG_EXPIRED|^LOG_VERBOSE|^LOG_DEBUG", "fg_dim", "", None),
    (r"^LOG_COMMAND_INPUT", "con_green", "b", None),
    (r"^LOG_COMMAND_OUTPUT", "fg_dim", "", None),
    (r"^LOG_(INFO|TIME)", "fg_dim", "", None),
    (r"^LOG", "fg", "", None),
    # SQL 对象
    (r"^SQL_(PROCEDURE|FUNCTION)", "function", "", None),
    (r"^SQL_", "class_name", "", None),
    # 键值对（须在 CLASS/TAG/FIELD 之前）
    (r"ATTRIBUTE_VALUE|PROPERTY_VALUE|_VALUE$|\.VALUE$|PROPERTY_KEY_VALUE",
     "string", "", None),
    (r"ATTRIBUTE_NAME|PROPERTY_NAME|PROPERTY_KEY|\.KEY$|_KEY$|SCALAR_KEY|EXTENSION",
     "attr_name", "", None),
    (r"^INI\.", "attr_name", "", None),
    (r"REGEXP|HEREDOC|UNICODE", "string", "", None),
    (r"ESCAPE", "escape", "", None),
    (r"STRING|CHARACTER|\bCHAR\b", "string", "", None),
    (r"NUMBER|NUMERIC|DIGIT|_COLOR$|HASH", "number", "", None),
    (r"KEYWORD|MODIFIER|PRIMITIVE|RESERVED|PSEUDO_INSTRUCTION|INSTRUCTION",
     "keyword", "", None),   # 官方关键字不加粗（等宽字体下 bold 会破字距）
    (r"INTERNAL_COMMAND", "keyword", "", None),
    (r"FUNCTION|METHOD|CALL|ROUTINE|PROCEDURE|COMMAND|MIXIN", "function", "", None),
    (r"INTERFACE|TRAIT|PROTOCOL", "interface_name", "", None),
    (r"ENUM", "enum_name", "", None),
    (r"CONSTANT|BUILTIN|PREDEFINED|REGISTER", "constant", "", None),
    (r"CLASS|STRUCT|RECORD|MODULE|NAMESPACE|PACKAGE|TYPE_ALIAS|TYPE_GUARD",
     "class_name", "", None),
    (r"TYPE_PARAMETER|GENERIC|TYPE_ARGUMENT|TYPE_SPECIFICATION", "type_param", "", None),
    (r"PARAMETER|ARGUMENT|RECEIVER", "parameter", "", None),
    (r"LOCAL_VARIABLE|VARIABLE|VAR_USE|SELF", "local_var", "", None),
    (r"FIELD|PROPERTY|MEMBER|ATTRIBUTE|ANCHOR", "field", "", None),
    (r"TAG", "tag", "b", None),
    (r"ENTITY|REFERENCE", "constant", "", None),
    (r"BRACE|BRACKET|PARENTH|ANGLE|DELIMITER", "brace", "", None),
    (r"OPERATION|OPERATOR|ASSIGN|SIGN|EQUALS", "operator", "", None),
    (r"SEMICOLON|COMMA|DOT|COLON|PUNCTUATION|SECTION", "punctuation", "", None),
    (r"GUTTER|LINE_NUMBER|LINENUMBER", "line_numbers", "", None),
    (r"CARET", "caret", "", None),
    (r"INDENT", "indent_guide", "", None),
    (r"WHITESPACE|WHITE_SPACE", "whitespace", "", None),
    (r"MARGIN|TEARLINE", "right_margin", "", None),
    (r"TEXT|IDENT|DEFAULT|LABEL", "fg", "", None),
]

# ---------------------------------------------------------------------------
# <colors> 区块：编辑器界面（非语法）颜色
# 键名取自真实主题的 <colors> 区块，保证均为有效键
# ---------------------------------------------------------------------------
CHROME_SKIP_ATTR = {"CODE_LENS_BORDER_COLOR"}

CHROME_OVERRIDE = [
    # VCS 状态：官方把"合并冲突"给红、"已删除"给中性灰、"已复制"与"新增"同绿
    ("FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_CONFLICTS", "vcs_conflict"),
    ("FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_BOTH_CONFLICTS", "vcs_conflict"),
    ("FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_PROPERTY_CONFLICTS", "vcs_conflict"),
    ("FILESTATUS_changelistConflict", "vcs_conflict"),
    ("FILESTATUS_DELETED", "vcs_deleted"),
    ("FILESTATUS_IDEA_FILESTATUS_DELETED_FROM_FILE_SYSTEM", "vcs_deleted"),
    ("FILESTATUS_COPIED", "string"),
    # Javadoc {@link}：官方给 teal，刻意与普通超链接分开
    ("DOC_COMMENT_LINK", "doc_link"),
    # 官方这个键装的是**背景**色（#402929 暗红），不是文字色
    ("ERROR_HINT", "bg_error_hint"),
]

CHROME = [
    ("CARET_COLOR", "caret"),
    ("CARET_ROW_COLOR", "bg_caret_row"),
    ("GUTTER_BACKGROUND", "bg_gutter"),
    ("INDENT_GUIDE", "indent_guide"),
    ("VISUAL_INDENT_GUIDE", "indent_guide"),
    ("SELECTED_INDENT_GUIDE", "line_numbers_active"),
    ("LINE_NUMBERS_COLOR", "line_numbers"),
    ("LINE_NUMBER_ON_CARET_ROW_COLOR", "line_numbers_active"),
    ("RIGHT_MARGIN_COLOR", "right_margin"),
    ("SELECTION_BACKGROUND", "bg_selection"),
    ("TEARLINE_COLOR", "right_margin"),
    ("SELECTED_TEARLINE_COLOR", "line_numbers_active"),
    ("WHITESPACES", "whitespace"),
    ("WHITESPACES_MODIFIED_LINES_COLOR", "whitespace"),
    ("SOFT_WRAP_SIGN_COLOR", "fg_dim"),
    ("METHOD_SEPARATORS_COLOR", "indent_guide"),
    ("SEPARATOR_ABOVE_COLOR", "right_margin"),
    ("SEPARATOR_BELOW_COLOR", "right_margin"),
    ("TAB_UNDERLINE", "indent_guide"),
    ("TAB_UNDERLINE_INACTIVE", "right_margin"),
    ("CODE_LENS_BORDER_COLOR", "right_margin"),
    ("ANNOTATIONS_COLOR", "fg_dim"),
    ("DOCUMENTATION_COLOR", "bg_panel"),
    ("LOOKUP_COLOR", "bg_raised"),
    ("NOTIFICATION_BACKGROUND", "bg_raised"),
    ("PROMOTION_PANE", "bg_raised"),
    ("RECENT_LOCATIONS_SELECTION", "bg_selection"),
    ("ERROR_HINT", "error"),
    ("INFORMATION_HINT", "info"),
    ("QUESTION_HINT", "info"),
    # 变更竖条要和"修改行底色"拉开对比；原先用 bg_diff_* 几乎同色
    ("ADDED_LINES_COLOR", "string"),
    ("MODIFIED_LINES_COLOR", "con_blue"),
    ("DELETED_LINES_COLOR", "error"),
    ("IGNORED_ADDED_LINES_BORDER_COLOR", "fg_dim"),
    ("IGNORED_MODIFIED_LINES_BORDER_COLOR", "fg_dim"),
    ("IGNORED_DELETED_LINES_BORDER_COLOR", "fg_dim"),
    ("DIFF_SEPARATORS_BACKGROUND", "bg_panel"),
    ("DIFF_SEPARATOR_WAVE", "fg_dim"),
    ("CONSOLE_BACKGROUND_KEY", "bg_console"),
    ("CONSOLE_NORMAL_OUTPUT", "fg"),
    ("CONSOLE_ERROR_OUTPUT", "error"),
    ("CONSOLE_USER_INPUT", "keyword"),
    ("CONSOLE_SYSTEM_OUTPUT", "con_cyan"),
    ("CONSOLE_BLACK", "con_black"),
    ("CONSOLE_RED", "con_red"),
    ("CONSOLE_GREEN", "con_green"),
    ("CONSOLE_YELLOW", "con_yellow"),
    ("CONSOLE_BLUE", "con_blue"),
    ("CONSOLE_MAGENTA", "con_magenta"),
    ("CONSOLE_CYAN", "con_cyan"),
    ("CONSOLE_GRAY", "con_gray"),
    ("CONSOLE_DARKGRAY", "con_darkgray"),
    ("CONSOLE_WHITE", "con_white"),
    # VCS 文件状态
    ("FILESTATUS_ADDED", "con_green"),
    ("FILESTATUS_DELETED", "con_red"),
    ("FILESTATUS_MODIFIED", "con_blue"),
    ("FILESTATUS_MERGED", "con_magenta"),
    ("FILESTATUS_UNKNOWN", "fg_dim"),
    ("FILESTATUS_NOT_CHANGED_IMMEDIATE", "fg_dim"),
    ("FILESTATUS_NOT_CHANGED_RECURSIVE", "fg_dim"),
    ("FILESTATUS_IDEA_FILESTATUS_DELETED_FROM_FILE_SYSTEM", "con_red"),
    ("FILESTATUS_IDEA_FILESTATUS_IGNORED", "fg_dim"),
    ("FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_CONFLICTS", "warning"),
    ("FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_BOTH_CONFLICTS", "warning"),
    ("FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_PROPERTY_CONFLICTS", "warning"),
    ("FILESTATUS_addedOutside", "con_green"),
    ("FILESTATUS_modifiedOutside", "con_blue"),
    ("FILESTATUS_changelistConflict", "warning"),
    # 行内 VCS 注解
    ("VCS_ANNOTATIONS_COLOR_1", "fg"),
    ("VCS_ANNOTATIONS_COLOR_2", "con_green"),
    ("VCS_ANNOTATIONS_COLOR_3", "con_blue"),
    ("VCS_ANNOTATIONS_COLOR_4", "con_magenta"),
    ("VCS_ANNOTATIONS_COLOR_5", "warning"),
]

FONT_TYPE = {"": 0, "b": 1, "i": 2, "bi": 3}

# 官方有 FONT_TYPE、而分类规则推不出来的键（粗体/斜体是"排版语义"，
# 无法从键名规则推断，只能逐键照官方写）。由对账第 7 条规则守着。
FONT_OVERRIDE = {
    "CONSOLE_USER_INPUT": "i",
    "CSS.IMPORTANT": "b",
    "DEBUGGER_INLINED_VALUES_EXECUTION_LINE": "i",
    "DEBUGGER_INLINED_VALUES_MODIFIED": "i",
    "JS.GLOBAL_VARIABLE": "i",
    "JSP_DIRECTIVE_NAME": "b",
    "LINE_FULL_COVERAGE": "b",
    "LINE_NONE_COVERAGE": "b",
    "LINE_PARTIAL_COVERAGE": "b",
    "REGEXP.CHAR_CLASS": "b",
    "REGEXP.REDUNDANT_ESCAPE": "b",
}
# 官方 Islands Dark 只用 {1,2,3,5}，从不用 0：
#   1 = 实线下划线（超链接、重新赋值的变量）
#   2 = 波浪线（错误/警告/拼写/非法转义）
#   3 = 删除线（废弃、标记删除）
#   5 = 方框/点线（运行时错误、未解析引用）
EFFECT_TOKENS = ("u", "w", "s", "box", "bx0")

EFFECT_TYPE = {"": None, "u": 1, "w": 2, "s": 3, "box": 5, "bx0": 0}

# 官方对这些"状态块"只给效果色、**不给前景色**（错误/警告不把文字染红，更耐看；
# 也避免 WARNING 的前景与注解色撞车）
NO_FOREGROUND = {
    "WARNING_ATTRIBUTES", "WEAK_WARNING_ATTRIBUTES", "ERRORS_ATTRIBUTES",
    "INFO_ATTRIBUTES", "TYPO", "MARKED_FOR_REMOVAL_ATTRIBUTES",
    "GENERIC_SERVER_ERROR_OR_WARNING", "TEXT_STYLE_WARNING",
    # 官方 DIFF_* 只给 BACKGROUND；给 FOREGROUND 会让 diff 用浅色前景
    # 覆盖整行背景（2026.2 实测），白字直接看不见
    "DIFF_INSERTED", "DIFF_DELETED", "DIFF_MODIFIED", "DIFF_CONFLICT",
}

# 官方不给这些键 EFFECT_COLOR（缺省即用前景色画线），照做以免自行发明效果色
# 滚动条 / 边栏条纹色：官方这 9 个键都有 ERROR_STRIPE_COLOR，我们之前漏了
# （键在、条纹字段为空 ⇒ RangeHighlighter 拿不到颜色 ⇒ 条纹不画）
# 只写 EFFECT_COLOR 的键：官方对 CODE_LENS_BORDER_COLOR 只给效果色，
# 靠读入器的缺省 ET=BOXED(0) 画代码透镜框；写 FOREGROUND 会把框弄没
# 参考要求"同时有斜体与 ET=0(BOXED)"的键：普通 style 字段表达不了组合，单列
EXTRA_ET = {"DEBUGGER_INLINED_VALUES": 0}

EFFECT_ONLY = {
    # 官方对这个键**只**写 EFFECT_COLOR（靠读入器缺省 ET=BOXED(0) 画代码透镜框），
    # 写 FOREGROUND 会把框弄没
    "CODE_LENS_BORDER_COLOR": "border",
}
# 官方这些键"另加"了 EFFECT_COLOR（但没有 ET，靠缺省 BOXED 生效）。
# 与 EFFECT_ONLY 的区别：这些键的 FOREGROUND/BACKGROUND 要照常写。
EFFECT_COLOR_NO_ET = {
    "CONSOLE_RANGE_TO_EXECUTE": "separator",
    "DOC_CODE_BLOCK": "doc_comment",
    "DOC_TIPS_SHORTCUT": "fg_dim",
    "LIVE_TEMPLATE_ATTRIBUTES": "hyperlink",
    "TEXT_SEARCH_RESULT_ATTRIBUTES": "search_border",   # 当前命中"画个框"
}

STRIPE = {
    "BOOKMARKS_ATTRIBUTES": "bookmark",
    "BREAKPOINT_ATTRIBUTES": "breakpoint",
    "IDENTIFIER_UNDER_CARET_ATTRIBUTES": "function",
    "RUNTIME_ERROR": "error",
    "SEARCH_RESULT_ATTRIBUTES": "search_stripe",
    "TEXT_SEARCH_RESULT_ATTRIBUTES": "search_current_stripe",
    "TODO_DEFAULT_ATTRIBUTES": "todo",
    "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES": "removal_stripe",
    "WRITE_SEARCH_RESULT_ATTRIBUTES": "removal_stripe",
    "DIFF_INSERTED": "string", "DIFF_DELETED": "vcs_deleted",
    "DIFF_MODIFIED": "number", "DIFF_CONFLICT": "vcs_conflict",
}

# 有意多加排版、且参考方案没有的键 —— 必须逐条写明理由（第 4 轮评审要求）
FONT_INTENT = {
    "HTML_TAG": "HTML/XML/Spring/MyBatis 配置里标签名加粗，与属性名拉开",
    "HTML_TAG_NAME": "同上",
    "HTML_CUSTOM_TAG_NAME": "同上",
    "HTML_ATTRIBUTE_NAME": "同上",
    "XML_TAG": "同上",
    "XML_TAG_NAME": "同上",
    "XML_CUSTOM_TAG_NAME": "同上",
    "DEFAULT_TAG": "同上（通用标签）",
    "PHP_TAG": "同上",
    "BOOKMARKS_ATTRIBUTES": "书签是用户主动标记，加粗提高可见性",
    "FOLDED_TEXT_ATTRIBUTES": "折叠占位符加粗，替代被折叠的代码块",
    "WRITE_SEARCH_RESULT_ATTRIBUTES": "写入态的查找命中，加粗以区分读写",
    "MARKDOWN_BOLD": "样式即语义", "MARKDOWN_ITALIC": "样式即语义",
    "MARKDOWN_HEADER": "样式即语义", "MARKDOWN_HEADER_BOLD": "样式即语义",
    "MARKDOWN_BLOCK_QUOTE": "样式即语义", "MARKDOWN_LINK_TITLE": "样式即语义",
    "MARKDOWN_BLOCK_QUOTE_MARKER": "样式即语义",
    "STATIC_METHOD_ATTRIBUTES": "与 DEFAULT_STATIC_METHOD 同族（官方斜体）",
    "STATIC_FINAL_FIELD_ATTRIBUTES": "与 DEFAULT_STATIC_FIELD 同族（官方斜体）",
    "PHP_STATIC_METHOD": "同上",
}

NO_EFFECT_COLOR = {
    # 官方不给这些键 EFFECT_COLOR（缺省即用前景色画线），照做以免自行发明效果色
    "ANNOTATION_ATTRIBUTE_NAME_ATTRIBUTES", "CUSTOM_KEYWORD4_ATTRIBUTES",
    "IDENTIFIER_UNDER_CARET_ATTRIBUTES",
    "PROPERTIES.KEY", "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES",
}

# 少数键的效果色要单独指定（官方给的是中性灰下划线，而不是前景色）
EFFECT_COLOR_KEYS = {   # 值改成"调色板键名"，随主题走

    "DEFAULT_DOC_COMMENT_TAG": "doc_tag",
    "DEFAULT_REASSIGNED_LOCAL_VARIABLE": "grey_underline",
    "DEFAULT_REASSIGNED_PARAMETER": "grey_underline",
    "REASSIGNED_LOCAL_VARIABLE_ATTRIBUTES": "grey_underline",
    "REASSIGNED_PARAMETER_ATTRIBUTES": "grey_underline",
    "WARNING_ATTRIBUTES": "warning_stripe",
    "WEAK_WARNING_ATTRIBUTES": "warning_stripe",
    "GENERIC_SERVER_ERROR_OR_WARNING": "warning_stripe",
    "KOTLIN_MUTABLE_VARIABLE": "grey_underline",
    "DELETED_TEXT_ATTRIBUTES": "fg",   # 删除线用正文色（对暗红底 6.14:1），不用暗灰
    "IMPLICIT_ANONYMOUS_CLASS_PARAMETER_ATTRIBUTES": "constant",
    "DEFAULT_HIGHLIGHTED_REFERENCE": "grey_underline",
    "INACTIVE_HYPERLINK_ATTRIBUTES": "grey_underline",
    "Unresolved reference access": "grey_underline",
    "INFO_ATTRIBUTES": "info_stripe",            # 官方 #857042 暗琥珀（不是我原来的函数蓝）
    "TYPO": "typo_stripe",                       # 官方 #7ec482 绿（拼写≠编译错误）
    "MARKED_FOR_REMOVAL_ATTRIBUTES": "removal_stripe",  # 官方 #f75464 红（forRemoval 要有警报感）
    "IMPLICIT_ANONYMOUS_CLASS_PARAMETER_ATTRIBUTES": "implicit_ec",  # 官方 EC 比 FG 暗一档，下划线才携带信息
    "FOLLOWED_HYPERLINK_ATTRIBUTES": "followed_link",
}


def classify(name, pal):
    """返回 (前景键, 样式, 背景键, 来源)。

    来源很关键：**启发式规则不决定排版**。粗体/斜体是"排版语义"，
    无法从键名正则可靠推断（"INLAY_BUTTON" 不该斜体、"BASH.SHEBANG" 不该斜体），
    推断错了会让预览/产物/文档三份口径互相矛盾 —— 上一个版本就这样漏了 69 个键。
    只有显式条目（EXPLICIT / FONT_OVERRIDE，两者都逐键对照过官方原文）能设样式。
    """
    if name in EXPLICIT:
        spec = EXPLICIT[name]
        return (spec[0], spec[1], spec[2] if len(spec) > 2 else None, "explicit")
    base = name
    if base.endswith("_ATTRIBUTES"):
        base = base[: -len("_ATTRIBUTES")]
    for pattern, fg, style, bg in RULES:
        if re.search(pattern, base):
            if fg not in pal:
                fg = "fg"
            if bg is not None and bg not in pal:
                bg = None
            return (fg, style, bg, "rule")
    return ("fg", "", None, "default")


def chrome_default(name):
    """给非官方主题里出现的界面颜色键做启发式归类。

    这些键来自两类来源：IDE 各语言插件的 colorSchemes 片段、
    以及官方 <bundledColorScheme> 指向的内置方案（后者键名 100% 有效）。
    """
    n = name.upper()
    # 滚动条（官方方案里有，属于编辑器内滚动条）
    if "SCROLLBAR" in n:
        if "TRACK" in n or n.endswith("BACKGROUND") or n.endswith(".BACKGROUND"):
            return "bg_gutter"
        if "HOVER" in n:
            return "line_numbers_active"
        if "BORDER" in n:
            return "indent_guide"
        return "line_numbers"
    # 书签
    if "BOOKMARK" in n:
        if "BACKGROUND" in n:
            return "bg_folded"
        if "BORDER" in n:
            return "indent_guide"
        if "FOREGROUND" in n:
            return "fg"
        return "bookmark"
    # VCS 文件状态
    if "FILESTATUS" in n:
        if "CONFLICT" in n:
            return "warning"
        if "DELETED" in n or "IGNORED" in n or "OBSOLETE" in n:
            return "fg_dim"
        if "HIJACKED" in n:
            return "con_magenta"
        if "COPIED" in n or "RENAMED" in n or "SWITCHED" in n:
            return "con_blue"
        return "con_green"
    # 缩进参考线类
    if "GUIDE" in n:
        return "indent_guide"
    if "DOC_COMMENT_LINK" in n or "LINK" in n:
        return "hyperlink"
    if "INLINE_REFACTORING_SETTINGS" in n:
        return "bg_raised" if "DEFAULT" in n else "line_numbers_active"
    if "BLOCK_TERMINAL" in n:
        return "bg_selection" if "SELECT" in n else "bg_raised"
    if "ANNOTATIONS_LAST_COMMIT" in n:
        return "fg_dim"
    if "FOREGROUND" in n or "ICONTEXTFOREGROUND" in n:
        return "fg"
    # 通用规则
    if "SELECT" in n:
        return "bg_selection"
    if "DIFF" in n or "REMOVAL" in n or "DELETE" in n or "CHANGED" in n or "_ADD_" in n:
        return "bg_diff_del" if ("REMOVAL" in n or "DELETE" in n) else "bg_diff_add"
    if "ERROR" in n or "BAD" in n:
        return "error"
    if "GUTTER" in n:
        return "bg_gutter"
    if "BACKGROUND" in n or "PANEL" in n or "CELL" in n or "INSIGHT" in n:
        return "bg_raised"
    if ("GRID" in n or "EDGE" in n or "BEND" in n or "BORDER" in n
            or "SNAPPING" in n or "SEPARATOR" in n):
        return "indent_guide"
    if "HIGHLIGHT" in n or "HOT_SPOT" in n or "PORT" in n:
        return "line_numbers_active"
    return "fg_dim"


# 官方 Islands Dark 不定义这些键，保持"未定义"才有正确行为：
#   SELECTION_FOREGROUND —— 不定义 = 选中时保留语法高亮色（官方做法）
CHROME_SKIP = {"SELECTION_FOREGROUND"}


def _assert_no_duplicate_explicit():
    """EXPLICIT 是字典字面量，重复键后者胜 —— 这个坑咬过三次，改成硬报错。"""
    import ast
    tree = ast.parse(open(__file__, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "EXPLICIT":
            keys = [k.value for k in node.value.keys]
            dup = sorted({k for k in keys if keys.count(k) > 1})
            if dup:
                raise SystemExit("EXPLICIT 表里有重复键（后者会静默覆盖前者）：%s" % dup)


def build_icls(pal, names, extra_chrome=()):
    _assert_no_duplicate_explicit()
    scheme = ET.Element("scheme", {
        "name": pal["name"], "version": "142",
        "parent_scheme": pal["parent"]})
    meta = ET.SubElement(scheme, "metaInfo")
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    for k, v in (("created", now), ("ide", "IU"),
                 ("ideVersion", "2026.2.3.0"), ("modified", now),
                 ("originalScheme", pal["name"])):
        ET.SubElement(meta, "property", {"name": k, "value": v})

    colors = ET.SubElement(scheme, "colors")
    seen = set()
    for opt, key in list(CHROME_OVERRIDE) + list(CHROME) + \
            [(n, chrome_default(n)) for n in extra_chrome]:
        if opt in CHROME_SKIP or opt in CHROME_SKIP_ATTR:
            continue
        if opt in seen:
            continue
        seen.add(opt)
        ET.SubElement(colors, "option", {
            "name": opt, "value": pal[key].lstrip("#")})

    attrs = ET.SubElement(scheme, "attributes")
    for name in sorted(set(names)):
        fg, style, bg, src = classify(name, pal)
        style = FONT_OVERRIDE.get(name, style)
        if src == "rule" and name not in FONT_OVERRIDE:
            # 只剥**排版**（粗体/斜体），不动**装饰**（u/w/s/box）——
            # 两者共用 style 字段，但语义完全不同：装饰是语义的一部分（波浪线=错误），
            # 排版无法从键名可靠推断（"INLAY_BUTTON" 不该斜体）。
            if style not in EFFECT_TOKENS:      # 装饰类（u/w/s/box）原样保留
                style = "".join(c for c in style if c not in "bi")
        opt = ET.SubElement(attrs, "option", {"name": name})
        val = ET.SubElement(opt, "value")
        if name in EFFECT_ONLY:
            ET.SubElement(val, "option", {
                "name": "EFFECT_COLOR", "value": pal[EFFECT_ONLY[name]].lstrip("#")})
            continue
        if name not in NO_FOREGROUND:
            ET.SubElement(val, "option", {
                "name": "FOREGROUND", "value": pal[fg].lstrip("#")})
        if bg:
            ET.SubElement(val, "option", {
                "name": "BACKGROUND", "value": pal[bg].lstrip("#")})
        ft = FONT_TYPE.get(style, 0)
        if ft:
            ET.SubElement(val, "option", {"name": "FONT_TYPE", "value": str(ft)})
        et = EFFECT_TYPE.get(style)
        if et is not None:
            ET.SubElement(val, "option", {"name": "EFFECT_TYPE", "value": str(et)})
            if name not in NO_EFFECT_COLOR:   # 官方不给这些键效果色（缺省即用前景色画线）
                ov = EFFECT_COLOR_KEYS.get(name)
                ecolor = "deprecated" if style == "s" else fg
                ET.SubElement(val, "option", {
                    "name": "EFFECT_COLOR",
                    "value": (pal[ov] if ov in pal else pal[ecolor]).lstrip("#")})
        if name in EXTRA_ET:
            ET.SubElement(val, "option", {"name": "EFFECT_TYPE",
                                          "value": str(EXTRA_ET[name])})
        if name in EFFECT_COLOR_NO_ET:
            ET.SubElement(val, "option", {
                "name": "EFFECT_COLOR",
                "value": pal[EFFECT_COLOR_NO_ET[name]].lstrip("#")})
        if name in STRIPE:
            ET.SubElement(val, "option", {
                "name": "ERROR_STRIPE_COLOR",
                "value": pal[STRIPE[name]].lstrip("#")})
        elif style == "w":
            ET.SubElement(val, "option", {
                "name": "ERROR_STRIPE_COLOR", "value": pal[fg].lstrip("#")})
        # 警告：前景不抢眼，靠更亮的波浪线/条纹表达
        if name in ("WARNING_ATTRIBUTES", "WEAK_WARNING_ATTRIBUTES", "GENERIC_SERVER_ERROR_OR_WARNING"):
            ET.SubElement(val, "option", {
                "name": "ERROR_STRIPE_COLOR", "value": pal["warning_stripe"].lstrip("#")})
        # 查找匹配改用两档背景区分"全部匹配 / 当前匹配"（官方也不用描边）
    return scheme


def indent(elem, level=0):
    pad = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = pad + "  "
        for child in elem:
            indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = pad + "  "
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = pad
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = pad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", nargs="*", default=[])
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "themes"))
    ap.add_argument("--chrome-names", nargs="*", default=[],
                    help="额外界面颜色键清单文件（可多个，来自 harvest_ide_keys.py）")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    names = set(FALLBACK_NAMES)
    loaded = []
    for path in args.names:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                got = {ln.strip() for ln in fh
                       if ln.strip() and not ln.startswith("#")}
            names |= got
            loaded.append((path, len(got)))
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    extra_chrome = []
    for path in (args.chrome_names or []):
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                extra_chrome += [ln.strip() for ln in fh if ln.strip()]

    for _, pal in sorted(PALETTES.items()):
        scheme = build_icls(pal, names, extra_chrome)
        indent(scheme)
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               + ET.tostring(scheme, encoding="unicode") + "\n")
        stem = scheme_stem(pal)
        path = os.path.join(outdir, stem + ".icls")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(xml)
        print("写入 %s  (attributes=%d, colors=%d)"
              % (os.path.relpath(path), len(list(scheme.find("attributes"))),
                 len(list(scheme.find("colors")))))

    if args.check:
        print("\n对比度检查（WCAG 比值；正文建议 >= 4.5）")
        for label, pal in sorted(PALETTES.items()):
            print("  [%s]" % label)
            pairs = [("正文 fg", "fg", "bg_editor"),
                     ("注释 comment", "comment", "bg_editor"),
                     ("关键字 keyword", "keyword", "bg_editor"),
                     ("字符串 string", "string", "bg_editor"),
                     ("数字 number", "number", "bg_editor"),
                     ("类名 class_name", "class_name", "bg_editor"),
                     ("函数 function", "function", "bg_editor"),
                     ("行号 line_numbers", "line_numbers", "bg_editor"),
                     ("错误 error", "error", "bg_editor"),
                     ("选中文字 fg_sel", "fg_sel", "bg_selection"),
                     ("控制台输出 fg", "fg", "bg_console")]
            for human, fg, bg in pairs:
                r = contrast(pal[fg], pal[bg])
                flag = "OK " if r >= 4.5 else ("偏低" if r >= 3.0 else "过低")
                print("    %-18s %5.2f:1  %s" % (human, r, flag))
    if loaded:
        print("\n已合并参考清单: " + ", ".join(
            "%s(%d)" % (os.path.basename(p), n) for p, n in loaded))


if __name__ == "__main__":
    main()
