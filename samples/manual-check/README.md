# Green Eye 真机检查样例

用 IntelliJ 打开这个目录（或 `pom.xml`），然后按下面截 3 张图。
不需要运行 Maven，也不需要改任何主题设置。

## 1. 编辑器总览

打开 `src/main/java/ManualCheck.java`，截 IDE 全窗口，包含：

- `broken` 的红色波浪线；
- `unused` 的黄色警告；
- `sum` 的 Javadoc `@param` / `@return` 下划线；
- `@Override` 与 `@Deprecated` 的颜色/删除线；
- `// TODO` 的颜色。

## 2. 调试暂停

`ManualCheck.java` 故意有一行编译错误，不能直接运行。请打开
`src/main/java/DebugCheck.java`，在 `total += i;` 打断点，点 Debug（`Shift+F9`），
截暂停时的全窗口：断点行、当前执行行、变量/调用栈。
如果 `combine(1, 2)` 前没有 `left:` / `right:` 参数名提示，
在 `Settings → Editor → Inlay Hints → Java → Parameter names` 打开。

## 3. Git diff

把 `return "ManualCheck";` 临时改成 `return "ManualCheck v2";`，
在 Git 面板打开 diff，截新增/删除/修改三种颜色。

> 这个样例在父仓库里，IntelliJ 会识别父级 `.git`；不要提交这次临时改动。

## 可选：主题下拉

`Settings → Appearance & Behavior → Appearance → Theme`，
截两款主题都在的下拉框。

## 看不出来怎么办

如果某项不确定，直接说“不确定”，不用勉强判断；这三张图已经覆盖
最容易出问题的渲染点。
