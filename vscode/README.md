# vscode —— 待实现

VS Code 实现目前**还没有做**。这个目录是落点，下面是开工前已经确定好的部分。

## 为什么现在就能开工

色值已经在 [`../shared/palette.json`](../shared/palette.json) 里，是平台无关的：
两款主题、112 个语义槽位、每个槽位的语义说明与对底色的对比度，外加一份
**已记录的例外清单**（新平台的检查器要读它，否则会拿不知道例外的标准去判、必然误报）。

所以 VS Code 侧**不需要**理解 IntelliJ 的 475 个属性键，只需要做一次"语义槽位 → VS Code 键"的映射。

## 要做的事

1. `vscode/src/` 写一个生成器，读 `../shared/palette.json`，产出
   `themes/green-eye-dark.json` 与 `themes/green-eye-mineral.json`
   （VS Code 主题文件是 `{ "name", "type": "dark", "colors": {...}, "tokenColors": [...] }`）。
2. `vscode/scripts/build.sh`：生成 → `green_eye.py check` → 打包 `.vsix`。
3. 把结果并入顶层 README 的平台表。

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
| `bg_diff_add` / `bg_diff_del` / `bg_diff_mod` | `diffEditor.insertedTextBackground` / `removedTextBackground` / `…ModifiedTextBackground` |
| `error` / `warning` | `editorError.foreground` / `editorWarning.foreground` |
| `vcs_conflict` | `gitDecoration.conflictingResourceForeground` |
| `vcs_deleted` | `gitDecoration.deletedResourceForeground` |
| `doc_link` / `hyperlink` | `textLink.foreground` / `textLink.activeForeground` |

### `tokenColors`（语法）

| 本项目槽位 | TextMate scope（建议） |
|---|---|
| `comment` | `comment` |
| `doc_comment` | `comment.block.documentation` |
| `doc_tag` | `comment.block.documentation keyword` / `storage.type.class.jsdoc` |
| `keyword` | `keyword` `storage.type` `storage.modifier` |
| `string` | `string` |
| `attr_value` | `string.quoted` / `string.template` |
| `number` | `constant.numeric` |
| `constant` | `variable.other.constant` `variable.other.enummember` |
| `function` | `entity.name.function` `support.function` |
| `annotation` | `entity.name.type.annotation` `storage.type.annotation` |
| `escape` | `constant.character.escape` |
| `error` / `warning` | `invalid` / `invalid.deprecated` |
| `fg` | （不写 scope，作为 `editor.foreground` 兜底） |

> 注意 VS Code 的 TextMate 语义比 IntelliJ 粗，`tokenColors` 里**不要**给
> `punctuation`/`operator`/`bracket` 单独上色 —— 那会破坏"彩色只留给语义"这条法则
> （IntelliJ 侧这些槽位也都等于 `fg`）。

## 验收

```bash
python3 ../shared/tools/check_palette.py     # 色值层：四类判据
```
色值层过了之后，再人工核对一次 VS Code 实际渲染（`Developer: Inspect Editor Tokens and Scopes`），
因为 TextMate scope 的落点无法静态穷举 —— 这与 IntelliJ 侧"实机逐屏走查"是同一类边界。
