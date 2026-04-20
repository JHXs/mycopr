transforms` 本质上是“把上游拿到的原始值，转换成 spec 里应该写的值”的规则。

它不是在改文件结构，也不是在决定改哪一行；它只回答一个问题：

> 上游给我的值是 `X`，那 `%global 某个宏` 最终应该写成什么？

最关键的入口有两处：

- [packages/packages.toml](/home/hansel/Documents/ITProject/copr/packages/packages.toml:1) 里配置 `transforms`
- [scripts/common.py](/home/hansel/Documents/ITProject/copr/scripts/common.py:23) 里的 `apply_transform()`

先看最小例子：

```toml
[obsidian]
type = "github_release"
spec = "packages/obsidian/obsidian.spec"
```

如果你没写 `transforms`，脚本会走默认规则。  
这个默认规则在 [get_default_transforms()](/home/hansel/Documents/ITProject/copr/scripts/common.py:82) 里决定：

- 普通 release 包默认是：
  ```python
  {"package_version": "strip_v"}
  ```
- `github_commit` 包默认是：
  ```python
  {"commit": "raw"}
  ```

意思分别是：

- 把上游的 `version` 转成 `%global package_version` 要写的值
- 把上游的 commit 原样写进 `%global commit`

---

**一、`transforms` 的结构是什么**

它是一个 TOML 内联表，格式像这样：

```toml
transforms = { package_version = "strip_v, dot" }
```

左边：

- `package_version`

表示“要更新 spec 里的哪个 `%global` 宏”。

右边：

- `"strip_v, dot"`

表示“先后做哪些转换”。

所以这句话的完整含义是：

> 把上游拿到的值，按 `strip_v` 再按 `dot` 处理，最后写到 `%global package_version`。

---

**二、当前支持哪些转换规则**

在 [apply_transform()](/home/hansel/Documents/ITProject/copr/scripts/common.py:23) 里，当前真正支持的只有这几种：

1. `strip_v`
2. `dot`
3. `strip:TEXT`

逐个解释。

1. `strip_v`

```python
elif op == "strip_v": v = v.lstrip('v')
```

作用：

- 去掉字符串开头连续的 `v`

例子：

- `v1.2.3` -> `1.2.3`
- `vv1.2.3` -> `1.2.3`
- `GE-Proton8-25` -> 不变

这个规则最适合 GitHub release 常见的 tag：

- 上游：`v1.12.7`
- spec 想写：`1.12.7`

---

2. `dot`

```python
if op == "dot": v = v.replace('-', '.')
```

作用：

- 把所有 `-` 替换成 `.`

例子：

- `8-25` -> `8.25`
- `1-2-3` -> `1.2.3`

这个规则通常用于上游 tag 用短横线，但 spec 里你想用点号。

---

3. `strip:TEXT`

```python
elif op.startswith("strip:"): v = v.replace(op[6:], "")
```

作用：

- 把指定文本整体删除

例子：

- `strip:GE-Proton`
- `GE-Proton8-25` -> `8-25`

再比如：

- `strip:release-`
- `release-1.2.3` -> `1.2.3`

注意这里不是“只删开头”，而是 `replace()`，所以字符串里所有匹配文本都会被删。

---

**三、`raw` 是怎么回事**

你会在配置里看到：

```toml
transforms = { git_commit = "raw", git_short = "raw", commit_date = "raw" }
```

但 [apply_transform()](/home/hansel/Documents/ITProject/copr/scripts/common.py:23) 里并没有专门处理 `raw`。

这不是 bug，而是当前实现里：

- `raw` 不命中任何 if/elif
- 所以值保持原样不变

也就是说，`raw` 的语义实际上是：

> 什么也不做

例如：

- 上游：`abcdef123456`
- 规则：`raw`
- 结果：`abcdef123456`

---

**四、多个转换是怎么串起来的**

这一行很关键：

```python
for op in transform_str.split(','):
```

说明一条规则字符串里可以写多个操作，用逗号分隔，按顺序执行。

比如：

```toml
transforms = { package_version = "strip_v, strip:GE-Proton, dot" }
```

处理顺序是：

1. `strip_v`
2. `strip:GE-Proton`
3. `dot`

顺序不同，结果可能不同。

拿 `GE-Proton8-25` 来看：

- `strip_v`：不变
- `strip:GE-Proton`：变成 `8-25`
- `dot`：变成 `8.25`

最终结果是：

```text
8.25
```

这正是你在 [packages/packages.toml](/home/hansel/Documents/ITProject/copr/packages/packages.toml:39) 里 `ge-proton` 的用法。

---

**五、`transforms` 到底在哪两个地方被用到**

它在两条链路里都会被用：

1. 判断需不需要更新  
2. 真正修改 spec

对应代码是：

- 判断： [scripts/common.py](/home/hansel/Documents/ITProject/copr/scripts/common.py:107)
- 修改： [scripts/update_spec.py](/home/hansel/Documents/ITProject/copr/scripts/update_spec.py:6)

这点非常重要。

因为如果只在“修改”阶段用 transforms，而“不在判断”阶段用，就会出现：

- 判断说“不需要更新”
- 但真正生成的值其实和 spec 不一致

现在你的仓库设计是统一的：

- `is_update_needed()` 用 transforms 算“期望值”
- `update_spec()` 也用 transforms 算“要写入的值”

所以两边逻辑一致。

---

**六、完整例子 1：`obsidian`**

上游返回：

```python
data = {"version": "v1.12.7"}
```

默认 transforms：

```python
{"package_version": "strip_v"}
```

流程是：

1. 目标宏是 `package_version`
2. 从上游数据里取到 `version`
3. 应用 `strip_v`
4. 得到 `1.12.7`
5. 去检查/写入：
   ```spec
   %global package_version 1.12.7
   ```

所以 `transforms` 在这里干的事就是：

> 把 GitHub 的 tag 写法 `v1.12.7` 变成 spec 的写法 `1.12.7`

---

**七、完整例子 2：`ge-proton`**

配置是：

```toml
transforms = { package_version = "strip_v, strip:GE-Proton, dot", proton_ver = "strip_v, strip:GE-Proton" }
```

假设上游返回：

```python
data = {"version": "GE-Proton8-25"}
```

对于 `package_version`：

1. 原始值：`GE-Proton8-25`
2. `strip_v`：不变
3. `strip:GE-Proton`：`8-25`
4. `dot`：`8.25`

最终写入：

```spec
%global package_version 8.25
```

对于 `proton_ver`：

1. 原始值：`GE-Proton8-25`
2. `strip_v`：不变
3. `strip:GE-Proton`：`8-25`

最终写入：

```spec
%global proton_ver 8-25
```

注意这里同一个上游值，通过不同 transforms，可以生成两个不同宏值。

这就是 `transforms` 最有价值的地方：

> 一个上游字段，可以派生出多个 spec 宏，而且每个宏的格式都可以不同。

---

**八、完整例子 3：commit 包**

配置：

```toml
transforms = { git_commit = "raw", git_short = "raw", commit_date = "raw" }
```

上游返回：

```python
data = {
  "sha": "abcdef1234567890",
  "short": "abcdef1",
  "date": "20260420"
}
```

这里 `transforms` 的作用不是做格式清洗，而是明确告诉脚本：

- 要更新哪些宏：
  - `git_commit`
  - `git_short`
  - `commit_date`
- 这些宏都原样写

所以它更像“字段映射声明”。

---

**九、你最需要记住的 3 个点**

1. `transforms` 左边决定“更新哪个宏”
2. `transforms` 右边决定“值怎么变形”
3. 同一个上游值可以通过不同规则生成多个不同 spec 宏

---

**十、什么时候该写 `transforms`，什么时候不用写**

可以不写的情况：

- 你的包很普通
- 上游返回 `version`
- spec 里用 `%global package_version`
- 只需要去掉前缀 `v`

这时默认规则就够了。

建议显式写 `transforms` 的情况：

- 你不是更新 `package_version`
- 你要同时更新多个 `%global`
- 上游 tag 格式很怪，需要多步清洗
- 你想让规则一眼可读，不依赖默认行为

---

**十一、一句话总结**

`transforms` 不是“修改 spec 的命令”，而是：

> “定义上游值如何映射成 spec 宏值”的一套规则。

如果你愿意，我下一条可以继续把你仓库里现有每个包的 `transforms` 都逐个解释一遍，告诉你它们各自在解决什么问题。
