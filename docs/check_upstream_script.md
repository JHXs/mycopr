这份文档专门解释 `scripts/check_upstream.py` 这个脚本。

它在整个自动化流程里的位置是：

- `check_upstream.py`：先判断“哪些包需要更新”
- `update_spec.py`：再去真的修改 `.spec`
- `copr-update.yml`：最后调度整条流水线并触发 Copr 构建

如果说：

- `fetch_upstream_data()` 是“情报员”
- `is_update_needed()` 是“判断员”

那么 `check_upstream.py` 就是：

> “巡检队长”

它负责把所有包挨个检查一遍，然后整理出一份“待更新名单”。

---

## 1. 这个脚本整体要做什么

这个脚本的目标可以浓缩成一句话：

> 遍历 `packages/packages.toml` 里的所有包，抓取上游最新信息，并输出一个“需要更新的包列表”。

这个列表最终会被 GitHub Actions 拿去做后续事情，比如：

- 批量调用 `update_spec.py`
- 构建 matrix
- 触发 Copr 构建

---

## 2. 先看脚本整体结构

脚本内容很短：

```python
import argparse
import json
import sys
from common import fetch_upstream_data, is_update_needed, load_packages

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force updates for all packages")
    args = parser.parse_args()

    packages = load_packages()

    to_update = []
    for name, cfg in packages.items():
        try:
            data = fetch_upstream_data(cfg)
            if args.force or is_update_needed(cfg, data):
                to_update.append({"name": name, "data": data})
        except Exception as e:
            print(f"Error fetching {name}: {e}", file=sys.stderr)

    print(json.dumps(to_update))

if __name__ == "__main__":
    main()
```

从结构上看，它只做 4 件事：

1. 读取命令行参数
2. 读取全部包配置
3. 遍历每个包并检查是否需要更新
4. 输出 JSON 结果

---

## 3. `import` 这一段在干什么

```python
import argparse
import json
import sys
from common import fetch_upstream_data, is_update_needed, load_packages
```

每一项都有明确用途。

### `argparse`

用来读取命令行参数，例如：

```bash
uv run scripts/check_upstream.py --force
```

### `json`

用来把最终结果编码成 JSON 字符串输出。

因为后面的 GitHub Actions 很适合消费 JSON。

### `sys`

这里主要用来把错误日志写到标准错误输出：

```python
print(..., file=sys.stderr)
```

这样错误信息不会混进 JSON 主输出里。

### `fetch_upstream_data`

负责去上游平台抓最新数据，例如：

- GitHub release
- GitHub commit
- AUR
- Gitea release

### `is_update_needed`

负责判断：

> 抓到的上游数据，是否已经反映在本地 `.spec` 里

### `load_packages`

负责从 `packages/packages.toml` 读取全部包配置。

---

## 4. `main()` 为什么是入口函数

```python
def main():
```

这是这个脚本真正的执行入口。

最后这段：

```python
if __name__ == "__main__":
    main()
```

意思是：

- 如果你是直接运行这个文件
- 就执行 `main()`

这是 Python 脚本很常见的写法。

---

## 5. 第一步：解析命令行参数

```python
parser = argparse.ArgumentParser()
parser.add_argument("--force", action="store_true", help="Force updates for all packages")
args = parser.parse_args()
```

这里定义了一个可选参数：

```bash
--force
```

### 它的作用

如果加了 `--force`，脚本会把所有包都当成“需要更新”。

也就是说，即使某个包其实已经是最新的，也会被加入输出列表。

### `action="store_true"` 是什么意思

它表示这个参数是一个布尔开关：

- 写了 `--force`，值就是 `True`
- 不写，值就是 `False`

所以：

```python
args.force
```

最终只会是：

- `True`
- `False`

### 举例

#### 不带参数

```bash
uv run scripts/check_upstream.py
```

此时：

```python
args.force == False
```

#### 带 `--force`

```bash
uv run scripts/check_upstream.py --force
```

此时：

```python
args.force == True
```

---

## 6. 第二步：读取所有包配置

```python
packages = load_packages()
```

这一行会把 `packages/packages.toml` 全部读进来。

结果大致是一个字典：

```python
{
    "obsidian": {
        "type": "github_release",
        "repo": "obsidianmd/obsidian-releases",
        "spec": "packages/obsidian/obsidian.spec"
    },
    "zotero": {
        "type": "aur",
        "repo": "zotero-bin",
        "spec": "packages/zotero/zotero.spec"
    }
}
```

你可以把它理解成一整本“包配置通讯录”。

---

## 7. 第三步：准备待更新清单

```python
to_update = []
```

这是一个空列表。

它的用途是：

> 把所有“需要更新的包”收集起来

最后输出的就是它。

一开始它什么都没有：

```python
to_update == []
```

---

## 8. 第四步：遍历每个包

```python
for name, cfg in packages.items():
```

这里的 `.items()` 会把字典拆成：

- `name`：包名
- `cfg`：这个包的配置

例如一次循环里可能得到：

```python
name = "obsidian"
cfg = {
    "type": "github_release",
    "repo": "obsidianmd/obsidian-releases",
    "spec": "packages/obsidian/obsidian.spec"
}
```

下一轮可能变成：

```python
name = "zotero"
cfg = {
    "type": "aur",
    "repo": "zotero-bin",
    "spec": "packages/zotero/zotero.spec"
}
```

---

## 9. 为什么这里用了 `try / except`

```python
try:
    ...
except Exception as e:
    print(f"Error fetching {name}: {e}", file=sys.stderr)
```

这样做的原因是：

> 某一个包出错，不应该让整个巡检过程全部崩掉。

例如：

- `obsidian` 正常
- `zotero` 的上游接口临时坏了

那理想行为应该是：

- 打印 `zotero` 的错误
- 继续检查其他包

而不是整个脚本直接退出。

所以这里是“单包隔离失败”的设计。

---

## 10. 第五步：抓取上游数据

```python
data = fetch_upstream_data(cfg)
```

这一步会根据 `cfg["type"]` 决定去哪里拿数据。

### 举例 1：release 包

如果：

```python
cfg["type"] == "github_release"
```

那么可能拿到：

```python
data = {"version": "v1.12.8"}
```

### 举例 2：commit 包

如果：

```python
cfg["type"] == "github_commit"
```

那么可能拿到：

```python
data = {
    "sha": "abcdef1234567890",
    "short": "abcdef1",
    "date": "20260420",
    "msg": "fix: improve candidate matching"
}
```

### 它的意义

这一步得到的是“上游现在最新是什么”的事实依据。

后面 `is_update_needed()` 就要拿这个数据和本地 spec 做比较。

---

## 11. 第六步：判断这个包要不要更新

```python
if args.force or is_update_needed(cfg, data):
```

这是一行非常关键的判断。

它的含义是：

> 只要满足以下两者之一，就把这个包加入待更新列表：

- 用户手动指定了 `--force`
- 或者这个包确实检测到需要更新

### 拆开理解

#### 情况 A：用了 `--force`

```python
args.force == True
```

那不管 `is_update_needed(...)` 返回什么，这个包都会被加入列表。

#### 情况 B：没用 `--force`

```python
args.force == False
```

那就完全由：

```python
is_update_needed(cfg, data)
```

决定。

如果返回 `True`，加入列表。  
如果返回 `False`，跳过。

---

## 12. 第七步：把需要更新的包加入列表

```python
to_update.append({"name": name, "data": data})
```

一旦判断“这个包需要处理”，就往 `to_update` 列表里塞一个字典。

格式统一是：

```python
{
    "name": "<包名>",
    "data": <上游数据字典>
}
```

例如：

```python
{
    "name": "obsidian",
    "data": {"version": "v1.12.8"}
}
```

或者：

```python
{
    "name": "krunner-pinyin-search",
    "data": {
        "sha": "abcdef1234567890",
        "short": "abcdef1",
        "date": "20260420"
    }
}
```

这个结构非常重要，因为后面的 workflow 就是按这个格式去拆解和处理的。

---

## 13. 出错时为什么写到 `stderr`

```python
print(f"Error fetching {name}: {e}", file=sys.stderr)
```

原因是：

这个脚本最后要输出一个纯 JSON：

```python
print(json.dumps(to_update))
```

如果错误日志也写到标准输出，那么 JSON 就会被污染，例如变成：

```text
Error fetching zotero: ...
[{"name":"obsidian","data":{"version":"v1.12.8"}}]
```

这样后面的 GitHub Actions 就无法把它当 JSON 解析了。

所以这里把错误信息单独写到标准错误输出，是一个很正确的设计。

---

## 14. 第八步：输出最终 JSON

```python
print(json.dumps(to_update))
```

这是整个脚本最重要的最终产物。

### 如果没有更新

输出：

```json
[]
```

### 如果有更新

例如输出：

```json
[
  {
    "name": "obsidian",
    "data": {"version": "v1.12.8"}
  },
  {
    "name": "zotero",
    "data": {"version": "7.1.0"}
  }
]
```

这个 JSON 会被 GitHub Actions workflow 读取，并作为 matrix 的来源。

---

## 15. 一次完整的执行例子

假设 `packages/packages.toml` 里有两个包：

```python
{
    "obsidian": {...},
    "zotero": {...}
}
```

并且：

- `obsidian` 上游已经更新到 `v1.12.8`
- `zotero` 本地已经是最新

执行：

```bash
uv run scripts/check_upstream.py
```

### 运行过程

#### 第 1 轮：`obsidian`

1. 调用 `fetch_upstream_data(cfg)`
2. 得到：
   ```python
   {"version": "v1.12.8"}
   ```
3. 调用 `is_update_needed(cfg, data)`
4. 返回：
   ```python
   True
   ```
5. 加入列表：
   ```python
   {"name": "obsidian", "data": {"version": "v1.12.8"}}
   ```

#### 第 2 轮：`zotero`

1. 调用 `fetch_upstream_data(cfg)`
2. 得到：
   ```python
   {"version": "7.1.0"}
   ```
3. 调用 `is_update_needed(cfg, data)`
4. 返回：
   ```python
   False
   ```
5. 不加入列表

### 最终输出

```json
[
  {
    "name": "obsidian",
    "data": {"version": "v1.12.8"}
  }
]
```

---

## 16. 再看 `--force` 的完整例子

执行：

```bash
uv run scripts/check_upstream.py --force
```

此时即使：

- `obsidian` 已经是最新
- `zotero` 也已经是最新

它们仍然都会被加入输出列表。

例如输出：

```json
[
  {
    "name": "obsidian",
    "data": {"version": "v1.12.8"}
  },
  {
    "name": "zotero",
    "data": {"version": "7.1.0"}
  }
]
```

这在调试 workflow 时特别有用，因为你可以强制触发后面的更新和构建流程。

---

## 17. 这个脚本和其他脚本的关系

这个脚本在整条链路里的位置非常关键。

### 它依赖谁

- `load_packages()`
- `fetch_upstream_data()`
- `is_update_needed()`

### 谁依赖它

- `.github/workflows/copr-update.yml`

workflow 里这一句：

```bash
PACKAGES=$(uv run scripts/check_upstream.py $FORCE_ARG)
```

拿到的就是这个脚本输出的 JSON。

也就是说：

> `check_upstream.py` 的输出，直接决定后面整个 workflow 要处理哪些包。

---

## 18. 一句话总结

如果你以后只记一句话，记这个就够了：

> `check_upstream.py` 会遍历所有包，抓取上游最新数据，筛出需要更新的包，并把它们整理成 JSON 列表输出。

再压缩一点：

> 它是整个自动化更新流程的“待处理清单生成器”。
