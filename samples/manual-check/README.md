# Green Eye 真机检查样例

用 IntelliJ 打开这个目录（或 `pom.xml`）。主代码可以直接看；
`src/test/java` 下的 JUnit 测试需要先让 Maven 同步依赖（首次会下载 JUnit）。

## 1. 编辑器总览

打开 `snippets/BrokenSnippet.java`，截红色波浪线；

再打开 `src/main/java/ManualCheck.java`，截：

- `unused` 的黄色警告；
- `sum` 的 Javadoc `@param` / `@return` 下划线；
- `@Override` 与 `@Deprecated` 的颜色/删除线；
- `// TODO` 的颜色。

> `BrokenSnippet.java` 放在 Maven 源码目录之外，故意编译错误但不阻塞测试。

## 2. 调试暂停

打开 `src/main/java/DebugCheck.java`，在 `total += i;` 打断点，
点 Debug（`Shift+F9`），截暂停时的全窗口：断点行、当前执行行、变量/调用栈。

如果 `combine(1, 2)` 前没有 `left:` / `right:` 参数名提示，
在 `Settings → Editor → Inlay Hints → Java → Parameter names` 打开。

## 3. 测试运行器

打开 `src/test/java/DebugCheckTest.java`：

- `passes`：绿色；
- `intentionallyFails`：红色（**故意失败**）；
- `disabled`：灰色。

点测试方法左侧的绿色箭头运行整个类，截测试树/失败信息/颜色。

## 4. Git diff

把 `ManualCheck.java` 里的 `return "ManualCheck";` 临时改成
`return "ManualCheck v2";`，在 Git 面板打开 diff，
截新增/删除/修改三种颜色。

> 不要提交这次临时改动。

## 可选：主题下拉

`Settings → Appearance & Behavior → Appearance → Theme`，
截两款主题都在的下拉框。

## 看不出来怎么办

如果某项不确定，直接说“不确定”，不用勉强判断。
