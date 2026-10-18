# 第三方材料说明

## 本项目自身代码

以 **MIT** 许可证发布，完整文本见 [`LICENSE`](LICENSE)。

下面列出的是仓库内用于对照/校验的**第三方材料**；它们不包含在发布包中，
也不改变本项目自身代码的 MIT 许可。

本仓库的发布包（`release/*.zip`）只包含本项目生成的插件 jar 与 `.icls` 配色方案，
**不包含**下面这些第三方材料。它们仅用于本地对照 / 兼容性校验，放在
`intellij/build/ref/` 下，不随发布包分发。

## Everforest for JetBrains

- 来源：<https://github.com/francma/everforest-jetbrains>
- 许可证：ISC
- 版权：Copyright (c) 2021, Martin Franc
- 本仓库位置：`intellij/build/ref/everforest/`
- 用途：参考主题对照

```text
ISC License

Copyright (c) 2021, Martin Franc

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
```

## GitHub theme for JetBrains

- 来源：<https://github.com/sergeymakinen/jetbrains-github-theme>
- 许可证：MIT
- 版权：Copyright (c) 2016 Sergey Makinen
- 本仓库位置：`intellij/build/ref/github/GitHub 3.icls`
- 用途：参考主题对照

```text
The MIT License (MIT)

Copyright (c) 2016 Sergey Makinen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## JetBrains 官方主题与配色方案

- 来源：本地安装的 IntelliJ IDEA 2026.2.3（IU-262.10968.63）内置资源
- 版权：JetBrains s.r.o.
- 本仓库位置：`intellij/build/ref/ide_official_schemes/`、
  `intellij/build/ref/ide2026/themes/`、`intellij/build/ref/Darcula.xml`、
  `intellij/build/ref/*_names.txt`
- 用途：只做属性键、装饰编码与父方案行为的本地对照；不随发布包分发。
- 说明：这些文件的使用受 JetBrains 许可约束；本项目不主张对它们的任何权利。

## 字体

预览渲染使用操作系统自带字体（Menlo / Hiragino Sans GB / DejaVu Sans Mono /
Consolas / Microsoft YaHei 等），字体文件不随仓库或发布包分发。
