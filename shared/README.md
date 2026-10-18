# shared —— 平台无关层

这一层只放**与编辑器无关**的东西：色值、语义角色、设计法则、以及只按色值判定的检查。
任何平台（IntelliJ / VS Code / Vim / 终端…）都从这里取色，而不是从别家的主题文件里抄。

## 数据流（单向，不要反向依赖）

```
intellij/src/palette.py        ← 唯一真相（改色只改这里）
        │  shared/export_palette.py
        ▼
shared/palette.json            ← 跨平台契约
        │
        ├── intellij/  （.icls + .theme.json，475 个属性键的映射）
        └── vscode/    （待实现）
```

`shared/palette.json` **是生成物**，由 `make build` 自动重导，并带一致性断言
（`export_palette.py --check`），不要手改。

## 契约 schema

```jsonc
{
  "schema": "green-eye-palette/1",
  "anchor": "两款主题共用同一块底色 #1F3027；换平台时底色与对比度标准不变。",
  "roles":  { "keyword": "关键字", "bg_selection": "选中", ... },   // 29 条语义说明
  "exceptions": {                       // ★ 已记录的例外，新平台的检查器必须读它
    "same_by_design":   [["bg_editor","bg_gutter"], ...],           // 语义相同 → 同值合理
    "accepted_pairs":   [{ "pair": [...], "reason": "..." }, ...],  // 已评估接受的撞色，附理由
    "reference_token_de": { "doc_comment|doc_tag": 11.7, ... }      // 参考自己也贴得近的配对
  },
  "themes": [{
    "id": "dark", "name": "Green Eye Dark", "label": "松林", "dark": true,
    "parent": "Darcula",              // IntelliJ 概念，其他平台可忽略
    "bg_editor": "#1F3027",
    "colors":   { "keyword": "#D7BA76", ... },   // 112 个色值，键名即语义槽位
    "contrast": { "keyword": 7.38, ... }         // 对各自编辑器底的 WCAG 比值
  }]
}
```

## 设计法则（换平台也必须遵守）

1. **底色锚点**：编辑器底固定 `#1F3027`。这是整套设计的"地"，不因平台而变。
2. **对比度是约束**：正文 ≈9:1 · 强调色 6–7:1 · 注释 3.5–4.4:1 · 光标 ≈10.7:1 · 行号 ≈2.2:1。
   任何平台的目标是让这些比值**落在同一区间**，而不是照抄十六进制（不同底色上同 hex 的比值不同）。
3. **彩色只留给语义**：正文/标识符/括号/运算符/标签全部同色（暖中性墨）。
4. **状态色必须两两可分**：块与块之间"亮度差不足 **且** 色差也不足"才算分不开（CIE ΔE2000）。
5. **身份靠中彩度 token**：高亮度近中性的墨色（C\* < 5）在物理上承载不了主题身份，
   身份只能由 C\* 20–60 的 token（字符串/数字/函数/关键字/常量/注解）承担。
6. **有意偏离要写理由**：任何"和参考不同"的地方都进 `exceptions`，不能静默放行。

## 验收

```bash
make check
```
四类判据（只读 `palette.json`，与平台无关）：

| 判据 | 内容 |
|---|---|
| 对比度下限 | 按语义角色（`FLOORS`）逐槽位检查 |
| 状态色两两可分 | 亮度差 <1.10:1 **且** ΔE2000 <12 才判失败；跳过 `same_by_design` 与 `accepted_pairs` |
| 前景 token 可分 | 同上；对"参考自己也贴得近"的配对改用**不得比参考更近**的严格口径 |
| 主题身份 | novelty ≥15 · 频率加权 ≥16 · 主力 token ≥5/8 |

另有**色觉缺陷模拟**（Machado 2009）作为**报告项**不判失败：官方是靠发布
deuteranopia/protanopia 变体解决的，本项目暂未提供（已知缺口，已量化）。

`tools/colorlib.py` 是零依赖的色彩数学（WCAG 对比度 / CIELAB / CIEDE2000 / CVD 模拟），
新平台可以直接复用；IntelliJ 侧另有一份更细的实现，两者口径一致。
