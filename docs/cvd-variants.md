# CVD 变体设计说明（P3-13 阶段 2）

## 现状

[`build/ref/cvd-report.md`](../intellij/build/ref/cvd-report.md)（由 `green_eye.py cvd` 生成）
逐对列出正常色觉可分、但在 protanopia / deuteranopia 模拟下 ΔE2000 < 12 的 token：

- 松林 Green Eye Dark：**18 对**
- 矿彩 Green Eye Mineral：**20 对**

最严重的是：

| 主题 | 配对 | 正常 ΔE | 最差 CVD ΔE |
|---|---|---|---|
| 松林 | `string` ↔ `error` | 55.6 | 1.3（deuteranopia） |
| 松林 | `keyword` ↔ `string` | 33.6 | 2.0（deuteranopia） |
| 松林 | `comment` ↔ `error` | 27.5 | 2.4（protanopia） |
| 矿彩 | 见报告 | — | — |

## 自动求解原型（未采纳）

试过一版纯数值优化：

- 只调整前景 token，背景/UI 不动；
- 约束：正常对比度不低于角色下限、正常色觉下 token 两两 ΔE ≥ 12；
- 目标：最大化 CVD 模拟下 token 两两 ΔE 的最小值；
- 方法：随机局部搜索（候选色 = Okabe-Ito 种子 + HSL 色相/明度网格）。

结果：

- 最差 CVD ΔE 从 **1–2 提升到 9–10**；
- 但颜色语义崩坏，例如：
  - `comment` 变成黄绿色 `#C3D537`；
  - `error` 变成蓝色 `#8B94E6`；
  - `string` 变成粉色 `#CCAAA0`。

**结论：这不是纯数值优化问题。** 12 个 token 在 CVD 模拟后的二维色空间里要同时满足
ΔE ≥ 12，还要保持"错误是红、字符串是绿、注释是灰"的语义，必须由人做取舍和审美判断。
原型只作为"约束可行域"的探测，不进入发布产物。

### 最小改动原型（方案 A 的探测）

又试了一版**只改 1–2 个语义 token**、且候选色限制在语义合理色相内的搜索：

| 主题 / 变体 | 调整 | 塌陷对数 | 最差 CVD ΔE |
|---|---|---|---|
| 松林 protanopia | `keyword` → `#BEB22F`、`error` → `#DF7E9F` | 18 → **9** | 2.6 |
| 松林 deuteranopia | `keyword` → `#BDB33F`、`annotation` → `#D8A9C1` | 18 → **9** | 1.3 |
| 矿彩 protanopia | `doc_tag` → `#7DA1A8`、`doc_comment` → `#667D82` | 20 → **9** | 3.0 |
| 矿彩 deuteranopia | `annotation` → `#D5A288`、`doc_tag` → `#77A495` | 20 → **10** | 2.8 |

即使只改两个 token，塌陷也只能减半，最差配对仍然是
`string` ↔ `error`、`string` ↔ `annotation`、`comment` ↔ `doc_comment`，
最差 ΔE 仍只有 1.3–3.0。

**结论：方案 A 只能是"改善"，不可能单靠 1–2 个 token 达到 CVD 安全。**
要真正关闭缺口，需要方案 B（整屏 CVD 安全盘）或接受并明确列出残余配对。

## 设计选项

### A. 只修最严重的 3–5 对（推荐先试）

- 只改 `error` / `string` / `keyword` / `annotation` 中冲突最重的几个；
- `comment` / `doc_comment` / 背景 / UI 尽量不动；
- 接受仍然存在的少量 CVD 塌陷，在变体说明里如实列出；
- 优点：改动小、语义保留好、可逐项评审；
- 缺点：不是"完全 CVD 安全"，只是"明显改善"。

### B. Okabe-Ito 风格的 8 色 CVD 安全盘

- 用一组经过色盲友好设计的种子色（橙/天蓝/蓝绿/黄/蓝/朱红/紫红/灰）；
- 整屏重新分配 token，允许主题身份与基础版明显不同；
- 优点：CVD 下分离度最好；
- 缺点：等于重新设计一套主题，需要重新过对比度、身份、审美评审。

### C. 暂不提供变体，只发布报告

- 保持当前状态：报告量化缺口，主题本体不冒充 CVD 安全；
- 优点：不误导用户；
- 缺点：P3-13 不关闭。

## 如果做，建议的默认参数

- 平台：先做 **VS Code**（theme JSON 简单、验证成本低），再考虑 IntelliJ；
- 范围：只调整塌陷的 token，背景/UI 不动；
- 命名：`Green Eye Dark (Deuteranopia)` / `Green Eye Dark (Protanopia)`，矿彩同理；
- 入口：`green_eye.py cvd-variants`，不默认进主 `build`；
- 产物：`vscode/themes/green-eye-dark-deuteranopia.json` 等 + 独立 `.vsix`。

## 验收标准（建议）

任何 CVD 变体在发布前至少满足：

1. **CVD 分离**：目标 token 两两在 protanopia / deuteranopia 下 ΔE ≥ 12；
   若无法全部达到，必须在变体 README 中列出残余配对，且不得比基础版更差。
2. **正常对比度**：不低于 `shared/tools/check_palette.py` 的角色下限。
3. **正常身份**：与基础主题的对应 token 保持可识别的语义（错误仍偏红/暖、字符串仍偏冷等）。
4. **视觉走查**：在真实 VS Code / IDEA 里用 CVD 模拟或截图确认，不只看数字。

## 当前决定

在拿到明确的设计取舍前，**不自动生成并发布 CVD 变体**。
本轮只完成报告与设计说明；阶段 2 仍待定。
