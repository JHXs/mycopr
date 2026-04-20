这份文档专门解释 `scripts/common.py` 里这 3 个函数：

- `get_default_transforms(config)`
- `pick_upstream_value(data, var_name)`
- `is_update_needed(config, data)`

它们是“判断一个包要不要更新”的核心辅助逻辑。

你可以把它们理解成 3 个角色：

- `get_default_transforms`：先决定“默认该检查哪个 `%global` 宏”
- `pick_upstream_value`：再决定“这个宏应该从上游数据里拿哪个值”
- `is_update_needed`：最后把“期望值”和本地 `.spec` 做比对

---

## 1. 整体目标

脚本并不是在问：

> “这个 `.spec` 文件有没有任何变化？”

它真正问的是：

> “这个 `.spec` 文件里，关键 `%global` 宏的值，是否已经和上游最新版本一致？”

例如：

```spec
%global package_version 1.12.7
```

如果上游最新版本也是 `1.12.7`，那就说明这个包不需要更新。  
如果上游已经变成 `1.12.8`，那就需要更新。

---

## 2. 先看输入长什么样

这 3 个函数处理的主要是两类数据。

### `config`

它来自 `packages/packages.toml`，描述“这个包应该怎么更新”。

例如 `obsidian` 这种 release 型包，大致是：

```python
config = {
    "type": "github_release",
    "repo": "obsidianmd/obsidian-releases",
    "spec": "packages/obsidian/obsidian.spec",
    "copr_repos": ["ikunji/mycopr", "ikunji/obsidian"]
}
```

再比如 `krunner-pinyin-search` 这种 commit 型包：

```python
config = {
    "type": "github_commit",
    "repo": "AOSC-Dev/krunner-pinyin-search",
    "spec": "packages/krunner-pinyin-search/krunner-pinyin-search.spec",
    "transforms": {
        "git_commit": "raw",
        "git_short": "raw",
        "commit_date": "raw"
    }
}
```

### `data`

它来自上游 API，是“当前最新版本信息”。

对于 release 型包，通常像这样：

```python
data = {
    "version": "v1.12.7"
}
```

对于 commit 型包，通常像这样：

```python
data = {
    "sha": "abcdef1234567890",
    "git_commit": "abcdef1234567890",
    "short": "abcdef1",
    "git_short": "abcdef1",
    "date": "20260420",
    "commit_date": "20260420",
    "msg": "fix: improve candidate matching"
}
```

---

## 3. `get_default_transforms(config)` 做什么

函数代码的意思很简单：

```python
def get_default_transforms(config):
    if config["type"] == "github_commit":
        return {"commit": "raw"}
    return {"package_version": "strip_v"}
```

### 作用

如果 `packages/packages.toml` 没有显式写 `transforms`，它就提供一套默认规则。

### 为什么需要默认规则

不是每个包都会在配置里明确写：

```toml
transforms = { package_version = "strip_v" }
```

很多包其实遵循固定约定：

- 普通 release 包：通常更新 `%global package_version`
- commit 包：通常更新 `%global commit`

所以可以给默认值，省得每个包都写一遍。

### 两种默认情况

#### 情况 A：普通 release 包

返回：

```python
{"package_version": "strip_v"}
```

意思是：

- 目标宏名是 `package_version`
- 上游值要先做 `strip_v`

例如：

- 上游给：`v1.12.7`
- 转换后：`1.12.7`

#### 情况 B：commit 包

返回：

```python
{"commit": "raw"}
```

意思是：

- 目标宏名是 `commit`
- 值不做处理，原样使用

---

## 4. `pick_upstream_value(data, var_name)` 做什么

这个函数的任务是：

> 给定一个“spec 里的宏名”，推断应该从 `data` 里的哪个字段取值。

代码逻辑可以翻译成一句话：

> “先试直接同名取值；如果没有，就根据宏名猜最合理的字段。”

### 第一层：直接同名取值

```python
value = data.get(var_name)
if value is not None:
    return value
```

例如：

- `var_name = "git_commit"`
- `data` 里刚好有 `git_commit`

那就直接返回。

这是最稳妥的情况，因为完全不用猜。

---

### 第二层：按名字特征兜底

如果没有同名字段，就开始根据宏名猜。

#### 1. 宏名里带 `short`

```python
if "short" in var_name:
    return data.get("short")
```

例如：

- `var_name = "git_short"`
- 虽然 `data.get("git_short")` 可能没有
- 但可以合理推断它应该取 `data["short"]`

#### 2. 宏名里带 `date`

```python
if "date" in var_name:
    return data.get("date")
```

例如：

- `var_name = "commit_date"`
- 就去取 `data["date"]`

#### 3. 宏名里带 `commit` 或 `sha`

```python
if "commit" in var_name or "sha" in var_name:
    return data.get("sha")
```

例如：

- `var_name = "commit"`
- `var_name = "git_commit"`
- `var_name = "source_sha"`

都优先取完整 `sha`

#### 4. 最后兜底：优先 `version`，其次 `sha`

```python
return data.get("version") or data.get("sha")
```

这是最常见的 release 包场景。

例如：

- `var_name = "package_version"`
- 它既不带 `short`，也不带 `date`，也不带 `sha`
- 那就大概率应该取 `version`

---

## 5. `is_update_needed(config, data)` 做什么

这是主函数，它把前两个辅助函数串起来。

它的任务可以拆成 5 步：

1. 找到 `.spec` 文件
2. 读出文件内容
3. 决定要检查哪些宏
4. 算出这些宏“应该是什么值”
5. 检查 `.spec` 里是否已经有这些值

---

## 6. 逐步执行流程

### 第一步：定位 spec 文件

```python
spec_path = resolve_repo_path(config["spec"])
```

例如：

```python
config["spec"] == "packages/obsidian/obsidian.spec"
```

会变成仓库里的完整路径。

这样无论脚本从哪个目录运行，都能找到同一个文件。

---

### 第二步：如果 spec 不存在，直接判定需要更新

```python
if not spec_path.exists():
    return True
```

这个很好理解：

- 文件都不存在
- 那就不可能已经是“最新状态”

所以直接返回 `True`

---

### 第三步：读整个 spec 内容

```python
content = spec_path.read_text()
```

后面会在这个字符串里搜索类似：

```spec
%global package_version 1.12.7
```

---

### 第四步：拿到转换规则

```python
transforms = config.get("transforms", get_default_transforms(config))
```

意思是：

- 如果配置里有显式 `transforms`，优先用配置里的
- 没有的话，就用默认规则

例如：

#### 普通 release 包

得到：

```python
{"package_version": "strip_v"}
```

#### commit 包自定义了 3 个宏

得到：

```python
{
    "git_commit": "raw",
    "git_short": "raw",
    "commit_date": "raw"
}
```

---

### 第五步：逐个检查每个宏

```python
for var_name, rule in transforms.items():
```

如果 `transforms` 是：

```python
{"package_version": "strip_v"}
```

那就只循环一次。

如果是：

```python
{
    "git_commit": "raw",
    "git_short": "raw",
    "commit_date": "raw"
}
```

那就循环三次。

---

### 第六步：决定这个宏应该用上游哪个值

```python
upstream_value = pick_upstream_value(data, var_name)
```

例如：

- `var_name = "package_version"`
- `data = {"version": "v1.12.7"}`

最后会取到：

```python
upstream_value == "v1.12.7"
```

再比如：

- `var_name = "git_short"`
- `data["short"] = "abcdef1"`

最后会取到：

```python
upstream_value == "abcdef1"
```

---

### 第七步：把上游值变成 spec 里应有的格式

```python
expected_value = apply_transform(upstream_value, rule)
```

例如：

- `upstream_value = "v1.12.7"`
- `rule = "strip_v"`

得到：

```python
expected_value == "1.12.7"
```

再比如：

- `upstream_value = "GE-Proton8-25"`
- `rule = "strip_v, strip:GE-Proton, dot"`

得到：

```python
expected_value == "8.25"
```

这一步的重点是：

> 上游值不一定和 spec 里写法一样，所以要先做转换。

---

### 第八步：拼出“期望的 `%global` 宏模式”

```python
pattern = rf'%global\s+{var_name}\s+{re.escape(expected_value)}'
```

如果：

- `var_name = "package_version"`
- `expected_value = "1.12.7"`

那这个正则大致想匹配：

```spec
%global package_version 1.12.7
```

这里用 `\s+` 而不是写死一个空格，是为了更宽容：

- 一个空格也行
- 多个空格也行
- tab 也行

`re.escape(expected_value)` 是为了防止值里有特殊字符时把正则弄坏。

---

### 第九步：检查 spec 里有没有这个宏

```python
if re.search(pattern, content) is None:
    return True
```

如果找不到，就表示：

- 本地 spec 里没有这个“期望宏”
- 说明还没同步到最新值
- 所以返回 `True`

注意，这里是“发现一个不匹配就立刻返回 `True`”。

它不是等所有项都检查完再算分，而是：

> 只要有一个宏没对上，就说明这个包需要更新。

---

### 第十步：全部检查通过，说明不需要更新

```python
return False
```

只有当所有宏都匹配成功，才会走到这里。

这表示：

- spec 里的关键 `%global` 宏
- 已经全部和上游保持一致

所以不需要更新。

---

## 7. 例子一：`obsidian` 这种 release 包

假设：

```python
config = {
    "type": "github_release",
    "spec": "packages/obsidian/obsidian.spec"
}
```

上游返回：

```python
data = {
    "version": "v1.12.7"
}
```

本地 spec 里有：

```spec
%global package_version 1.12.7
```

执行过程：

1. `get_default_transforms(config)` 返回：
   ```python
   {"package_version": "strip_v"}
   ```
2. 检查 `package_version`
3. `pick_upstream_value(data, "package_version")`
   返回 `v1.12.7`
4. `apply_transform("v1.12.7", "strip_v")`
   返回 `1.12.7`
5. 在 spec 里搜索：
   ```spec
   %global package_version 1.12.7
   ```
6. 找到了，于是这个宏通过
7. 没有别的宏要检查
8. 返回 `False`

结论：**不需要更新**

---

## 8. 例子二：commit 包

假设配置里写了：

```python
config = {
    "type": "github_commit",
    "spec": "packages/krunner-pinyin-search/krunner-pinyin-search.spec",
    "transforms": {
        "git_commit": "raw",
        "git_short": "raw",
        "commit_date": "raw"
    }
}
```

上游返回：

```python
data = {
    "sha": "abcdef1234567890",
    "short": "abcdef1",
    "date": "20260420"
}
```

本地 spec 假设是：

```spec
%global git_commit abcdef1234567890
%global git_short abcdef1
%global commit_date 20260420
```

执行过程：

### 第 1 轮：检查 `git_commit`

- `pick_upstream_value(data, "git_commit")`
- 没有同名键
- 宏名里带 `commit`
- 取 `data["sha"]`
- 得到 `abcdef1234567890`

规则是 `raw`，所以值不变。

### 第 2 轮：检查 `git_short`

- 宏名里带 `short`
- 取 `data["short"]`
- 得到 `abcdef1`

### 第 3 轮：检查 `commit_date`

- 宏名里带 `date`
- 取 `data["date"]`
- 得到 `20260420`

三轮都在 spec 里找到了对应 `%global`，所以最终返回：

```python
False
```

结论：**不需要更新**

---

## 9. 什么时候会返回 `True`

这个函数会在下面几种情况返回 `True`：

### 情况 1：spec 文件不存在

```python
if not spec_path.exists():
    return True
```

### 情况 2：某个 `%global` 宏不存在

例如期待：

```spec
%global package_version 1.12.7
```

但 spec 里根本没有这一行。

### 情况 3：宏存在，但值旧了

例如 spec 里是：

```spec
%global package_version 1.12.6
```

上游已经是：

```python
{"version": "v1.12.7"}
```

那就返回 `True`

---

## 10. 一句话总结

这 3 个函数串起来做的事，可以概括成：

> 先决定“应该检查哪些 spec 宏”，  
> 再决定“每个宏应该从上游拿哪个值”，  
> 再把这个值转换成 spec 的写法，  
> 最后检查 spec 里是否已经存在完全一致的 `%global` 定义。

如果你以后只记一句话，记这个就够了：

> `is_update_needed()` 不是比较整个文件，而是在比较关键 `%global` 宏是否已经同步到上游最新值。
