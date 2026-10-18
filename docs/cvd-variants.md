# CVD 变体：A+「CVD Improved」已采纳

## 现状

[`build/ref/cvd-report.md`](../intellij/build/ref/cvd-report.md)（由 `green_eye.py cvd` 生成）
逐对列出正常色觉可分、但在 protanopia / deuteranopia 模拟下 ΔE2000 < 12 的 token：

- 松林 Green Eye Dark：**18 对**
- 矿彩 Green Eye Mineral：**20 对**

最严重的几对：

| 主题 | 配对 | 正常 ΔE | 最差 CVD ΔE |
|---|---|---|---|
| 松林 | `string` ↔ `error` | 55.6 | 1.3（deuteranopia） |
| 松林 | `keyword` ↔ `string` | 33.6 | 2.0（deuteranopia） |
| 松林 | `comment` ↔ `error` | 27.5 | 2.4（protanopia） |
| 矿彩 | 见报告 | — | — |

## 预览

```bash
python3 green_eye.py cvd --preview
```

生成 `intellij/preview/cvd-compare.png`：每款主题逐 token 并排显示
正常 / protanopia / deuteranopia 三种色值。

## A+ 实现（已采纳）

只改 3 个 token，背景 / UI / 其余前景不动：

| 主题 | 槽位 | 原值 | CVD Improved | 对比度 |
|---|---|---|---|---|
| 松林 | `string` | `#8BBD84` | `#6BC087` | 6.30:1 |
| 松林 | `doc_tag` | `#85B295` | `#91AFB6` | 5.97:1 |
| 松林 | `doc_comment` | `#658C7C` | `#577F87` | 3.17:1 |
| 矿彩 | `annotation` | `#D8A5B8` | `#D2AD9B` | 6.75:1 |
| 矿彩 | `doc_tag` | `#A6BCAD` | `#899BC0` | 4.97:1 |
| 矿彩 | `doc_comment` | `#578F7A` | `#707A8F` | 3.22:1 |

按正式 `gen_cvd_report.collapse_pairs` 口径复核后的真实结果：

| 主题 | 原塌陷 | CVD Improved | 正常最小 ΔE | protanopia | deuteranopia |
|---|---|---|---|---|---|
| 松林 | 18 | **13** | 12.5 | 11 | 12 |
| 矿彩 | 20 | **14** | 12.2 | 10 | 12 |

**这不是 CVD 安全版**：仍有 13 / 14 对塌陷，最差 ΔE 约 2.3 / 4.6。
残余配对照实写入 `build/ref/cvd-variants-report.md`，不宣称“色盲友好”。

### 命令与产物

```bash
python3 green_eye.py cvd-variants
# 或 make cvd-variants
```

产物：

```
intellij/themes/variants/Green-Eye-Dark-CVD.icls
intellij/themes/variants/Green-Eye-Mineral-CVD.icls
vscode/themes/variants/green-eye-dark-cvd.json
vscode/themes/variants/green-eye-mineral-cvd.json
vscode/dist/green-eye-cvd-variants-<version>.vsix
release/green-eye-<version>-cvd.zip
```

- IntelliJ：`Color Scheme -> 齿轮 -> Import Scheme...` 选 `.icls`；
- VS Code：安装变体 `.vsix`，主题名 `Green Eye Dark (CVD Improved)` / `Green Eye Mineral (CVD Improved)`；
- 汇总包里的 `cvd-variants-report.md` 列出残余配对。

## 为什么没有走 B / C

- **B（整屏 Okabe-Ito 安全盘）**：需要重新设计主题身份，工作量和审美风险都大；本轮未做。
- **C（不做变体）**：用户已选择 A+，因此保留为备选，不再作为当前状态。

## 早期原型的教训

试过纯数值优化：它能提高最差 CVD ΔE，但会把 `comment` 变黄、`error` 变蓝，
语义崩坏，因此未采纳。

也试过“只改 1–2 个 token”的估计，早期脚本曾给出 9/10 对的数字；
后来用正式的 `collapse_pairs` 复核，发现口径不一致，真实只能到 13/14。
现在仓库里的 `cvd-variants-report.md` 和测试都以正式口径为准，不再使用早期估计。

## 验收标准

1. **真实残余**：必须用 `collapse_pairs` 统计，且在 README / 报告中列出；
2. **正常对比度**：不低于 `shared/tools/check_palette.py` 的角色下限；
3. **正常身份**：字符串仍偏冷、错误仍偏暖、注释仍中性；
4. **不冒充安全**：名称用 `CVD Improved`，不用 `CVD Safe`；
5. **视觉走查**：CVD 变体仍需在真实 IDE 里目视确认。
