# Green Eye · IntelliJ IDEA 护眼绿色主题

> **这是 `green-eye-theme` 项目里的 IntelliJ IDEA 实现**（`intellij/`）。
> 项目总览与"如何新增 VS Code 等其他平台"见 [上层 README](../README.md)；
> 平台无关的色值契约在 [`../shared/palette.json`](../shared/palette.json)。
> 本目录下的文档只讲 **IDEA 侧**：475 个属性键的映射、装饰编码、评审修订史、有意偏离清单。

同一个插件里装了**两款**主题，共用**同一块苔绿底 `#1F3027`**，但语义配色是两套不同的设计语言：

| | 「松林」 Green Eye Dark | 「矿彩」 Green Eye Mineral |
|---|---|---|
| 设计方法 | 色相与饱和度**沿用 JetBrains 官方 Islands Dark**，只按官方对比度重解明度 | 以底色为中心**重新设计**，且做**角色互换**：**暖矿结构**（金黄关键字 / 赭石常量 / 玫瑰注解 / 芥黄 TODO）+ **冷矿内容**（冰青字符串 / 紫晶数字 / 玉青函数），正文层暖中性墨 |
| 关键字 | 橙 `#D9A58B` | **金黄** `#D7BA76` |
| 注解 `@Override` | 橄榄 `#B8B476` | **玫瑰** `#D8A5B8` |
| 常量 / 字段 | 紫 `#D296C8` | **赭石** `#B58268` |
| 字符串 | 绿 `#8BBD84` | **冰青** `#94B8C5`（内容层整体移到冷极） |
| 数字 | 青 `#2FC1CF` | **紫晶** `#C1A5DA` |
| 函数 | 电光蓝 `#85BDF1`（S79） | **玉青** `#5FCAB4`（S50） |
| 注释 | 暖灰 `#93918A` | **冷石** `#859391` |
| 选中 / 查找 | 青 `#335662` / 绿 `#2D5440` | **深绿** `#365847` / **琥珀** `#594F25` |

**对比度是两款共同的设计约束**（这也是当初参考官方的唯一目的）：正文 9:1、强调色 6–7:1、
注释 ~4.4:1、光标 ~10.7:1、行号 2.2:1，并且状态色两两可分（CIE ΔE2000 + WCAG，以官方为标尺）。
「矿彩」的每个色由 `(色相, 饱和度, 目标对比度)` **反解明度**得到，所以对比度是设计约束而不是事后检查。

> 浅色版本已按你的要求删除（`gen_icls.py` 里仍保留生成能力，需要时可再出）。

面向本机 **IntelliJ IDEA 2026.2.3（IU-262.10968.63）** 生成与校验。

| 「松林」 | 「矿彩」 |
|---|---|
| ![松林整站](preview/ui-dark.png) | ![矿彩整站](preview/ui-mineral.png) |

---

## 1. 为什么是"官方结构 + 绿色皮肤"

我先把安装包里 6 个官方内置方案原文拆开做了统计，得到四条规律：

1. **绝大多数代码是同一个中性色**。官方 Islands Dark 的 159 个带色键里只有
   76 种颜色，`#bcbec4` 一个中性色被复用 **16 次** —— 标识符、类名引用、标签、
   括号、分号、运算符全是它。
2. **重点色比正文暗**：中性正文 9.37:1，重点色只有 5.9~6.9:1，注释 4.27:1。
3. **重点色偏深偏浓**：明度 44%~65%、饱和度 28%~91%，靠**饱和度**跳出背景，
   而不是靠亮度。
4. **关键字不加粗**；只有静态成员/常量/文档注释/TODO 用斜体。

本主题逐条照做，只把色相里"哪一类变绿"做了取舍：

<!-- PALETTE-TABLE:DARK:BEGIN -->
| 语义 | 官方 Islands Dark | 本主题「松林」 | 对比度 |
|---|---|---|---|
| 正文 / 标识符 / 类名 / 括号 / 运算符 / 标签 | `#bcbec4` | `#D1D0CA` | 9.00:1 · 全部同色（官方做法） |
| 注释 | `#7a7e85` | `#93918A` | 4.41:1 · 冷绿灰中性，与正文色相拉开 60°+ |
| 文档注释（斜体） | `#5f826b` | `#658C7C` | 3.70:1 · 压到 3.7:1，长 Javadoc 不再发光 |
| 关键字 | `#cf8e6d` | `#D9A58B` | 6.43:1 · 色相/饱和度同官方 |
| 字符串 | `#6aab73` | `#8BBD84` | 6.43:1 · 色相 128°→112°，与底色间距拉到 36° |
| 数字 | `#2aacb8` | `#2FC1CF` | 6.39:1 · 同官方 |
| 函数 / 方法 | `#56a8f5` | `#85BDF1` | 6.98:1 · 饱和度 89%→79% |
| 字段 / 静态 / 常量 | `#c77dbb` | `#D296C8` | 5.92:1 · 同官方 |
| 注解 / Javadoc 标签 | `#b3ae60` | `#B8B476` | 6.51:1 · 同官方 |
| 警告（前景＝注解色，波浪线另用） | `官方未定义` | `#B8B476` | 6.51:1 · 不自造色相；波浪线见下 |
| 警告波浪线 | `—` | `#E8D48A` | 9.41:1 · 比前景明显更亮 |
| TODO（斜体） | `#8bb33d` | `#A7C73D` | 7.20:1 · 同官方 |
| 错误 / 未匹配括号 | `#f75464` | `#F97884` | 5.33:1 · 同官方 |
| 链接 | `#548af7` | `#78A89D` | 5.22:1 · 色相 220°→245°，与函数蓝分开 |
| 光标 | `#ced0d6` | `#E3E2DE` | 10.73:1 · 官方 11.3:1 |
| 行号 | `#4b5059` | `#61605A` | 2.20:1 · 官方 2.15:1 |
| 背景：编辑器 / 面板 / 浮层 | #191A1C / #26282C / #33353B | `#1F3027 / #1B211D / #2E4739` | 浮层对编辑器 1.37:1 |
| 边框：浮层轮廓 / 窗口发丝线 | — | `#3B5847 / #2C3D35` | 对编辑器 1.77 / 1.21:1 |
| 当前行 / 折叠区 | — | `#283D32（与底色同相）` | 1.19:1 |
| 选中 / 查找匹配 | — | `#335662 青 / #2D5440 绿 + 描边 #57966A` | 1.75 / 1.62:1 |
| diff 新增 / 删除 / 修改 | — | `#2E4A2A / #673838 / #2E4059` | 1.41 / 1.46 / 1.32:1 |
<!-- PALETTE-TABLE:DARK:END -->

### 「矿彩」语义配色表

<!-- PALETTE-TABLE:MINERAL:BEGIN -->
| 语义 | 官方 Islands Dark | 本主题「矿彩」 | 对比度 |
|---|---|---|---|
| 正文 / 标识符 / 类名 / 括号 / 运算符 / 标签 | `#bcbec4` | `#D1D0CA` | 9.00:1 · 全部同色（官方做法） |
| 注释 | `#7a7e85` | `#859391` | 4.36:1 · 冷石色，与正文暖墨分层 |
| 文档注释（斜体） | `#5f826b` | `#578F7A` | 3.72:1 · 压到 3.7:1，长 Javadoc 不再发光 |
| 关键字 | `#cf8e6d` | `#D7BA76` | 7.40:1 · 金黄 H42，与错误(H358)分开 |
| 字符串 | `#6aab73` | `#94B8C5` | 6.57:1 · 冰青 H196，与底色 H148 拉开 48° |
| 数字 | `#2aacb8` | `#C1A5DA` | 6.40:1 · 紫晶 H272，与函数(玉青 H168)分开 |
| 函数 / 方法 | `#56a8f5` | `#5FCAB4` | 7.01:1 · 玉青 H168，S50 降低刺激 |
| 字段 / 静态 / 常量 | `#c77dbb` | `#B58268` | 4.21:1 · 赭石 H20，暖极深处 |
| 注解 / Javadoc 标签 | `#b3ae60` | `#D8A5B8` | 6.62:1 · 玫瑰 H338，暖极另一端 |
| 警告（前景＝注解色，波浪线另用） | `官方未定义` | `#D8A5B8` | 6.62:1 · 不自造色相；波浪线见下 |
| 警告波浪线 | `—` | `#E9D481` | 9.40:1 · 比前景明显更亮 |
| TODO（斜体） | `#8bb33d` | `#BABE47` | 6.98:1 · 芥黄 H62，与字符串(冰青)拉开 |
| 错误 / 未匹配括号 | `#f75464` | `#E98588` | 5.41:1 · 红 H358，与关键字(H42)分开 |
| 链接 | `#548af7` | `#78A299` | 4.92:1 · 灰青 H168，比函数更灰、更暗 |
| 光标 | `#ced0d6` | `#E3E2DE` | 10.73:1 · 官方 11.3:1 |
| 行号 | `#4b5059` | `#616059` | 2.20:1 · 官方 2.15:1 |
| 背景：编辑器 / 面板 / 浮层 | #191A1C / #26282C / #33353B | `#1F3027 / #1A211E / #2F463C` | 浮层对编辑器 1.37:1 |
| 边框：浮层轮廓 / 窗口发丝线 | — | `#3B5849 / #2C3D35` | 对编辑器 1.77 / 1.21:1 |
| 当前行 / 折叠区 | — | `#293C33（与底色同相）` | 1.18:1 |
| 选中 / 查找匹配 | — | `#365847 绿 / #594F25 琥珀 + 描边 #9C862D` | 1.75 / 1.70:1 |
| diff 新增 / 删除 / 修改 | — | `#274B28 / #683839 / #323E61` | 1.41 / 1.47 / 1.32:1 |
<!-- PALETTE-TABLE:MINERAL:END -->

<!-- MINERAL-DESIGN:BEGIN -->
### 「矿彩」的设计意图（逐槽位）

「矿彩」不是从官方派生的，所以这里写的不是「偏离」，而是**为什么这样定**。

| 槽位 | 官方 Islands Dark | 矿彩 | 落在 | 为什么 |
|---|---|---|---|---|
| **关键字** keyword | `#cf8e6d` · H20 S51 | `#D7BA76` · H42 S55 · 7.40:1 | 暖极·最亮 | 官方是**橙红**(H20)，贴近「警告/危险」的语义；矿彩改用**金黄**(H42 S55)，把「语言结构」与「出错」在色相上分开，同时更贴「矿物」这个主题词 |
| **常量 / 字段** constant | `#c77dbb` · H310 S40 | `#B58268` · H20 S34 · 4.21:1 | 暖极·最深 | 官方是**紫**(H310)，与字符串/函数都无关联；矿彩改用**赭石**(H20 S34)，落在暖极深处 —— 与关键字拉开 ΔE 21.4、与错误拉开 15.9，读起来像「沉淀下来的值」 |
| **注解 / 警告** annotation | `#b3ae60` · H56 S35 | `#D8A5B8` · H338 S40 · 6.62:1 | 暖极·另一端 | 官方是**橄榄**(H56)，夹在关键字与字符串之间最容易被忽略；矿彩改用**玫瑰**(H338 S40)，放到暖极的另一端，与关键字形成明确的「两端」关系。警告沿用同色（不自造色相） |
| **TODO** todo | `#8bb33d` · H80 S49 | `#BABE47` · H62 S48 · 6.98:1 | 暖极·偏黄 | 官方是黄绿(H80)，与字符串绿撞车；矿彩移到**芥黄**(H62 S48)，与字符串(冰青 H196)拉开 133.9° |
| **字符串** string | `#6aab73` · H128 S28 | `#94B8C5` · H196 S30 · 6.57:1 | 冷极·冰青 | 官方是标准绿(H128)，在绿底上「绿叠绿」；矿彩改用**冰青**(H196 S30)，与底色 H148 拉开 **47.7°**，靠色相而不是只靠亮度站住 |
| **数字** number | `#2aacb8` · H185 S63 | `#C1A5DA` · H272 S42 · 6.40:1 | 冷极·紫晶 | 官方是**电光青**(H185 S63)；矿彩改用**紫晶**(H272 S42)，从「发光」变成「矿石的反光」，与函数(玉青 H168)分开 104.0° |
| **函数 / 方法** function | `#56a8f5` · H209 S89 | `#5FCAB4` · H168 S50 · 7.01:1 | 冷极·深处 | 官方是**电光蓝**(H209 S89)。函数是出现频率最高的彩色 token，高饱和最伤眼 —— 矿彩降到 **S50**，仍与数字(紫晶 H272)分开 104.0° |
| **Javadoc 标签** doc_tag | `#67a37c` · H141 S25 | `#A6BCAD` · H139 S14 · 6.90:1 | 注释层·苔石 | 早期把它放在冷极，结果与数字几乎同色；现在改用**苔石色**(H139 S14)，归入注释层：Javadoc 标签本来就是注释的一部分，与数字拉开 ΔE 28.5，与注释/文档注释的最小 ΔE 为 13.3 |
| **注释** comment | `#7a7e85` · H218 S4 | `#859391` · H171 S6 · 4.36:1 | 文本层·冷石 | 官方是中性灰。矿彩把注释做成**冷石色**(H171 S6)：正文是暖墨、注释是冷石，同一屏里两种「温度」自然分层，注释不需要靠「更暗」来退后 |
| **文档注释** doc_comment | `#5f826b` · H141 S16 | `#578F7A` · H158 S24 · 3.72:1 | 文本层·冷石 | 同上，冷石色 + 斜体，明度压到 3.72:1，长 Javadoc 不会「发光」 |
| **选中** bg_selection | `#2A4371` · H219 S46 | `#365847` · H150 S24 · 1.75:1 | 同相·深绿 | 官方是蓝(H219)。矿彩把选中定为**同相深绿**(H150 S24)：选中是「焦点」信号，与底色同相、只靠明度抬起（1.75:1），不引入第三套色相；查找改用琥珀(H48)，用冷暖对照把两种状态分开 |
| **查找命中** bg_search | `#2d543f` · H148 S30 | `#594F25` · H48 S41 · 1.70:1 | 暖信号·琥珀 | ★ 这是矿彩最大胆的一处：官方/松林都用绿色命中；矿彩改用**琥珀**(H48 S41)，像荧光笔划过一样明确，且与「绿底」不再互相干扰。文字在琥珀上仍有 6.9:1 |

**贯穿两款的一条线**：底色 `#1F3027` 不动，对比度标准不动（正文 9:1 / 强调 6–7:1 / 注释 ~4.4:1 / 光标 10.7:1 / 行号 2.2:1），变的是**色相怎么分配给语义**。
<!-- MINERAL-DESIGN:END -->

**为什么关键字是橙不是绿**：绿色在 WCAG 里主导亮度，要在深底上达到官方那条
6.4:1 就必须做得很亮，就成了你否掉的"亮眼的绿"。官方自己的绿其实是
**低饱和**的（字符串 `#6aab73` 只有 28% 饱和）。所以本主题让**绿由字符串承担**
（Java 里到处都是），关键字回归官方的暖橙 —— 冷暖对比反而更耐看。

两条备选路线（已渲染存档，未采用）：
- `preview/java-v3.png` —— 关键字用柔和苔绿 `#6AB576`、字符串琥珀；观感更静，但整屏偏灰
- `preview/java-v4-types.png` —— 类型淡金版 `#B9AB71`，类型更醒目、整屏偏暖

---

## 2. 评审驱动的修订（共四轮）

初版交给一位资深 IDE 主题评审做对抗性评审，**6/10 → 8/10 → 8.5/10**。它的核心结论我完全认同：

> 单个色值都是有纪律的（它反算过 HSL，色相/饱和度确实都是官方值），
> 问题是**什么颜色负责什么职责**的分层没做 —— 绿同时铺在"面"和"字"上，
> 所有层级挤在 128°–162° 一条走廊里。

四轮修的东西（括号内为实测目标 → 结果）：

| 轮次 | 问题 | 修订 |
|---|---|---|
| 1 | 当前行像"脏斑"（1.04:1 且色相偏黄） | `#273D34` 同底相 → **1.19:1** |
| 1 | 注释与正文同色相，像"正文调了透明度" | 正文转暖中性(H51)、注释转冷绿灰(H114) |
| 1 | 浮层没浮起、无边框（1.11:1） | 浮层 **1.37:1** + 新增 `border` 描边 **1.77:1** |
| 1 | 光标只有官方一半对比 | `#E3E2DE` → **10.73:1**（官方 11.3） |
| 1 | 选中/查找/diff 三态互撞 | 选中搬到**青相** H196；diff 三态色相分离 |
| 2 | **我报的数字错了**：面板 S 说 14% 实为 20%；diff 最小色相差说 152° 实为 58°（漏比 add↔mod） | 复算并改正；**把撞色检查自动化**，不再手算 |
| 2 | 三面只有明度差、没有色度梯度 | 面板 `#1B211D`（**S 20%→10%**）、编辑器 S22%、浮层 S22% |
| 2 | `border` 一色两用（浮层轮廓 + 窗口发丝线） | 拆成 `border #3B5847`（只给浮层）+ `separator #2C3D35`（窗口内） |
| 3 | **`EFFECT_TYPE` 整体错位一格，32 个属性块受影响** —— 真实 IDE 里错误/警告波浪线会变成实线下划线 | 映射改 `{u:1, w:2, s:3, box:5}`；运行时错误按官方用 5；分布与官方对齐 |
| 3 | **`SELECTION_FOREGROUND` 是我自己加的**，一选中就抹掉全部语法色（官方不定义它 = 保留语法色） | 删除该键（根因：被 `--chrome-names` 启发式重新生成，加了显式跳过表） |
| 3 | `DEFAULT_REASSIGNED_*` 与注解/警告三值同色 | FG→标识符原色、EC→中性灰 `#7A7D77`、ET→1 |
| 3 | 光标所在标识符底色是暖中性暗块（高频） | → `#2E353C`（偏蓝灰，避开绿系与暖中性）；inlay hint 加底 |
| 4 | 色相分工闭合 | **暖中性 = 文本层**（fg/注释/行号）、**绿 = 内容层**（字符串/文档注释）、**其余 = 语义层** |
| 5 | **官方有 `EFFECT_TYPE` 而我完全没写的键有 10 个** —— 真机里 Javadoc `@param` 下划线、光标标识符下划线会直接消失（预览只画自己那条波浪线，照不到） | 10 个键逐个照官方补齐 ET/EC，并加 `NO_EFFECT_COLOR` 抑制表；规则固化为 `check_attribute_parity.py`（"官方有、我们缺失 → 报"，不再要求两边都有） |
| 5 | `DEFAULT_DOC_COMMENT_TAG` 与 `DEFAULT_METADATA` 被我合并成一个键（`@param` 与 `@Override` 同色） | 拆开：注解橄榄 `#B8B476` / Javadoc tag 绿 `#85B295`(5.83:1) + 下划线、不加粗 |
| 6 | **检查器自己有洞**：`if name not in mine: continue` 把"键完全没定义"跳过了 —— 而这恰恰是从 Darcula 继承、最该报的一类 | 删掉该分支；顺带查出根因：**采集脚本把名字带空格的键全过滤了**（官方属性键 220→**224**），补上 `Unresolved reference access`(ET=5) 等 |
| 6 | **渲染器把 Javadoc `@tag` 写死成 `annotation`**，`palette["doc_tag"]` 是死代码 → 改动静默失效，且官方对照那侧也被画错 | tag 改吃 `doc_tag`，官方对照补 `#67a37c`；像素复核 139 vs 49（此前两侧同为橄榄） |
| 6 | **产物比代码旧**：`cmd && echo` 在 `set -e` 下会**吞掉失败**（`&&` 列表里非末尾命令的失败不触发 `set -e`），渲染器崩了我却以为成功了 | 去掉 `&&`；色板矩阵容忍官方缺键；加**产物新鲜度断言** |
| 6 | **状态类属性块不该设 FOREGROUND**（官方一个都不设）——`WARNING` 的前景正好等于注解橄榄，刚拆开的颜色从另一个键长回来 | 5 个状态块改为"只给 ET+EC、不染文字" |
| 6 | 我以为官方 `IDENTIFIER_UNDER_CARET` 只有下划线、没有底色 —— **这是我的事实错误**，官方原文有 `BACKGROUND #373b39`（写入态 `#402f33`） | 按评审要求**换色而非删除**：读取态 `#405146`、写入态 `#45383A`，两者不同色；两个键都恢复"底+下划线" |
| 7 | **第四类盲区：BACKGROUND 对账** —— 官方有底而我们缺失的有 **17 个**，含 `EXECUTIONPOINT`(调试执行行)/`BREAKPOINT`/`NOT_TOP_FRAME` 三个调试器关键项；它们原本躺在"需真机走查"清单里，**其实静态可查** | parity 规则扩到 BACKGROUND（5 条规则）；17 个逐个补齐；`EXPLICIT` 表加 **AST 硬守卫**防重复键静默覆盖（这个坑咬过三次，守卫立刻又抓出 4 个） |
| 7 | `FILESTATUS_*_MERGED_WITH_*_CONFLICTS` 用了警告橄榄（合并冲突被降级成"提示"，且橄榄多了第 4 个含义） | 查官方原文后改红 `#C96A6F`（官方 `#DE6A66`） |
| 7 | `ERROR_HINT` 是**背景**色（官方 `#402929` 暗红），我给了亮红 `#F97884`；`DOC_COMMENT_LINK` 等于超链接色 | `ERROR_HINT`→`#3A2626`；`DOC_COMMENT_LINK`→teal `#4FA3B8`（官方 `#3887A1`）；`FILESTATUS_DELETED`→中性灰、`FILESTATUS_COPIED`→绿 |
| 7 | `INFO`/`TYPO`/`MARKED_FOR_REMOVAL` 的效果色与官方语义不符（INFO=函数蓝、拼写错误=编译错误红、forRemoval=灰） | 按官方调：`#8A7548` 暗琥珀 / `#7FC08A` 绿 / `#E86A72` 红 |

**四个只能靠"逐键对比官方原文"才能发现的 bug**（预览图结构上照不到）：`EFFECT_TYPE` 取值错位
（32 处）、官方有 `EFFECT_TYPE` 而我们完全没写（10 处）、`SELECTION_FOREGROUND` 抹掉语法色、
`DEFAULT_DOC_COMMENT_TAG` 与 `DEFAULT_METADATA` 被合并。为此把检查从"色值"升级到"**属性块**"，
并且规则写成"**官方有、我们缺失就报**"（而不是"两边都有才比"——后者正是我漏掉那 10 个键的原因）：

- `check_collisions.py`：状态色两两撞色（CIE ΔE2000 + WCAG），以官方为标尺，只在"比官方多出"时报错，例外需写明理由
- `check_attribute_parity.py`：与官方逐键对比 `EFFECT_TYPE` / `EFFECT_COLOR` 完备性

这两条规则把上述四个 bug 永久关闭。

现在的结论：**状态色两两可分性不劣于官方**（官方基线 2 对不达标，本主题 0 对）。

---

## 3. 安装

### 推荐：IDE 原生安装（不需要 Python）

先构建再打包（开发者执行一次）：

```bash
uv run green_eye.py build
uv run green_eye.py package
```

`release/green-eye-<version>.zip` 里就是可安装的 jar：

```
Settings / Preferences → Plugins → ⚙ → Install Plugin from Disk… → 选 jar
→ 完全退出并重启 IDEA
→ Settings → Appearance & Behavior → Appearance → Theme
```

jar 里已通过 `bundledColorScheme` + `themeProvider` 注册了两款主题，
所以装完在 Theme 和 Color Scheme 两个下拉框里都能看到。

### 脚本安装（跨平台）

```bash
uv run green_eye.py install          # 自动获得 Python + Pillow
python3 green_eye.py install         # 系统 Python 也可以
python3 green_eye.py install --dry-run
python3 green_eye.py install --uninstall
python3 green_eye.py install --icls-only
python3 green_eye.py install --all
```

安装器是纯 Python，macOS / Linux / Windows 原生都能跑，不依赖 bash、unzip、
grep、cmp、awk、shasum。`intellij/scripts/install.sh` 现在只是兼容壳。

装完**完全退出并重启 IDEA**，然后在
`Settings → Appearance & Behavior → Appearance → Theme` 里选「Green Eye Dark 松林」或「Green Eye Mineral 矿彩」。

### 幂等保证

安装器按"**先算计划 → 确认 → 再执行**"三段式工作，重复运行不会累积垃圾：

| 之前的形态 | 重装时的处理 |
|---|---|
| 旧版本 jar（如 1.0.0） | 删除 —— 两个同 id 插件共存会让 IDEA 报重复/禁用其中一个 |
| 被解压成 `plugins/GreenEye-Theme/` 目录 | 删除 —— 与 jar 形态同 id 冲突 |
| 手工导入/复制过同名 `.icls` | 删除 —— 否则 Color Scheme 下拉框里会出现两个同名项 |
| 用 `--icls-only` 装过，现在要装插件（或反过来） | 移除另一种形态 —— 两种模式互斥 |
| `disabled_plugins.txt` 里有本插件 | 移除该行 —— 否则重装也不会生效（其余插件的记录不动） |
| 已经装的是同一版本 | **跳过复制，连 mtime 都不改**，并输出"无需改动（幂等）" |

`python3 green_eye.py install --dry-run` 会打印同样的计划但不执行，可用于先确认要动哪些文件。


## 4. 文件清单

```
idea-green-theme/
├── README.md
├── scripts/
│   ├── build.sh                   兼容壳 → green_eye.py build
│   ├── install.sh                 兼容壳 → green_eye.py install
│   └── test_install.sh            兼容壳 → tests/test_install.py
├── themes/
│   ├── Green-Eye-Dark.icls          编辑器方案（475 属性 + 157 界面色）
│   ├── GreenEyeDark.theme.json      整站 UI 主题（330 color token + 68 个控件组覆盖）
│   └── GreenEyeDarkScheme.xml       打包进插件用的方案副本
├── dist/
│   └── GreenEye-Theme-1.1.0.jar     可安装插件
│       ├── META-INF/plugin.xml                注册 bundledColorScheme + themeProvider
│       ├── themes/GreenEyeDarkScheme.xml      编辑器配色方案
│       └── themes/GreenEyeDark.theme.json     整站 UI 主题
├── preview/                         预览图
│   ├── ui-dark.png                  整站 UI 仿真（工具窗 / 补全弹窗 / 状态栏）
│   ├── current-vs-official.png      官方 vs 正式版（同一段 Java）
│   ├── java-current.png / java-official.png
│   ├── current-swatches.png (+@2x)  色板矩阵（2× 便于逐值对账）
│   └── crop-*.png                   1:1 与 2× 局部裁剪
├── src/
│   ├── palette.py                   正式调色板（改这里就能改主题）
│   ├── build_pipeline.py            构建编排（取代 build.sh 的逻辑）
│   ├── install.py                   跨平台安装器（取代 install.sh 的逻辑）
│   ├── package_release.py           发布包：jar + icls + INSTALL.txt
│   ├── render_spec.py               无 Pillow 的 Java 样例 / 样式映射
│   ├── gen_icls.py                  生成 .icls
│   ├── gen_theme_json.py            生成 .theme.json 并打包插件 jar
│   ├── render_preview.py            仿 IDE 窗口渲染器（支持任意语言）
│   ├── render_java.py               Java 样例 + Java token 化器
│   ├── render_ui.py                 整站 UI 仿真图
│   ├── make_crops.py                1:1 / 2× 局部裁剪（逐像素核对用）
│   ├── check_collisions.py          ★ 状态色撞色检查（CIE ΔE2000，以官方为标尺）
│   ├── check_attribute_parity.py    ★ 与官方逐键对比（含"键完全缺失"）
│   ├── check_palette_usage.py       ★ 断言每个调色板键都被消费
│   ├── check_freshness.py           ★ 断言产物不早于源码
│   ├── check_style.py               ★ 格式守门（不需 black/ruff）
│   ├── gen_readme_table.py          从调色板自动重写本文配色表
│   ├── gen_verification_report.py   从产物自动生成 build/ref/verification.md
│   ├── analyze_official.py          分析官方内置方案（提炼规律）
│   ├── official_palette.py          还原官方配色 + 备选方案 V3/V4
│   ├── harvest_ide_keys.py          采集 IDE 内各语言/官方方案的配色键
│   └── validate_names2.py           键名精确校验（权威结论）
└── build/ref/
    ├── verification.md              ★ 验收报告（自动生成）
    ├── validation_report.md         键名来源与覆盖率的说明
    ├── ide_official_schemes/        官方内置方案原文（判断父方案的依据）
    ├── *_attribute_names.txt / *_chrome_names.txt   三个来源的键清单
    └── ide_language_report.txt      每个来源文件的明细
```

---

## 5. 已做的校验 / 未做的事

**自动校验（`green_eye.py build` 每次都会跑，任何一项失败即中止）**
完整结果见 [`build/ref/verification.md`](build/ref/verification.md)（从产物自动生成，**29 项全过**）：

| 类别 | 内容 |
|---|---|
| 键名来源 | 语法属性键 **475** 个，全部有真实来源（真实主题导出 349 + IDE 插件片段 56 + **官方内置方案 224**，并集去重后 475）；官方方案的属性键 **224/224 全覆盖**；界面色键 157 个，官方方案 **105/105 全覆盖**，13 个无效键已删 |
| 结构 | `.icls`/`.theme.json`/`plugin.xml` 均为合法 XML/JSON；`parent_scheme="Darcula"`；主题用**方案名**引用 `editorScheme`；`bundledColorScheme` 注册与方案 `name` 一致；`ui` 覆盖 68 个控件组（键名都在官方主题里出现过） |
| **与官方逐键对比（10 条规则，标尺 = `effective(官方 Islands Dark ∪ Darcula)`）** | `EFFECT_TYPE` 缺失 0 · 取值不同 0 · `EFFECT_COLOR` 缺失 0 · 键完全缺失 0 · `BACKGROUND` 缺失 0 · 背景强度低于 0.85× 的 0 个 · **`FONT_TYPE` 全一致** · **`ERROR_STRIPE_COLOR` 全有** · 自建键底色全 ≥1.10:1 · **风格家族一致性**（同族键的 `FONT_TYPE` 必须与规范键相同 —— 真机渲染查的是 `JAVA_KEYWORD` 这类语言键，只改规范键等于没改；这一条抓出 69 个语言键的排版偏差） |
| **反向覆盖（第 8 维度）** | 产物里的每个颜色都必须来自**它自己的**调色板 —— 正向检查发现不了"产物混进了另一款主题的颜色"（`grey_underline`/`followed_link` 就踩过）。两款均 0 越界 |
| **渲染样式一致（第 9 维度）** | 预览图里的斜体必须与产物 `FONT_TYPE` 一致 —— 这一维度曾被整段忽略（渲染器只吃颜色），导致 17 个键的粗斜体写错也没人发现。现已接上，且 `DEFAULT_STATIC_METHOD` 这类"mock 无法解析"的记为已知限制 |
| **主题身份（`check_identity.py`）** | 把"一眼看出是两款"变成判据：{字符串/数字/函数} 的最小 ΔE ≥ 15、**实测 token 频率加权**（剔除等于正文色的结构性别名）≥ 16、8 个主力 token 里 ≥5 个 ΔE ≥ 12。当前 **25.5 / 17.2 / 6** —— 达标 |
| **色觉缺陷模拟（第 10 维度）** | Machado 2009 模拟红/绿色盲：**已知缺口** —— 正常色觉可分、色盲下塌陷的有 58 对（官方靠发布 71 个 deuteranopia/protanopia 变体解决，我们暂未提供）。已把 `constant` 压到 4.20:1 让最严重的一对（常量↔错误）从 2.2 改善到 7.5 |
| **预览覆盖面** | 除代码视图外，还渲染 **diff 视图**与**调试器视图**（`render_diff_debug.py`）—— 状态色检查里最可疑的几条例外（diff 新增/删除/修改行、断点行、调用栈非栈顶帧、当前执行行）全部只在这两个视图出现，之前结构上无法证伪 |
| **状态色撞色** | CIE ΔE2000 + WCAG 对比度，以官方为标尺，四数并列不以"0"粉饰：检查 **269 对**，本主题未达阈值 2 对（**官方标尺里同样是这 2 对**）、已显式接受并写明理由 17 对、**未豁免 0 对**；官方标尺覆盖 29/32 个状态块键 |
| **重复键守卫** | 所有字典字面量出现重复键直接抛错 —— "同名静默覆盖"在 `EXPLICIT` 咬过三次、在 `ACCEPTED` 又咬了一次（一条理由被悄悄丢掉） |
| **格式守门** | `check_style.py`（无需 black/ruff）：语法可编译 · 同一字典里键所在行缩进一致 · 注释里无第二个 `#`（合并滑移特征）· 无超长行。首次运行抓到 `gen_icls.py` 一处键顶格、`palette.py` 两处注释被合并 |
| **前景 token 可分性（第 7 维度）** | 14 个前景 token 两两 ΔE2000：官方 ≥12 的配对我们也 ≥12；官方自己 <12 的配对（6 对）要求"不得比官方更近"。**两款主题均 0 违规** |
| **调色板消费** | 106 个键每个都至少被生成器或渲染器引用一次 —— 防"改了调色板但渲染器不消费"（`doc_tag` 就踩过） |
| **产物新鲜度** | `preview/*`、`themes/*`、`dist/*.jar` 全部不早于 `src/*.py` —— 防"拿旧图核新改动" |
| 对比度 | 正文 9.00:1 · 注释 4.41:1 · 文档注释 3.70:1 · 关键字/字符串 6.43:1 · 数字 6.39:1 · 函数 6.98:1 · 常量 5.92:1 · 注解 6.51:1 · Javadoc tag 5.83:1 · **光标 10.73:1** · 行号 2.20:1（官方 2.15） |
| 语义正确性 | 控制台 ANSI：`con_green` H128°、`con_red` H354°、`con_blue` H209° —— 不会因为"皮肤是绿的"把日志级别的绿也改成橙 |

**关于"已知盲区"（已关闭）**

早先 parity 检查的标尺只读官方 Islands Dark 的 XML，于是两类键对所有检查器隐身：
官方有 **13 个键只用 `baseAttributes` 定义**（`ANNOTATION_NAME_ATTRIBUTES`/`DEFAULT_FUNCTION_CALL`/`REGEXP.*` 等），
以及**由 Darcula 定义而官方未定义**的键（`CONSOLE_*_OUTPUT`/`DIFF_*`/`SPY-JS.*`/`EVALUATED_EXPRESSION*`）。

现已按 IntelliJ 的真实继承语义（**键在就用自己、字段缺省=清空；键不在才整块取父方案**）把标尺扩成
`effective(官方 ∪ Darcula)`，Darcula 从 `intellij.platform.ide.impl.jar` 的
`DefaultColorSchemesManager.xml` 抽出（`build/ref/Darcula.xml`）。**打开这个盲区后一次浮现 43 处/款**，
其中 30 处是真缺陷（JS 分析器的装饰、DIFF_* 的条纹、`DEBUGGER_INLINED_VALUES` 的斜体+ET=0、
`VELOCITY_KEYWORD`/`HAML_TAG` 的族冲突、`GENERIC_SERVER_ERROR_OR_WARNING` 的 ET 取值），全部已修；
其余是**有意清空 Darcula 底色**的 27 个键（控制台/终端按颜色分级铺底、JS 分析器铺底等），
已写成带理由的显式清单（`BG_EXEMPT`/`SPY_EXEMPT`/`STRENGTH_EXEMPT`）。

**未做（如实说明）**

- **没有在真实 IDE 内加载过。** 两条自动验证路线都试过且都不成立：
  - 无头模式（`inspect.sh` + 隔离配置）：插件确实加载了，但无头模式不初始化 LaF，
    `EditorColorsManager` 根本没被构造，出错那段代码没执行。我做了"复刻旧 bug 的
    对照包"，它在无头下同样干净 —— 证明这条路测不出来（假阳性）；
  - 隔离配置的 GUI 启动：新配置目录没有许可证，日志显示
    `Marking plugins 'disabled': [com.intellij.modules.ultimate]`，
    而 Islands/Darcula/Light 这些主题与内置方案恰好都由该模块声明，
    所以隔离环境与你的真实（已授权）环境不等价。
- 因此正确性依据是"逐键照抄 JetBrains 官方内置方案的写法"（`parent_scheme`、注册方式、
  `EFFECT_TYPE`/`EFFECT_COLOR` 完备性都做了与官方原文的自动对账），而不是一次成功的实机运行。
- 预览图是按调色板渲染的**仿真窗口**，不等于 IDE 真实截图。

**哪些已经关闭、哪些还没有**

| | 状态 |
|---|---|
| 配色分层（面/字/语义/状态四层）、色相分工、对比度、状态色两两可分 | ✅ 已关闭（撞色检查以官方为标尺，0 对劣于官方） |
| 官方属性块的装饰完备性（`EFFECT_TYPE`/`EFFECT_COLOR`/键缺失） | ✅ 已关闭（逐键对比 4 项全 0；这一类曾连续漏掉 32 处和 10 处） |
| 调色板改动是否真的生效（渲染器消费 / 产物新鲜度） | ✅ 已关闭（两条断言进管线；`doc_tag` 与"旧图核新改动"都踩过） |
| **真机逐屏走查**：diff 视图、调试器变量表、inlay hints、多光标、VCS/搜索/inspection 面板、gutter 各态 | ⬜ **未覆盖** —— 预览管线结构上照不到这些屏（`EFFECT_TYPE` 那两类 bug 就是从这里漏的），需要实机确认 |

即：**静态可查的部分已经关闭并附有断言输出；剩下的是覆盖面的问题，不是已知缺陷。**

上面那 6 屏怎么快速扫一遍 → **[`../docs/manual-verification.md`](../docs/manual-verification.md)**（按装饰线、调试器、diff、inlay hints、状态色和主观项分组）。

<!-- DEVIATIONS:BEGIN -->
### 有意偏离官方的取舍（不是缺陷，逐条给理由）

评审要求把**取舍与缺陷分开**，否则下一轮会被当 bug 报回来。以下每一项都写清了「偏离什么 / 为什么 / 代价是什么」：

| 偏离 | 具体 | 为什么 | 代价 |
|---|---|---|---|
| **墨色整体转暖中性** | 官方正文 `#bcbec4`（中性灰）、注释 `#7a7e85`；本主题正文 `#D1D0CA`(H51)、注释 `#93918A`(H48) | 官方是**中性底**配中性字；本主题底色是绿的，如果字也用中性灰，整屏会读成「绿底上蒙了一层灰」（第一轮评审的原话是「就是左侧乘了个绿蒙版」）。把墨色移到暖侧，让**绿只属于内容层**（字符串/文档注释），层次才立得住。 | 偏离了官方的中性墨色；在极高亮度屏上暖中性会比中性灰略「柔」一点。 |
| **底色降到 S≈21%、面板降到 S≈10%** | 官方编辑器 `#191A1C`(S≈5%) / 面板 `#26282C`；本主题 `#1F3027`(S≈21%) / 面板 `#1B211D`(S≈10%) | 绿色身份主要靠底色承载。但三个面如果都同色度、只有明度差，就会「糊成一片」（第二轮评审实测：三个面 S 全是 20–21%）。所以让面板明显更中性，形成**色度梯度**而不是明度梯度。 | 面板的「绿」几乎不可见，只有并排看才察觉；这是刻意的。 |
| **强调色沿用官方的色相/饱和度，只挪明度** | 关键字 `#D9A58B`(官方 `#cf8e6d`)、字符串 `#8BBD84`(官方 `#6aab73`)、数字 `#2FC1CF`(官方 `#2aacb8`)、常量 `#D296C8`(官方 `#c77dbb`)、注解 `#B8B476`(官方 `#b3ae60`) | 评审反算过 HSL：这些色的 H/S 与官方**完全一致**，只把明度调到绿底上的等效对比度。这是本主题「改皮不改骨」的核心做法。 | 两个例外：字符串色相 128°→112°（与底色间距从 20° 拉到 36°，否则压暗会沉底）、函数蓝饱和度 89%→79%（它在绿底上显得像外来户）。 |
| **Javadoc tag 与注解分开** | 官方 `DEFAULT_DOC_COMMENT_TAG`=`#67a37c`(绿+下划线) / `DEFAULT_METADATA`=`#b3ae60`(橄榄)；本主题 `#85B295` / `#B8B476` | 官方本来就分开：tag 属于**绿色注释家族**，橄榄是注解专用。我早先误把两者合并成一个键，导致 `@param` 和 `@Override` 同色（第五轮评审发现）。现在已按官方拆开。 | 无 —— 这一条是回归官方，不是偏离。 |
| **光标标识符底色用绿灰族** | 官方 `#373b39`（中性）/ 写入态 `#402f33`（偏红）；本主题 `#3E4A50` / `#45383A` | 官方这两个键**有底色**（我一度误以为没有而删掉，第六轮被评审纠正）。底色保留，只把色相挪到绿灰/红灰族，避免编辑器里出现唯一一块「既非绿也非暖」的面。 | 读取态与写入态的区分度比官方略低（官方的偏红更跳）。 |
| **状态块只画线、不染文字** | 官方 `ERRORS_ATTRIBUTES`/`WARNING_ATTRIBUTES`/`INFO_ATTRIBUTES`/`TYPO`/`MARKED_FOR_REMOVAL` **都不设 FOREGROUND** | 这是**照官方做**：错误/警告只以波浪线表达，不把标识符文字染红，更耐看；也顺带避免 `WARNING` 的前景与注解橄榄撞车。 | 无 —— 回归官方。 |
| **`bg_diff_add` 与弹窗底 `bg_raised` 的 ΔE 只有 6.8** | 检查器以官方为标尺时会报这一对（其余 51 对全部达标） | 两者不同视图，且弹窗有 1.77:1 描边隔开；要拉开到 ΔE≥12 需把新增行饱和度提到 **68%**（我穷举过全表），会过艳。Δhue 38° 已足够，且这组是第三轮评审明确接受的。 | inlay hint 芯片复用浮层底，落在 diff 新增行上时边界会消失；接受，因为 hint 文字在 `#2E4A2A` 上仍有 2.97:1，且 diff 视图的首要信号是行填充。 |
| **背景强度按「相对各自编辑器底」换算，而不是照抄官方 hex** | 官方的背景类颜色是在 `#191A1C` 上定的。本主题底是 `#1F3027`（更亮），直接照抄会让相对强度掉到官方的 0.6–0.8 倍（实测 `KOTLIN_SMART_CAST_*` 与 `BREAKPOINT_ATTRIBUTES` 只有 1.03:1 —— 那不是「低调」，是等于没有底色） | 所以每个背景键都按 `对比度(我们的底色, 我们的编辑器底) ≥ 0.85 × 官方同值` 重算明度；这条已经写成第 6 条自动对账规则，低于阈值会直接 fail。 | 只有 1 个键有意低于阈值：`INLINE_PARAMETER_HINT_CURRENT`（官方用独立蓝底 2.31×，我用同底 + 更亮前景 #9188EC vs #908D82）；给它独立底色会与查找/光标标识符底色撞色，实测过 3 组值都过不了。已在豁免表写明理由。 |
| **VCS / 链接色向官方靠但没有照抄数值** | `DOC_COMMENT_LINK`: 官方 `#3887A1` → 本主题 `#4FA3B8`；`FILESTATUS_DELETED`: 官方 `#6F737A` → 本主题 `#8A8F88`；合并冲突: 官方 `#DE6A66` → 本主题 `#C96A6F` | 官方的这些值是在**中性底**上定的，直接搬到绿底上会偏灰或偏暗，所以按同一语义换到等效明度。 | 色相与官方一致，只有明度差。 |

上表 9 条中，**2 条其实是「回归官方」而非偏离**（代价栏标为「无」）：早先版本偏离了官方，评审发现后改回。

对话之外的判断依据：撞色检查（以官方为标尺，0 对劣于官方）、逐键对比（`EFFECT_TYPE`/`EFFECT_COLOR`/`BACKGROUND`/键缺失 五项全 0 差异）、调色板消费、产物新鲜度 —— 四条断言全部挂在 `green_eye.py build` 里。
<!-- DEVIATIONS:END -->

## 6. 1.0.0 启动报错的根因（留档）

```
PluginException: Light [Plugin: com.greeneye.intellij.theme]
  at SchemeManagerImpl.loadBundledSchemes
Caused by: InvalidDataException: Light
  at AbstractColorsScheme.resolveParent
```

两个叠加的错误：

1. **引用方式错了**：主题 JSON 用 `"editorScheme": "/schemes/GreenEyeLight.xml"`
   （**路径**引用），这会把该文件当成 bundled scheme 在启动早期加载。
2. **父方案名不可解析**：写了 `parent_scheme="Light"`。`Light` 确实存在，
   但它由 **Ultimate 定制插件**声明为 `<bundledColorScheme id="Light" .../>`，
   在方案批量加载那一刻还没注册，于是 `resolveParent("Light")` 抛异常。

官方写法（一手证据）：

```xml
<!-- lib/intellij.idea.ultimate.customization.jar!/META-INF/plugin.xml -->
<bundledColorScheme id="Islands Dark" path="/themes/islands/IslandSchemeDark.xml" />
<themeProvider id="Islands Dark" path="/themes/islands/ManyIslandsDark.theme.json" />
```
```xml
<!-- lib/intellij.platform.ide.impl.jar!/themes/islands/IslandSchemeDark.xml -->
<scheme name="Islands Dark" version="142" parent_scheme="Darcula">
```

把 6 个官方方案的 `parent_scheme` 全抓出来对账：**浅色一律 `Default`、深色一律
`Darcula`，无一例外**。1.1.0 照此执行：方案放 `themes/` 下、
`<bundledColorScheme>` 显式注册、主题用**方案名**引用、
`parent_scheme="Darcula"`。

---

## 7. 配合主题更护眼的建议

| 项 | 建议 | 原因 |
|---|---|---|
| 字号 | 14~16 px | 小字号迫使你凑近屏幕 |
| 行高 | 1.2 ~ 1.3 | 行距过密容易串行 |
| 字体 | `JetBrains Mono` / `更纱黑体` / `Maple Mono` | 中英文等宽对齐 |
| 屏幕亮度 | 接近环境光，别比环境亮很多 | 亮度反差是主要眩光源 |
| 减少动效 | `Settings → Appearance` 关掉动画 | 减少余光干扰 |

---

## 8. 想自己改配色？

颜色集中在 [`src/palette.py`](src/palette.py)，改完重新生成：

```bash
uv run green_eye.py build              # 跨平台：自动提供 Python + Pillow
python3 green_eye.py build --no-preview  # 不生成预览图，不需要 Pillow
```

它依次执行下面的阶段，**任何一步失败即中止**，避免生成半成品：

| 阶段 | 脚本 | 作用 |
|---|---|---|
| 0 | `check_style.py` | **格式守门**：语法可编译 · 字典键缩进一致 · 无堆叠注释 · 无超长行 |
| 1 | `gen_icls.py` | 生成 `.icls` 并打印对比度报告 |
| 2 | `check_collisions.py` / `check_token_separation.py` / `check_identity.py` / `check_reverse_palette.py` / `check_render_styles.py` / `check_attribute_parity.py` | 撞色、token 可分、主题身份、反向调色板、渲染样式、官方逐键对账 |
| 3 | `gen_theme_json.py` | 生成 `.theme.json` 并打包插件 jar |
| 3.5 | `tests/test_install.py` | 安装器集成测试（jar 打好之后跑） |
| 4 | `gen_readme_table.py` / `gen_deviations.py` / `gen_mineral_doc.py` | 从调色板**自动重写本文的生成段** |
| 5 | `export_palette.py` + `check_palette.py` | 重导 `shared/palette.json` 并做平台无关验收 |
| 6 | `render_java.py` / `render_ui.py` / `render_diff_debug.py` | 渲染代码 / 整站 UI / diff / 调试器四类视图（`--no-preview` 跳过） |
| 7 | `check_palette_usage.py` / `check_freshness.py` | 断言调色板被消费、产物不早于源码 |
| 8 | `gen_verification_report.py` | 生成 [`build/ref/verification.md`](build/ref/verification.md)（29 项） |

调色板的键名是语义化的（`keyword` / `string` / `comment` / `bg_editor` …），
生成器会自动映射到 IntelliJ 的 475 个属性键上。
