# Changelog

## Unreleased

### Added

- 跨平台入口 `green_eye.py`：`build` / `check` / `palette` / `vscode` / `test` /
  `preview` / `install` / `package` / `clean`，支持 `uv run` 自动准备 Python + Pillow。
- VS Code 实现：`green_eye.py vscode` 生成两套主题并打 `.vsix`，
  纯 Python 标准库实现，不需要 Node / vsce。
- 纯 Python 安装器（`intellij/src/install.py`），macOS / Linux / Windows 原生可用，
  不再依赖 bash / unzip / grep / cmp / awk / shasum。
- `release/green-eye-<version>.zip` 发布包，目标电脑无需任何运行时。
- 预览字体的跨平台解析：环境变量 + 各平台候选路径 + 安全回退。
- GitHub Actions 三平台矩阵（macOS / Ubuntu / Windows），构建、测试并上传发布包。
- 安装器边界加固：UTF-8 BOM、IDEA 占用时的友好错误、版本号排序、写入后回读校验。
- 色彩数学单元测试：已知 WCAG/CIEDE2000 值 + shared/intellij 全量一致性。
- 色觉缺陷（CVD）报告：`green_eye.py cvd` 生成 `build/ref/cvd-report.md`，
  逐对列出正常色觉可分、红/绿色盲下塌陷的 token。
- `green_eye.py doctor`：预检 palette / jar / .icls / VSIX / 字体 / IntelliJ 安装状态。
- `docs/cvd-variants.md`：记录 CVD 自动求解原型的局限与三种变体设计方案。

### Changed

- `make` 与 `intellij/scripts/*.sh` 改为薄封装，逻辑集中在 Python。
- README 的矿彩说明、状态色口径、字体说明与自动生成表对齐。
- 文档生成器统一以 LF 写回 README，避免 Windows 上 CRLF 假 diff。

### Removed

- 已删除的浅色主题遗留代码（`render_preview.py` 的 light 对比分支）。
- `palette.py` 顶部会漂移的手写 hex 对照表，改为指向自动生成的 README。

## 1.1.0

- 两款深色主题：「松林」Green Eye Dark 与「矿彩」Green Eye Mineral，
  共用底色 `#1F3027`。
- IntelliJ 插件：475 个语法属性键、157 个界面色、330 个 UI color token、
  68 个控件组。
- 29 项自动验收：对比度、状态色撞色、前景 token 可分、主题身份、反向调色板、
  渲染样式、官方逐键对账、调色板消费、产物新鲜度等。
- 安装器幂等、原子替换、跨 macOS / Linux / Windows Git Bash。

## 1.0.1

### Fixed

- 启动报 `PluginException: InvalidDataException: Light`：
  - 主题 JSON 改用方案名引用 `editorScheme`；
  - `parent_scheme` 改为官方深色同款 `Darcula`；
  - 用 `<bundledColorScheme>` 显式注册两款方案。

## 1.0.0

- 首个版本：两款绿色主题、`.icls` 与 `.theme.json` 生成、插件打包。
