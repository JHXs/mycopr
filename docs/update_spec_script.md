这份文档专门解释 `scripts/update_spec.py` 这个脚本里最核心的几个部分：

- `update_spec(config, data)`
- `main()`

它的职责和 `is_update_needed()` 不一样。

你可以这样理解：

- `is_update_needed()` 负责判断：要不要更新
- `update_spec.py` 负责执行：真的去改 `.spec` 文件

如果说 `is_update_needed()` 是“侦察兵”，那 `update_spec.py` 就是“施工队”。

---

## 1. 这个脚本整体要做什么

这个脚本的使命可以概括成一句话：

> 根据上游最新数据，修改本地 `.spec` 文件中的关键字段，并把结果输出给 GitHub Actions。

它主要做 3 件事：

1. 更新 `%global` 宏
2. 必要时自动往 `%changelog` 里插入一条记录
3. 对 release 型包把 `Release:` 重置回 `1%{?dist}`

---

## 2. 先看输入长什么样

这个脚本主要接收两类输入：

### `config`

来自 `packages/packages.toml`。

例如：

```python
config = {
    "type": "github_release",
    "spec": "packages/obsidian/obsidian.spec",
    "copr_repos": ["ikunji/mycopr", "ikunji/obsidian"]
}
```

或者 commit 型包：

```python
config = {
    "type": "github_commit",
    "spec": "packages/krunner-pinyin-search/krunner-pinyin-search.spec",
    "transforms": {
        "git_commit": "raw",
        "git_short": "raw",
        "commit_date": "raw"
    },
    "update_changelog": True
}
```

### `data`

来自上游 API 查询结果。

release 型包：

```python
data = {
    "version": "v1.12.7"
}
```

commit 型包：

```python
data = {
    "sha": "abcdef1234567890",
    "short": "abcdef1",
    "date": "20260420",
    "msg": "fix: improve candidate matching"
}
```

---

## 3. 先看 `update_spec(config, data)` 的整体结构

这个函数的骨架是：

```python
def update_spec(config, data):
    spec_path = resolve_repo_path(config["spec"])
    content = spec_path.read_text()
    new_content = content

    # 1. 更新 %global 宏
    ...

    # 2. 追加 changelog
    ...

    # 3. 重置 Release
    ...

    if new_content != content:
        spec_path.write_text(new_content)
        return True
    return False
```

这说明它的工作流程是：

1. 读原文件
2. 在内存里生成一个修改后的版本
3. 如果内容真的变了，就写回去
4. 告诉外部“这次有没有实际修改”

---

## 4. 第一步：找到 `.spec` 文件

```python
spec_path = resolve_repo_path(config["spec"])
```

例如：

```python
config["spec"] == "packages/obsidian/obsidian.spec"
```

会被转换成仓库里的绝对路径。

作用是：

- 不依赖当前工作目录
- 无论脚本从哪里运行，都能找到同一个 spec 文件

---

## 5. 第二步：读原始内容，并准备一个“可修改副本”

```python
content = spec_path.read_text()
new_content = content
```

这里有两个变量：

- `content`：原始文件内容
- `new_content`：准备修改的内容

这样做的好处是：

- 可以保留原始内容做对比
- 最后可以判断“到底有没有发生实际修改”

你可以把它理解成：

- `content` 是原稿
- `new_content` 是你拿来修改的草稿

---

## 6. 第三步：更新 `%global` 宏

这是函数里最核心的一部分。

代码大意是：

```python
default_transforms = {"package_version": "strip_v"}
if config["type"] == "github_commit":
    default_transforms = {"commit": "raw"}

transforms = config.get("transforms", default_transforms)
for var_name, rule in transforms.items():
    ...
    new_content = re.sub(..., new_content)
```

### 这一步的目标

把 `.spec` 里类似这些内容：

```spec
%global package_version 1.12.6
```

替换成：

```spec
%global package_version 1.12.7
```

---

## 7. 默认转换规则是怎么来的

```python
default_transforms = {"package_version": "strip_v"}
if config["type"] == "github_commit":
    default_transforms = {"commit": "raw"}
```

意思是：

- 普通 release 包，默认更新 `%global package_version`
- commit 型包，默认更新 `%global commit`

如果配置里显式写了 `transforms`，就用配置里的。

例如：

```toml
transforms = { git_commit = "raw", git_short = "raw", commit_date = "raw" }
```

那脚本就不会再用默认值，而是按这 3 个宏去更新。

---

## 8. 这一步怎么决定“该写什么值”

循环里这段逻辑：

```python
val = data.get(var_name)
if val is None:
    if "short" in var_name: val = data.get("short")
    elif "date" in var_name: val = data.get("date")
    elif "commit" in var_name or "sha" in var_name: val = data.get("sha")
    else: val = data.get("version") or data.get("sha")
```

它和 `common.py` 里的 `pick_upstream_value()` 是同一类思路：

> 先试同名字段，找不到再根据宏名猜最合理的上游字段。

### 举例 1：普通 release 包

假设：

```python
var_name = "package_version"
data = {"version": "v1.12.7"}
```

执行过程：

1. `data.get("package_version")` 拿不到
2. 宏名里不含 `short`
3. 不含 `date`
4. 不含 `commit` 或 `sha`
5. 最后退回 `data.get("version")`

得到：

```python
val == "v1.12.7"
```

### 举例 2：commit 包

假设：

```python
var_name = "git_short"
data = {"short": "abcdef1"}
```

执行过程：

1. `data.get("git_short")` 可能拿不到
2. 因为名字里有 `short`
3. 所以取 `data["short"]`

得到：

```python
val == "abcdef1"
```

---

## 9. 上游值为什么还要再做转换

```python
val = apply_transform(val, rule)
```

原因是：

> 上游返回的值，不一定和 spec 里最终写法一致。

例如：

- 上游是 `v1.12.7`
- spec 里想写 `1.12.7`

那就需要：

```python
apply_transform("v1.12.7", "strip_v")
```

结果变成：

```python
"1.12.7"
```

再比如：

- 上游是 `GE-Proton8-25`
- 规则是 `strip_v, strip:GE-Proton, dot`

结果会变成：

```python
"8.25"
```

---

## 10. `re.sub(...)` 这一行到底做了什么

```python
new_content = re.sub(
    rf'(%global\s+{var_name}\s+)\S+',
    rf'\g<1>{val}',
    new_content
)
```

这是整个“改文件”动作里最关键的一行。

### 它想匹配什么

比如：

- `var_name = "package_version"`

它会匹配这种行：

```spec
%global package_version 1.12.6
```

正则拆开看：

```python
(%global\s+{var_name}\s+)\S+
```

含义是：

- `(%global\s+{var_name}\s+)`
  把前半部分 `%global package_version ` 捕获下来
- `\S+`
  匹配后面的旧值，例如 `1.12.6`

### 它替换成什么

```python
rf'\g<1>{val}'
```

意思是：

- 保留前半部分 `%global package_version `
- 把后半部分旧值替换成新值

例如：

原来：

```spec
%global package_version 1.12.6
```

替换后：

```spec
%global package_version 1.12.7
```

### 一句话总结

这行代码不是“重写整行”，而是：

> 保留 `%global 宏名` 不动，只替换后面的值。

---

## 11. 第四步：自动追加 `%changelog`

这一部分代码是：

```python
if config.get("update_changelog") and "%changelog" in new_content:
    short_sha = data.get("short")
    if short_sha and short_sha not in content:
        date_str = datetime.now().strftime("%a %b %d %Y")
        commit_date = data.get("date", "")
        commit_msg = data.get("msg", "Auto-update")
        entry = f"..."
        new_content = new_content.replace("%changelog\n", f"%changelog\n{entry}")
```

### 什么时候会触发

必须同时满足两个条件：

1. 配置里启用了：

   ```python
   config.get("update_changelog")
   ```

2. spec 文件里真的有 `%changelog`

   ```python
   "%changelog" in new_content
   ```

### 为什么主要给 commit 包用

因为 commit 型包通常会频繁变化，给它自动追加 changelog 很合适。  
release 型包往往只更新版本号，不一定要自动写 changelog。

### `short_sha` 这一步在干什么

```python
short_sha = data.get("short")
if short_sha and short_sha not in content:
```

作用是避免重复追加同一条记录。

如果本地内容里已经出现过这个 `short`，那就认为这次 changelog 已经写过了，不再重复插入。

### `date_str`

```python
date_str = datetime.now().strftime("%a %b %d %Y")
```

生成的是 changelog 头部的人类可读日期，例如：

```text
Mon Apr 20 2026
```

### `commit_date`

```python
commit_date = data.get("date", "")
```

取的是上游 commit 日期，例如：

```text
20260420
```

### `commit_msg`

```python
commit_msg = data.get("msg", "Auto-update")
```

取的是提交消息标题，如果没有就退回默认值。

### `entry`

拼出完整 changelog 条目，例如：

```text
* Mon Apr 20 2026 GitHub Actions <actions@github.com> - 20260420gitabcdef1
- Auto-update to commit abcdef1: fix: improve candidate matching
```

### 最后怎么插入

```python
new_content = new_content.replace("%changelog\n", f"%changelog\n{entry}")
```

意思是：

- 找到 `%changelog`
- 把新条目插到它后面

这样新记录就会出现在 changelog 最顶部。

---

## 12. 第五步：统一重置 `Release`

代码：

```python
if config.get("reset_release", True) and "commit" not in config["type"]:
    new_content = re.sub(r'(Release:\s+)\S+', r'\g<1>1%{?dist}', new_content)
```

### 这一步在解决什么问题

很多 release 型包升级到新上游版本后，希望：

```spec
Release: 1%{?dist}
```

重新从 `1` 开始。

例如：

原来：

```spec
Version: 1.12.6
Release: 3%{?dist}
```

升级到新版本后，希望变成：

```spec
Version: 1.12.7
Release: 1%{?dist}
```

### 为什么 commit 包通常不做这一步

因为 commit 型包本身就是在追踪“滚动变化”，它们往往不按普通 release 的节奏重置 `Release`。

所以这里特意加了：

```python
"commit" not in config["type"]
```

### `re.sub(...)` 做了什么

它会把：

```spec
Release: 5%{?dist}
```

改成：

```spec
Release: 1%{?dist}
```

---

## 13. 第六步：只有真的有变化才写回文件

```python
if new_content != content:
    spec_path.write_text(new_content)
    return True
return False
```

这段非常重要。

它的意思是：

- 如果修改后的内容和原内容不同
  - 真的写回文件
  - 返回 `True`
- 如果完全一样
  - 什么都不写
  - 返回 `False`

### 为什么这很重要

这样可以避免：

- 每次运行都改文件时间戳
- Git 里出现没必要的改动
- GitHub Actions 误以为有更新

---

## 14. 例子一：`obsidian` 这种 release 包

假设：

```python
config = {
    "type": "github_release",
    "spec": "packages/obsidian/obsidian.spec",
    "copr_repos": ["ikunji/mycopr", "ikunji/obsidian"]
}
```

上游：

```python
data = {
    "version": "v1.12.8"
}
```

本地 spec 原来是：

```spec
%global package_version 1.12.7
Release:        3%{?dist}
```

执行结果：

1. 默认规则是：
   ```python
   {"package_version": "strip_v"}
   ```
2. 取到上游值 `v1.12.8`
3. 转换成 `1.12.8`
4. 把：
   ```spec
   %global package_version 1.12.7
   ```
   改成：
   ```spec
   %global package_version 1.12.8
   ```
5. 因为是 release 包，重置：
   ```spec
   Release: 1%{?dist}
   ```
6. 如果内容变了，就写回文件并返回 `True`

---

## 15. 例子二：commit 包并自动写 changelog

假设：

```python
config = {
    "type": "github_commit",
    "spec": "packages/krunner-pinyin-search/krunner-pinyin-search.spec",
    "transforms": {
        "git_commit": "raw",
        "git_short": "raw",
        "commit_date": "raw"
    },
    "update_changelog": True
}
```

上游：

```python
data = {
    "sha": "abcdef1234567890",
    "short": "abcdef1",
    "date": "20260420",
    "msg": "fix: improve candidate matching"
}
```

本地 spec 原来是：

```spec
%global git_commit 1111111111111111
%global git_short 1111111
%global commit_date 20260418

%changelog
* Old entry
```

执行结果：

1. 更新 `%global git_commit`
2. 更新 `%global git_short`
3. 更新 `%global commit_date`
4. 因为启用了 `update_changelog`，并且旧内容里还没有 `abcdef1`
5. 自动插入一条新的 changelog 记录
6. 不会去重置 `Release`，因为这是 commit 包
7. 写回文件并返回 `True`

---

## 16. `main()` 做什么

`main()` 是命令行入口。

代码结构是：

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pkg", required=True)
    parser.add_argument("--upstream-data", required=True)
    args = parser.parse_args()

    data = json.loads(args.upstream_data)
    config = load_packages()[args.pkg]

    ...
    updated = update_spec(config, data)
    ...
    print(...)
```

### 它做的事情可以分成 4 步

1. 读取命令行参数
2. 把 JSON 字符串解析成 Python 字典
3. 从 `packages/packages.toml` 里拿到对应包配置
4. 调用 `update_spec()`，并把结果打印给 GitHub Actions

---

## 17. `argparse` 这一段是什么意思

```python
parser = argparse.ArgumentParser()
parser.add_argument("--pkg", required=True)
parser.add_argument("--upstream-data", required=True)
args = parser.parse_args()
```

这个脚本要求你调用时必须传两个参数：

### `--pkg`

包名，例如：

```bash
--pkg obsidian
```

### `--upstream-data`

上游数据的 JSON 字符串，例如：

```bash
--upstream-data '{"version":"v1.12.7"}'
```

---

## 18. 为什么要 `json.loads(...)`

```python
data = json.loads(args.upstream_data)
```

因为命令行参数进来时都是字符串。

例如：

```bash
'{"version":"v1.12.7"}'
```

在 Python 里只是普通文本，不能直接当字典用。

所以要先解析成真正的 Python 字典：

```python
{"version": "v1.12.7"}
```

---

## 19. `config = load_packages()[args.pkg]` 是什么意思

```python
config = load_packages()[args.pkg]
```

它的意思是：

1. 从 `packages/packages.toml` 里读取全部包配置
2. 按包名取出当前这个包的配置

例如：

```bash
--pkg obsidian
```

就相当于：

```python
config = load_packages()["obsidian"]
```

---

## 20. 打印 stderr 信息是为了什么

```python
print(f"📝 Updating {args.pkg} spec file...", file=sys.stderr)
```

以及：

```python
print(f"  ✨ Successfully updated to ...", file=sys.stderr)
print(f"  ℹ️ No changes needed for spec file", file=sys.stderr)
```

这些输出主要是给人看的日志。

也就是：

- 终端里好读
- GitHub Actions 日志里也好读

它们不作为机器解析结果使用。

---

## 21. 最后这几行为什么要 `print(...)`

```python
print(f"updated={'true' if updated else 'false'}")
print(f"version={data.get('version') or data.get('short') or 'updated'}")
print(f"copr_repos={','.join(config['copr_repos'])}")
print(f"spec_file={config['spec']}")
```

这几行是给 GitHub Actions 或其他自动化流程读的。

### `updated=...`

告诉外部：

- 这次有没有改动 spec

### `version=...`

告诉外部：

- 这次更新到哪个版本
- 如果没有 `version`，就退回 `short`

### `copr_repos=...`

把目标 Copr 仓库列表拼成逗号分隔字符串，例如：

```text
ikunji/mycopr,ikunji/obsidian
```

### `spec_file=...`

告诉外部当前处理的是哪个 spec 文件。

---

## 22. 一次完整命令示例

例如你在本地运行：

```bash
uv run scripts/update_spec.py \
  --pkg obsidian \
  --upstream-data '{"version":"v1.12.8"}'
```

执行过程是：

1. 解析参数
2. 得到：
   ```python
   args.pkg == "obsidian"
   args.upstream_data == '{"version":"v1.12.8"}'
   ```
3. `json.loads(...)` 后得到：
   ```python
   {"version": "v1.12.8"}
   ```
4. 从 `packages/packages.toml` 取出 `obsidian` 配置
5. 调用 `update_spec(config, data)`
6. 如果 spec 真改了，终端会打印：
   ```text
   📝 Updating obsidian spec file...
     ✨ Successfully updated to v1.12.8
   ```
7. 标准输出还会额外打印：
   ```text
   updated=true
   version=v1.12.8
   copr_repos=ikunji/mycopr,ikunji/obsidian
   spec_file=packages/obsidian/obsidian.spec
   ```

---

## 23. 一句话总结

如果你以后只记一句话，记这个就够了：

> `update_spec.py` 会把上游数据转换成 spec 应有的格式，替换 `%global` 宏，必要时补 changelog，最后把结果输出给自动化流程。

再压缩一点：

> `is_update_needed()` 负责判断，`update_spec.py` 负责动手修改。
