# Green Eye · 护眼绿色主题家族

**同一套设计系统，面向多个编辑器。** 底色锚定在同一块墨绿 `#1F3027`，
对比度是设计约束而不是事后检查；换平台时**底色与对比度标准不变**，
变的是"色相如何分配给语义"以及各平台的实现方式。

变更记录见 [CHANGELOG.md](CHANGELOG.md)；第三方材料与许可证说明见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 平台

| 平台 | 状态 | 入口 |
|---|---|---|
| IntelliJ IDEA | ✅ 已实现 | `green_eye.py build` / `green_eye.py install` |
| VS Code | ✅ 已实现 | `green_eye.py vscode` |

## 目录结构

```
green-eye-theme/
├── green_eye.py          ★ 跨平台入口：build / check / palette / vscode / cvd / doctor / bump / test / install / package
├── Makefile              兼容入口（薄封装，逻辑都在 green_eye.py）
├── CHANGELOG.md          变更记录
├── THIRD_PARTY_NOTICES.md 第三方材料与许可证说明
├── docs/                 人工核对与维护文档
├── shared/               平台无关层：色值契约 + 通用检查
│   ├── palette.json       生成物：两款主题的全部色值 + 语义角色表 + 例外清单
│   ├── export_palette.py  从 intellij 侧导出（单向：intellij → shared）
│   ├── README.md          设计法则、契约 schema、四类判据
│   └── tools/             无依赖的色彩数学 + 平台无关验收
│
├── intellij/              IntelliJ IDEA 实现
│   ├── scripts/            兼容入口（薄封装，逻辑都在 src/）
│   ├── src/                生成器、检查器、跨平台安装器（Python）
│   ├── themes/             生成的 .icls + .theme.json
│   ├── dist/               生成的插件 jar
│   ├── preview/            生成的预览图
│   └── build/              官方参考资料（构建输入）与验收报告
│
├── release/              生成的发布包（jar + icls + INSTALL + 第三方说明）
├── tests/                CLI / 安装器 / 字体 / 色彩 / VS Code / 发布包测试
└── vscode/               ✅ VS Code 实现：themes/ + dist/*.vsix
```

## 两款主题（同一块底，两套设计语言）

| | 「松林」Green Eye Dark | 「矿彩」Green Eye Mineral |
|---|---|---|
| 定位 | 参考 JetBrains 官方 Islands Dark 的色相/饱和度，只按对比度重解明度 | 以底色为中心的**原创设计**，做**角色互换** |
| 语言 | 整体暖黄绿 | **暖矿结构 + 冷矿内容** |
| 关键字 / 常量 / 注解 | 橙 `#D9A58B` / 紫 `#D296C8` / 橄榄 `#B8B476` | 金黄 `#D7BA76` / 赭石 `#B58268` / 玫瑰 `#D8A5B8` |
| 字符串 / 数字 / 函数 | 绿 `#8BBD84` / 青 `#2FC1CF` / 电光蓝 `#85BDF1` | 冰青 `#94B8C5` / 紫晶 `#C1A5DA` / 玉青 `#5FCAB4` |
| 选中 / 查找 | 青 `#335662` / 绿 `#2D5440` | 绿 `#365847` / 琥珀 `#594F25` |

两款必须**一眼能看出是两款**：`novelty 25.5`（≥15）· 频率加权 `17.5`（≥16）· 主力 token 6/8（≥5）。
判据与权重都写在 `shared/palette.json` 与 `shared/tools/check_palette.py` 里。

## 快速开始

### 给用户：安装主题（不需要 Python）

先生成发布包（开发者执行一次）：

```bash
uv run green_eye.py build        # 先生成 jar 与 .icls
uv run green_eye.py package      # IntelliJ 发布包
uv run green_eye.py package --all  # IntelliJ + VS Code 合并包
# 或：python3 green_eye.py build --no-preview && python3 green_eye.py package
```

得到 `release/green-eye-<version>.zip`；`--all` 会同时产出单平台包与 `-all.zip`，
里面是 jar + 两个 `.icls` + `INSTALL.txt`；合并包还包含 VS Code `.vsix`。
把这个 zip 拷到目标电脑，解压后：

1. IDEA → `Settings / Preferences → Plugins`
2. 右上角齿轮 → **Install Plugin from Disk…**
3. 选 `GreenEye-Theme-<version>.jar`
4. **完全退出并重启 IDEA**
5. `Settings → Appearance & Behavior → Appearance → Theme`
   选「Green Eye Dark 松林」或「Green Eye Mineral 矿彩」

**目标电脑不需要 Python、bash、make、unzip 或任何运行时。**
只想导入配色方案时，用 `Settings → Editor → Color Scheme → ⚙ → Import Scheme…`
选 `.icls` 即可。

### 给开发者：构建

推荐 `uv`——一个跨平台单文件二进制，会自动提供 Python 和 Pillow：

```bash
# 首次安装 uv（三选一）
brew install uv
winget install astral-sh.uv
curl -LsSf https://astral.sh/uv/install.sh | sh

uv run green_eye.py build        # 生成 + 校验 + 预览 + 打包 + 安装器测试
uv run green_eye.py install      # 安装到本机 IDEA
uv run green_eye.py vscode       # 生成 VS Code 主题 + .vsix
```

没有 uv、或不想装 Pillow 时，系统 Python 也能构建核心产物：

```bash
python3 green_eye.py build --no-preview   # 不渲染预览图，不需要 Pillow
python3 green_eye.py palette              # 只导出/验收 shared/palette.json
python3 green_eye.py vscode               # 生成 VS Code 主题 + .vsix
python3 green_eye.py cvd --preview        # CVD 报告 + 对比色板（需 Pillow）
python3 green_eye.py doctor               # 预检产物/字体/安装状态
python3 green_eye.py check                # 平台无关色值验收（需先 build）
python3 green_eye.py test                 # CLI + 安装器 + 字体 + 色彩 + VS Code + 发布包测试
```

Windows 原生用 `py` 代替 `python3` 即可。`make` 仍保留为兼容入口，
`make build` / `make build-no-preview` / `make install` 等价于上面的命令。

预览字体会自动在 macOS / Linux / Windows 的常见字体路径里查找；找不到时不会崩溃，
而是回退到 Pillow 默认字体并打印一次警告。想固定字体可以显式指定：

```bash
GREEN_EYE_CJK_FONT=/path/to/font.ttc uv run green_eye.py build
# Linux 一般装 fonts-noto-cjk 即可；Windows 自带微软雅黑
```

安装器是幂等的，所有改动先生成计划，文件替换用临时文件 + 原子重命名，
旧版本只在新文件准备好后清理。装完完全退出并重启 IDEA 即可选主题。

底层等价入口（macOS / Linux 的兼容壳）：

```bash
bash intellij/scripts/build.sh
bash intellij/scripts/install.sh --config-dir "/path/to/IntelliJIdea2026.2"
```

## 持续集成

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) 在 macOS / Ubuntu / Windows 上运行：

```bash
uv run green_eye.py build
uv run green_eye.py vscode
uv run green_eye.py test
uv run green_eye.py package --all
```

并上传 `release/*.zip` 与 `vscode/dist/*.vsix` 作为构建产物；
Linux 会预装 `fonts-noto-cjk` 以生成完整预览。

推 `v*` tag 时，[`.github/workflows/release.yml`](.github/workflows/release.yml)
会重新构建并创建 GitHub Release，附上 IntelliJ 包、合并包与 VS Code `.vsix`。

## 加一个新平台（例如 VS Code）

1. 读 `shared/palette.json`（不要读 IntelliJ 的 `.icls`——那是实现细节）；
2. 新建 `<platform>/`，把语义槽位映射到该平台的键（VS Code 的映射表已在 `vscode/README.md` 给出）；
3. 用 `shared/tools/check_palette.py` 做验收 —— 它只按色值判定，与平台无关；
4. `shared/palette.json` **由 `green_eye.py build` 自动重导**，不要手改；只改 `intellij/src/palette.py`。
