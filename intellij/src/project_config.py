#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Green Eye IntelliJ project metadata.

This is the single source of truth for values shared by generators and
packaging code. Shell tooling discovers the same values from the generated
artifact instead of duplicating them.
"""

PLUGIN_ID = "com.greeneye.intellij.theme"
PLUGIN_NAME = "Green Eye 护眼绿色主题"
VERSION = "1.1.0"
JAR_PREFIX = "GreenEye-Theme-"

# key, theme JSON stem, editor scheme stem, source .icls filename
THEME_SPECS = (
    ("dark", "GreenEyeDark", "GreenEyeDarkScheme", "Green-Eye-Dark.icls"),
    ("mineral", "GreenEyeMineral", "GreenEyeMineralScheme", "Green-Eye-Mineral.icls"),
)


def jar_name():
    return "%s%s.jar" % (JAR_PREFIX, VERSION)
