# vscode —— VS Code 实现

VS Code 侧已经实现：从 `../shared/palette.json` 读取平台无关色值，
生成两套 VS Code 主题，并打成可直接安装的 `.vsix`。

## 用法

```bash
# 生成 themes/*.json + dist/*.vsix
uv run green_eye.py vscode

# 只生成 themes/*.json
uv run green_eye.py vscode --no-package

# 指定 VSIX 输出目录
uv run green_eye.py vscode --outdir /tmp/green-eye
```

没有 uv 时：

```bash
python3 green_eye.py vscode
bash vscode/scripts/build.sh
```

输出：

```
vscode/themes/green-eye-dark.json
vscode/themes/green-eye-mineral.json
vscode/dist/green-eye-theme-<version>.vsix
```

`vscode/themes/` 与 `vscode/dist/` 都是生成物，已加入 `.gitignore`。

## 安装

```bash
code --install-extension vscode/dist/green-eye-theme-<version>.vsix
```

或在 VS Code 里：

1. `Extensions`
2. 右上角 `...` → **Install from VSIX…**
3. 选择 `.vsix`
4. `Command Palette` → `Preferences: Color Theme`
5. 选择「Green Eye Dark 松林」或「Green Eye Mineral 矿彩」

## 映射表（语义槽位 → VS Code）

### `colors`（工作台）

| 本项目槽位 | VS Code 键 |
|---|---|
| `bg_editor` | `editor.background` |
| `fg` | `editor.foreground` |
| `bg_panel` | `sideBar.background` / `panel.background` |
| `bg_raised` | `editorWidget.background` / `quickInput.background` |
| `border` | `editorWidget.border` / `panel.border` |
| `separator` | `sideBar.border` / `editorGroup.border` |
| `fg_dim` | `descriptionForeground` / `breadcrumb.foreground` |
| `caret` | `editorCursor.foreground` |
| `line_numbers` | `editorLineNumber.foreground` |
| `line_numbers_active` | `editorLineNumber.activeForeground` |
| `bg_selection` | `editor.selectionBackground` |
| `bg_search` | `editor.findMatchBackground` |
| `bg_search_current` | `editor.findMatchHighlightBackground` |
| `bg_caret_row` | `editor.lineHighlightBackground` |
| `bg_matched_brace` | `editorBracketMatch.background` + `editorBracketMatch.border` |
| `bg_diff_add` / `bg_diff_del` / `bg_diff_mod` | `diffEditor.insertedTextBackground` / `removedTextBackground` / `diagonalFill` |
| `error` / `warning` | `editorError.foreground` / `editorWarning.foreground` |
| `vcs_conflict` | `gitDecoration.conflictingResourceForeground` |
| `vcs_deleted` | `gitDecoration.deletedResourceForeground` |
| `doc_link` / `hyperlink` | `textLink.foreground` / `textLink.activeForeground` |

### `tokenColors`（语法）

| 本项目槽位 | TextMate scope |
|---|---|
| `comment` | `comment` |
| `doc_comment` | `comment.block.documentation`（斜体） |
| `doc_tag` | `comment.block.documentation keyword` / `storage.type.class.jsdoc` |
| `keyword` | `keyword` / `storage.type` / `storage.modifier` |
| `string` | `string` |
| `attr_value` | `meta.tag.attributes string` / `string.quoted.double.html` 等 |
| `number` | `constant.numeric` |
| `constant` | `variable.other.constant` / `variable.other.enummember`（斜体） |
| `function` | `entity.name.function` / `support.function` |
| `annotation` | `entity.name.type.annotation` / `storage.type.annotation` |
| `escape` | `constant.character.escape` |
| `error` / `warning` | `invalid` / `invalid.deprecated` |
| `todo` | `keyword.other.todo` / `comment.line.todo`（斜体） |

> VS Code 的 TextMate 语义比 IntelliJ 粗，`tokenColors` 里**不要**给
> `punctuation` / `operator` / `bracket` 单独上色 —— 那会破坏"彩色只留给语义"这条法则。
> 当前生成器也只给 `punctuation.definition.comment` 跟随注释色，不给字符串标点单独上色。

## CVD Improved 变体

```bash
uv run green_eye.py cvd-variants
```

生成 `vscode/dist/green-eye-cvd-variants-<version>.vsix`，包含：

- `Green Eye Dark (CVD Improved)`
- `Green Eye Mineral (CVD Improved)`

这是 A+ 改善版，不是 CVD 安全版：松林 18→13 对、矿彩 20→14 对塌陷。
残余配对见 `intellij/build/ref/cvd-variants-report.md`，设计取舍见
`docs/cvd-variants.md`。

## 验收

```bash
python3 shared/tools/check_palette.py    # 色值层：四类判据
python3 green_eye.py vscode              # 生成 + 打包
python3 green_eye.py test                # 含 tests/test_vscode.py
npx --yes @vscode/vsce ls                # 可选：用官方工具检查打包内容
```

`npx @vscode/vsce ls` 只应列出 `README.md`、`package.json` 和两个主题 JSON；
`src/`、`scripts/`、`__pycache__` 由 `.vscodeignore` 排除。

`green_eye.py vscode` 结束时会检查 `themes/*.json` 与 `.vsix` 的 mtime
不早于 `palette.json` / 生成器 / `package.json`，避免把旧主题打进 VSIX。

也可以用官方工具实际打包校验：

```bash
npx --yes @vscode/vsce package --out dist/vsce-check.vsix
```

它会产出 6 个文件（manifest、package.json、readme、两个主题、内容类型）。
`repository` 与 `LICENSE` 已配置，正常应无警告。

`tests/test_vscode.py` 会检查：

- 两套主题的 `colors` / `tokenColors` 只引用调色板里真实存在的颜色；
- 没有给 punctuation / operator / bracket 单独上色；
- 两款主题的关键 token 明显不同；
- VSIX 的 manifest、`package.json`、主题文件和 README 齐全。

## 已知限制

- **没有在真实 VS Code 里安装过**（本机没有 `code` CLI）。VSIX 结构按标准生成，
  但 TextMate scope 的实际落点需要
  `Developer: Inspect Editor Tokens and Scopes` 人工核对，这与 IntelliJ 侧的
  "实机逐屏走查"是同一类边界。
- `attr_value` 的 scope 只能靠 `meta.tag.attributes string` 等较具体的路径命中；
  不同语言插件的 scope 粒度不同，可能需要按实际渲染再调。
