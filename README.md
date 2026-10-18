# Green Eye · 护眼绿色主题家族

**同一套设计系统，面向多个编辑器。** 底色锚定在同一块墨绿 `#1F3027`，
对比度是设计约束而不是事后检查；换平台时**底色与对比度标准不变**，
变的是"色相如何分配给语义"以及各平台的实现方式。

## 目录结构

```
green-eye-theme/
├── Makefile              统一入口：build / test / install / uninstall
├── docs/                 人工核对与维护文档
├── shared/               平台无关层：色值契约 + 通用检查
│   ├── palette.json       两款主题的全部色值（224 个）+ 语义角色表 + 例外清单
│   ├── export_palette.py  从 intellij 侧导出（单向：intellij → shared）
│   ├── README.md          设计法则、契约 schema、四类判据
│   └── tools/             无依赖的色彩数学 + 平台无关验收
│
├── intellij/              IntelliJ IDEA 实现
│   ├── scripts/            构建、安装、测试的唯一入口实现
│   ├── src/                生成器与检查器（Python）
│   ├── themes/             生成的 .icls + .theme.json
│   ├── dist/               生成的插件 jar
│   ├── preview/            生成的预览图
│   └── build/              官方参考资料与验收报告
│
└── vscode/            ⬜ 待实现 —— VS Code 实现（见其 README）
```

## 两款主题（同一块底，两套设计语言）

| | 「松林」Green Eye Dark | 「矿彩」Green Eye Mineral |
|---|---|---|
| 定位 | 参考 JetBrains 官方 Islands Dark 的色相/饱和度，只按对比度重解明度 | 以底色为中心的**原创设计**，做**角色互换** |
| 语言 | 整体暖黄绿 | **暖矿结构 + 冷矿内容** |
| 关键字 / 常量 / 注解 | 橙 `#D9A58B` / 紫 `#D296C8` / 橄榄 `#B8B476` | 琥珀 `#D7BA76` / 赭石 `#B58268` / 玫瑰 `#D8A5B8` |
| 字符串 / 数字 / 函数 | 绿 `#8BBD84` / 青 `#2FC1CF` / 电光蓝 `#85BDF1` | 冰青 `#94B8C5` / 紫晶 `#C1A5DA` / 玉青 `#5FCAB4` |
| 选中 / 查找 | 青 `#335662` / 绿 `#2D5440` | 石板蓝 `#3E5173` / 琥珀 `#594F25` |

两款必须**一眼能看出是两款**：`novelty 25.5`（≥15）· 频率加权 `17.5`（≥16）· 主力 token 6/8（≥5）。
判据与权重都写在 `shared/palette.json` 与 `shared/tools/check_palette.py` 里。

## 快速开始

```bash
make setup                   # 首次使用：创建 .venv 并安装 Pillow
make build                   # 生成、校验、预览和打包
make test                    # 安装器集成测试
make install                 # 交互式安装插件
make install-dry-run         # 只显示安装计划
make uninstall               # 卸载插件、配色副本和禁用记录
```

安装器是幂等的，支持 macOS、Linux 和 Windows Git Bash；所有改动先生成计划，
文件替换采用临时文件加原子重命名，旧版本只在新文件准备好后清理。
装完完全退出并重启 IDEA，在 `Settings → Appearance & Behavior → Appearance → Theme` 里选
「Green Eye Dark 松林」或「Green Eye Mineral 矿彩」。

底层入口：

```bash
bash intellij/scripts/build.sh
bash intellij/scripts/install.sh --config-dir "/path/to/IntelliJIdea2026.2"
```

## 加一个新平台（例如 VS Code）

1. 读 `shared/palette.json`（不要读 IntelliJ 的 `.icls`——那是实现细节）；
2. 新建 `<platform>/`，把语义槽位映射到该平台的键（VS Code 的映射表已在 `vscode/README.md` 给出）；
3. 用 `shared/tools/check_palette.py` 做验收 —— 它只按色值判定，与平台无关；
4. `shared/palette.json` **由 `make build` 自动重导**，不要手改；只改 `intellij/src/palette.py`。
