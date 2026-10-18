# Changelog

## [1.2.1] - 2026-10-19

### Fixed

- Javadoc `@param` / `@return` 下划线丢失：为 `DEFAULT_DOC_COMMENT_TAG` 显式设置 `EFFECT_COLOR`。
- diff 修改行被 `FOREGROUND` 铺成浅蓝、白字不可读：`DIFF_*` 只保留背景，不再写前景。
- diff/变更竖条对比过低：修改行背景提到 2.0×，新增/删除行与竖条同步提亮。

### Changed

- `doctor` 在已安装旧版插件时明确报告版本，并提示退出 IDEA 后运行 install。
- `doctor` 读取 `idea.log`，确认最近一次 IDE 启动实际加载的 Green Eye 版本。
- `manual --quick`：8 项高信号检查；新增 `u`（不确定）状态，不再强迫对细微差异下结论。
- `samples/manual-check/`：可直接用 IntelliJ 打开的真机检查样例项目。

## [1.2.0] - 2026-10-18

### Added

- 项目以 MIT 许可证发布（`LICENSE`）。

- 跨平台入口 `green_eye.py`：`build` / `check` / `palette` / `vscode` / `test` /
  `preview` / `install` / `package` / `clean`，支持 `uv run` 自动准备 Python + Pillow。
- VS Code 实现：`green_eye.py vscode` 生成两套主题并打 `.vsix`，
  纯 Python 标准库实现，不需要 Node / vsce。
- `vscode/.vscodeignore`：官方 `vsce` 打包时只保留主题与 manifest。
- VS Code 构建增加产物新鲜度断言；存在 `LICENSE` 时自动收进 VSIX。
- 纯 Python 安装器（`intellij/src/install.py`），macOS / Linux / Windows 原生可用，
  不再依赖 bash / unzip / grep / cmp / awk / shasum。
- `release/green-eye-<version>.zip` 发布包，目标电脑无需任何运行时。
- `green_eye.py package --all`：把 IntelliJ jar/icls 与 VS Code .vsix 合成一个发布包。
- 预览字体的跨平台解析：环境变量 + 各平台候选路径 + 安全回退。
- GitHub Actions 三平台矩阵（macOS / Ubuntu / Windows），构建、测试并上传发布包。
- `v*` tag 触发的 GitHub Release workflow，自动附上 IntelliJ 包与 VS Code `.vsix`。
- CI 增加 `doctor --json` 诊断存档，并随构建产物上传。
- 安装器边界加固：UTF-8 BOM、IDEA 占用时的友好错误、版本号排序、写入后回读校验。
- 色彩数学单元测试：已知 WCAG/CIEDE2000 值 + shared/intellij 全量一致性。
- 色觉缺陷（CVD）报告：`green_eye.py cvd` 生成 `build/ref/cvd-report.md`，
  逐对列出正常色觉可分、红/绿色盲下塌陷的 token。
- `green_eye.py cvd --preview`：生成 normal / protanopia / deuteranopia 对比色板。
- `green_eye.py cvd-variants`：A+「CVD Improved」改善版（松林 18→13、矿彩 20→14 对塌陷），含 .icls、VSIX 与变体包；不是 CVD 安全版。
- `green_eye.py doctor`：预检 palette / jar / .icls / VSIX / 字体 / IntelliJ 安装状态。
- `green_eye.py bump X.Y.Z`：统一更新 project_config.py 与 VS Code package.json。
- `green_eye.py release X.Y.Z`：发布前全流程（bump/build/vscode/cvd/package/test），不自动 tag。
- `green_eye.py manual`：逐项运行真机走查清单并生成报告。
- `doctor` 增加 LICENSE、最近一次 manual 报告检查，并支持 `--json`。
- `green_eye.py report`：汇总 doctor、验收、CVD、真机走查与产物到 `build/ref/report.md`。
- `manual` 有失败项时返回非零退出码，便于脚本/CI 捕获。
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
