# 主题校验报告

> **历史记录**：本文件对应 1.0.1（含已删除的浅色版本），仅作留档。
> 当前版本的验收结果见 [verification.md](verification.md)（自动生成）。

对 `themes/Green-Eye-Light.icls`、`themes/Green-Eye-Dark.icls` 以及
`dist/GreenEye-Theme-1.0.1.jar` 的静态校验记录。

目标 IDE：本机 **IntelliJ IDEA 2026.2.3（IU-262.10968.63）**，
路径 `/Applications/IntelliJ IDEA.app`。

---

## 1. 语法属性键：468 个，全部有真实来源

`.icls` 的 `<attributes>` 里每个 `<option name="X">` 的 `X` 必须是真实存在的
`TextAttributesKey` 外部名，否则该条只是被忽略（不会报错，但也不会生效）。
这 468 个键的名字全部来自真实数据，没有一个是手写猜测：

| 来源 | 新增数 | 说明 |
|---|---|---|
| 真实主题导出的键清单 | 349 | 从 [JetBrains GitHub Theme](https://github.com/sergeymakinen/jetbrains-github-theme) 的 `GitHub 3.icls`（194 键）与 [Everforest for JetBrains](https://github.com/francma/everforest-jetbrains) 的 `src/includes/*.xml`（222 键）取并集去重 |
| IDE 自带语言插件的配色片段 | +33 | 用 [`src/harvest_ide_keys.py`](../../src/harvest_ide_keys.py) 遍历安装包内 **1801 个 jar**，从 44 个 `colorSchemes/*.xml` 片段采集（Kotlin/Groovy/SQL/YAML/Markdown/Mermaid/Docker/Kubernetes/Compose/NextEdit/Angular/Sass/Grazie/UML 等） |
| **JetBrains 官方内置方案** | +85 | 自动解析所有 plugin.xml 中的 `<bundledColorScheme path="..."/>`，取出官方随 IDE 发布的方案原文（Islands Dark / Light / High contrast / expUI 等 6 个），再采集其键名 |
| 生成器内置兜底清单 | +1 | `FALLBACK_NAMES` 中未被前三者覆盖的键 |
| **合计** | **468** | 交叉验证：`实际使用的键集合 - 四个来源并集 = 空集` |

**覆盖度可以逐一对账**：官方 6 个内置方案共定义 **220 个属性键**，
本主题**覆盖率 220/220 = 100%**。

> 说明：语言插件真正的高亮键大多带**回退链**（如 `KOTLIN_KEYWORD` →
> `DEFAULT_KEYWORD`）。本主题把 `DEFAULT_*` 全系列都显式定义了，所以即使某个
> 语言的私有键没被列出，它也会回退到本主题的绿色。1.0.1 又补齐了官方方案里的
> 86 个键（`KOTLIN_*`、`JAVA_KEYWORD`、`BREADCRUMBS_*`、`INLAY_*`、
> `INLINE_PARAMETER_HINT*`、`REGEXP.*`、`HTML_ATTRIBUTE_*`、`DOC_CODE_*` 等），
> 覆盖面进一步完整。

---

## 2. 界面颜色键：159 个，其中 13 个曾被证实无效并删除

`<colors>` 区块的键名不在上面的清单里，所以单独核验：

| 来源 | 数量 | 说明 |
|---|---|---|
| 手工核定清单 | 74 | 见 `src/gen_icls.py` 的 `CHROME` |
| IDE 语言插件片段 | +34 | 同上采集流程（含 `DIAGRAM_*`、`NEXT_EDIT.*`、`CONSOLE_*` 等） |
| **JetBrains 官方内置方案** | +51 | 含 `EDITOR_GUTTER_BACKGROUND`、`ScrollBar.*`、`Bookmark.*`、`DOC_COMMENT_GUIDE`、`MATCHED_BRACES_INDENT_GUIDE_COLOR`、`FILESTATUS_*` 等 |
| **合计** | **159** | 覆盖度对账：官方方案的 **105 个界面颜色键，覆盖率 105/105 = 100%** |

手工核定那 74 个键用了两种**互相独立**的方法核验：

**方法 A —— 真实主题佐证**：解析 [Everforest for JetBrains](https://github.com/francma/everforest-jetbrains)
`src/theme.xml` 的 `<colors>` 区块（76 个键，来自一个已发布可用的主题），
与本主题取交集 → **68 个键得到佐证**。

**方法 B —— 安装包字面量全盘扫描**：对方法 A 无法佐证的 53 个键，在整个
`Contents` 目录的 1801 个 jar 内做**精确字面量**匹配（不限制条目大小、
不依赖字符串切分），并放入阳性对照（`FOLDED_TEXT_ATTRIBUTES`、
`LINE_NUMBER_ON_CARET_ROW_COLOR`、`ADDED_LINES_COLOR`）：

- 阳性对照 **全部命中** → 证明扫描方法可靠，不会假阴性
- **40 个键命中** → 确认有效
- **13 个键零命中** → 判定无效，**已从主题中删除**

被删除的 13 个无效键（旧版本/其他 IDE 的键名，2026.2 中不存在）：

```
CONSOLE_LIGHTGRAY   CONSOLE_LIGHTRED      CONSOLE_LIGHTGREEN   CONSOLE_LIGHTYELLOW
CONSOLE_LIGHTBLUE   CONSOLE_LIGHTMAGENTA  CONSOLE_LIGHTCYAN
FOLDED_TEXT_BACKGROUND
NOT_CHANGED_LINES_COLOR
INACTIVE_ADDED_LINES_COLOR  INACTIVE_MODIFIED_LINES_COLOR  INACTIVE_DELETED_LINES_COLOR
SELECTED_LINE_NUMBER_COLOR
```

另有 `DIAGRAM_BEND_SELECTION` 在第一次带大小限制的扫描中漏检，
去掉限制后确认存在于 `plugins/uml/lib/uml-support.jar`，因此**保留**。

> 折行文本背景不再通过 `<colors>` 设置：`FOLDED_TEXT_BACKGROUND` 无效，
> 改为在 `FOLDED_TEXT_ATTRIBUTES` 这个语法属性上设置 `BACKGROUND`。
> 光标所在行行号颜色使用有效的 `LINE_NUMBER_ON_CARET_ROW_COLOR`。

---

## 3. 类继承选择：`parent_scheme` 的一手依据

1.0.0 因为 `parent_scheme="Light"` 解析不到而抛异常（详见第 6 节）。
为确定"哪些父方案名是安全的"，把安装包里全部官方内置方案的
`parent_scheme` 抓出来对账：

| 官方方案文件 | `parent_scheme` |
|---|---|
| `themes/Light.xml` | `Default` |
| `themes/expUI/expUI_lightScheme.xml` | `Default` |
| `themes/expUI/expUI_darkScheme.xml` | `Darcula` |
| `themes/expUI/expUI_darculaContrastScheme.xml` | `Darcula` |
| `themes/islands/IslandSchemeDark.xml` | `Darcula` |
| `themes/islands/highContrastScheme.xml` | `Darcula` |

**浅色一律 `Default`，深色一律 `Darcula`，没有任何官方方案用别的名字。**
本主题照用这两个名字。原文已导出到 `build/ref/ide_official_schemes/`。

---

## 4. 对比度校验（WCAG 相对亮度比）

```bash
python3 src/gen_icls.py --names build/ref/*attribute_names.txt \
        --chrome-names build/ref/*chrome_names.txt --outdir themes --check
```

| 组合 | 浅色「竹露」 | 深色「松林墨」 |
|---|---|---|
| 正文 / 编辑器底 | 8.86 : 1 | 9.27 : 1 |
| 注释 / 编辑器底 | 4.62 : 1 | 4.58 : 1 |
| 关键字 / 编辑器底 | 4.66 : 1 | 6.98 : 1 |
| 字符串 / 编辑器底 | 4.96 : 1 | 7.63 : 1 |
| 数字 / 编辑器底 | 4.65 : 1 | 6.61 : 1 |
| 类名 / 编辑器底 | 4.62 : 1 | 8.28 : 1 |
| 函数 / 编辑器底 | 4.79 : 1 | 7.11 : 1 |
| 错误 / 编辑器底 | 4.72 : 1 | 5.57 : 1 |
| 行号 / 编辑器底 | 3.36 : 1 | 3.40 : 1 |
| 选中文字 / 选中底 | 8.32 : 1 | 7.69 : 1 |
| 控制台输出 / 控制台底 | 9.56 : 1 | 9.98 : 1 |
| *参考：纯黑 / 纯白* | *21.00 : 1* | — |

行号刻意保持在 3.4:1 —— 行号属于界面元素而不参与阅读，压低是为了让它退到背景里。
正文相关组合全部 ≥ 4.5:1，且**上限控制在 11:1 以内**以避免高反差疲劳。

---

## 5. 结构性校验

| 检查项 | 结果 |
|---|---|
| 两个 `.icls` 是合法 XML、能被标准解析器读回 | ✅ |
| 属性键 / 界面色键无重复 | ✅ |
| 所有颜色值为 6 位十六进制（`.icls` 规范，无 `#` 前缀） | ✅ |
| `TEXT` 同时定义了前景与背景（决定编辑区底色） | ✅ |
| 两个 `.theme.json` 是合法 JSON，`dark` 为布尔值 | ✅ |
| jar 内 `META-INF/plugin.xml` 是合法 XML | ✅ |
| `<bundledColorScheme>` 指向的方案文件真实存在于 jar 内 | ✅ |
| 两个主题 JSON 的 `editorScheme` 名称与 `bundledColorScheme` 的 `id` 完全一致 | ✅ `Green Eye Dark` / `Green Eye Light` |
| jar 内嵌方案 XML 可解析 | ✅ |
| 方案 `name` 为纯 ASCII（避免被用作文本键/文件名时的编码问题） | ✅ |
| `parent_scheme` 使用官方同款名字（`Default` / `Darcula`） | ✅ |

---

## 6. 未做的校验（如实说明）

- **1.0.1 没有在你的 IDE 内实际加载过。** 我尝试了两条自动验证路线，**都不成立**：
  - **无头模式**（`bin/inspect.sh` + 隔离配置目录）：插件确实被加载了
    （日志有 `Loaded custom plugins: Green Eye 护眼绿色主题 (1.0.1)`），
    但无头模式不初始化 LaF，`EditorColorsManager` 根本没被构造，
    出错的那段代码（`loadBundledSchemes`）压根没执行。我特意做了一个
    **复刻 1.0.0 旧 bug 的对照包**（按路径引用方案 + `parent_scheme="Light"`），
    它在无头模式下同样是干净的 —— 证明这条路测不出问题，因此它的"通过"无效。
  - **隔离配置的 GUI 启动**：新建的配置目录里没有许可证，日志显示
    `Marking plugins 'disabled': [com.intellij.modules.ultimate]`，
    而 Islands/Darcula/Light 这些主题与内置方案恰好都由该模块声明，
    所以隔离环境与你的真实（已授权）环境不等价。
- 从两次失败里得到一条结论：**这个 bug 类别的验证必须在真实环境做**。
  因此 1.0.1 的正确性依据是"照抄 JetBrains 官方内置方案的写法"
  （第 1、3 节），而不是一次成功的实机运行。
- 预览图 `preview/*.png` 是按调色板渲染的**仿真窗口**，用于观察颜色关系，
  不等于 IDE 的真实截图。

---

## 7. 1.0.0 的启动报错：根因与修复

用户实际遇到的报错：

```
com.intellij.diagnostic.PluginException: Light [Plugin: com.greeneye.intellij.theme]
  at ...SchemeManagerImpl.loadBundledSchemes(SchemeManagerImpl.kt:172)
Caused by: com.intellij.openapi.util.InvalidDataException: Light
  at ...AbstractColorsScheme.resolveParent(AbstractColorsScheme.java:1070)
```

两个叠加的错误：

1. **引用方式错了。** 1.0.0 的主题 JSON 写
   `"editorScheme": "/schemes/GreenEyeLight.xml"` —— 用**路径**引用方案。
   这会额外把该文件当成一个 "bundled scheme" 在启动早期加载，
   于是 `resolveParent` 在我的方案上被执行。
2. **父方案名不可解析。** 浅色方案写了 `parent_scheme="Light"`。
   `Light` 确实是一个方案（官方 `expUI_light.theme.json` 的 `editorScheme` 就是它），
   但它由 **Ultimate 定制插件**声明为 `<bundledColorScheme id="Light" .../>`，
   在方案批量加载的那一刻**还没注册**，于是 `resolveParent("Light")` 抛异常。

官方写法（一手证据）：

```xml
<!-- lib/intellij.idea.ultimate.customization.jar!/META-INF/plugin.xml -->
<bundledColorScheme id="IntelliJ Light" path="themes/Light.xml" />
<bundledColorScheme id="Light"          path="themes/expUI/expUI_lightScheme.xml" />
<bundledColorScheme id="Dark"           path="themes/expUI/expUI_darkScheme.xml" />
<bundledColorScheme id="Islands Dark"   path="/themes/islands/IslandSchemeDark.xml" />
<themeProvider id="Islands Dark" path="/themes/islands/ManyIslandsDark.theme.json" targetUi="islands" />
```

```xml
<!-- lib/intellij.platform.ide.impl.jar!/themes/expUI/expUI_lightScheme.xml -->
<scheme name="Light" version="142" parent_scheme="Default">
<!-- lib/intellij.platform.ide.impl.jar!/themes/islands/IslandSchemeDark.xml -->
<scheme name="Islands Dark" version="142" parent_scheme="Darcula">
```

1.0.1 的修复：

1. 方案放在 `themes/` 下，用
   `<bundledColorScheme id="方案名" path="/themes/xxx.xml"/>` **显式注册**；
2. 主题 JSON 用**方案名**引用（`"editorScheme": "Green Eye Dark"`），**不用路径**；
3. 父方案改为官方同款：浅色 `Default`、深色 `Darcula`；
4. 方案名改纯 ASCII，中文标签移到 Theme 显示名里；
5. 安装脚本默认不再复制 `.icls`，避免与内置方案重名。
