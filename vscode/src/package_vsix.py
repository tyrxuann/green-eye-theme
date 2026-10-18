#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把生成好的 VS Code 主题打成 .vsix（ZIP，标准库即可，不需要 Node/vsce）。

VSIX 结构：
    [Content_Types].xml
    extension.vsixmanifest
    extension/package.json
    extension/themes/green-eye-dark.json
    extension/themes/green-eye-mineral.json
    extension/README.md
"""
import json
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
VSCODE = HERE.parent
ROOT = VSCODE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "intellij" / "src"))

import generate  # noqa: E402
from project_config import VERSION  # noqa: E402

CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="vsixmanifest" ContentType="text/xml"/>
  <Default Extension="md" ContentType="text/markdown"/>
</Types>
"""

README_TEXT = """# Green Eye 护眼绿色主题

两款深色主题，共用同一块墨绿底 `#1F3027`：

- Green Eye Dark 松林
- Green Eye Mineral 矿彩

## 安装

1. VS Code -> Extensions
2. 右上角 `...` -> Install from VSIX...
3. 选择本文件（green-eye-theme-%s.vsix）
4. Command Palette -> Preferences: Color Theme
5. 选择「Green Eye Dark 松林」或「Green Eye Mineral 矿彩」

完整说明见项目 README。
""" % VERSION


def manifest(pkg):
    engine = pkg.get("engines", {}).get("vscode", "^1.80.0")
    return """<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0"
  xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011"
  xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="%s" Version="%s" Publisher="%s" />
    <DisplayName>%s</DisplayName>
    <Description xml:space="preserve">%s</Description>
    <Tags>theme,green,eye,dark,comfort</Tags>
    <Categories>Themes</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="%s" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="ui" />
      <Property Id="Microsoft.VisualStudio.Code.ExecutesCode" Value="false" />
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest"
           Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details"
           Path="extension/README.md" Addressable="true" />
  </Assets>
</PackageManifest>
""" % (escape(pkg["name"]), escape(pkg["version"]), escape(pkg["publisher"]),
       escape(pkg["displayName"]), escape(pkg["description"]),
       escape(engine))


def package(outdir=None):
    if generate.generate() != 0:
        return 1
    pkg_path = VSCODE / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    if pkg.get("version") != VERSION:
        print("package.json 版本 %s 与 project_config.VERSION %s 不一致"
              % (pkg.get("version"), VERSION), file=sys.stderr)
        return 1
    out = Path(outdir).expanduser() if outdir else VSCODE / "dist"
    out.mkdir(parents=True, exist_ok=True)
    target = out / ("green-eye-theme-%s.vsix" % VERSION)
    themes = sorted((VSCODE / "themes").glob("green-eye-*.json"))
    if len(themes) < 2:
        print("缺少 vscode/themes/green-eye-*.json", file=sys.stderr)
        return 1

    extras = []
    license_path = ROOT / "LICENSE"
    if license_path.is_file():
        extras.append(("extension/LICENSE", license_path.read_bytes()))

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("extension.vsixmanifest", manifest(pkg))
        zf.writestr("extension/package.json", pkg_path.read_bytes())
        zf.writestr("extension/README.md", README_TEXT)
        for theme in themes:
            zf.writestr("extension/themes/%s" % theme.name,
                        theme.read_bytes())
        for arc, data in extras:
            zf.writestr(arc, data)

    print("写入 %s（%d 字节，%d 个文件）"
          % (target, target.stat().st_size, len(themes) + 4 + len(extras)))
    return 0


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="打包 VS Code .vsix")
    ap.add_argument("--outdir")
    args = ap.parse_args(argv)
    return package(args.outdir)


if __name__ == "__main__":
    sys.exit(main())
