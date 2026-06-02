这个 `fetch_upstream_data` 函数本质上是一个**“路由分发器”**或**“调度员”**。它根据你在 `packages/packages.toml` 里定义的 `type` 类型，把任务交给不同的“专家”去处理。

这几个函数是针对不同“数据源”的爬虫或接口调用工具，它们的目标都是**拿到最新的版本标识（Version/Commit SHA）**。

你可以把它们看作四个不同平台的“情报员”：

### 1. `get_github_release` (GitHub 最新发布版专家)
*   **它的活儿**：访问 GitHub API，找到该项目标记为 `latest`（最新）的那个 Release。
*   **结果**：它只带回一个东西：`tag_name`（比如 `v1.2.3`），并把它存成 `version`。
*   **适用场景**：绝大多数有正式发布习惯的 GitHub 项目。

这是最常用的专家，专门盯着 GitHub 的 **Latest Release**（最新发布）。

*   **它的逻辑**：
    1.  **构造地址**：把 `repo`（如 `SaladDay/cc-switch-cli`）填进 GitHub 的 API 地址：`https://api.github.com/repos/SaladDay/cc-switch-cli/releases/latest`。
    2.  **敲门问路**：使用 `httpx` 发送请求。`follow_redirects=True` 的意思是“如果项目改名或搬家了，自动跟着跳过去”。
    3.  **提取数据**：GitHub 会返回一堆 JSON 数据（包含发布日志、下载链接等），这个专家**只取 `tag_name`**（也就是版本号标签，比如 `v1.2.0`）。
*   **返回结果**：`{"version": "v1.2.0"}`
*   **优点**：非常稳定，拿到的都是开发者认为“已经做好了”的版本。


### 2. `get_github_commit` (GitHub 最新代码提交专家)
*   **它的活儿**：当项目没有正式 Release，或者你想追求“尝鲜”使用最新代码时，它会去查最新的 **Commit（提交记录）**。
*   **细节**：它会把长长的 `sha`（指纹）、前 7 位的 `short` 指纹，还有提交日期（格式化成 `20231027` 这种数字）都抓回来。
*   **结果**：它返回一个内容很丰富的字典，方便后续生成类似 `0.1.20231027gitabcdef` 这种版本号。

当一个项目很久不发 Release，或者你想直接追随开发者最新的代码时，就派这个专家去。

*   **它的逻辑**：
    1.  **查提交记录**：访问 API：`.../commits?per_page=1`，意思是“我只要最新的一次代码提交（Commit）”。
    2.  **深度挖掘**：
        *   **SHA**：抓取 40 位的哈希值（代码的唯一指纹）。
        *   **Short SHA**：截取前 7 位（比如 `a1b2c3d`），在打包时常作为后缀。
        *   **Date**：把提交日期（如 `2023-10-27T...`）变成纯数字格式 `20231027`。
        *   **Msg**：顺便抓一下那次提交的标题（前 60 个字），作为备注。
*   **返回结果**：返回一个很厚的字典，包含 `sha`, `short`, `date`, `msg` 等。
*   **优点**：能实现“每日更新”的效果，只要开发者提交了代码，你就能立马检测到。


### 3. `get_aur_version` (Arch Linux AUR 专家)
*   **它的活儿**：它不去 GitHub，而是去 **AUR (Arch User Repository)** 读取 Arch 打包元数据。
*   **实现细节**：它会同时下载 `.SRCINFO` 和 `PKGBUILD`，解析其中的简单变量赋值，并生成一些通用别名。
*   **适用场景**：如果你想让 Copr 包跟随 AUR 包维护者提供的版本号、日期、build id、commit 等字段。

这个专家很特殊，它不去源码仓库，而是去 **Arch Linux 的 AUR 社区**。

*   **它的逻辑**：
    1.  **下载元数据**：下载该包在 AUR 里的 `.SRCINFO` 和 `PKGBUILD`。
    2.  **解析简单变量**：扫描 `pkgver=...`、`pkgdate=...`、`_build=...`、`_commit=...` 这类简单标量赋值。
    3.  **跳过复杂 shell 结构**：数组、函数、命令替换不会被当成字段，例如 `source=(...)`、`pkgver() { ... }`、`_build=$(...)`。
    4.  **生成别名**：`pkgver` 会变成 `version`，`pkgdate` 会变成 `date` / `package_date`，`_xxx` 会额外暴露成 `xxx`。
*   **返回结果示例**：`{"pkgver": "2.0.10", "version": "2.0.10", "_build": "5119448496078848", "build": "5119448496078848"}`
*   **优点**：以后 AUR 包如果新增简单字段，通常只需要在 `packages.toml` 的 `transforms` 里引用它，不需要改 `common.py`。

更详细的字段解析流程见 [aur_field_parsing.md](./aur_field_parsing.md)。

### 4. `get_gitea_release` (Gitea 平台专家)
*   **它的活儿**：逻辑和 GitHub Release 类似，但它是专门为 **Gitea**（一种类似 GitHub 的自建代码托管平台）设计的。
*   **细节**：它会额外过滤掉 `prerelease`（预发布版/测试版），只取最新的稳定版 `tag_name`。

Gitea 是一个开源版的 GitHub。如果软件托管在私有服务器上（比如你配置里的 `https://git.um-react.app`），就派它去。

*   **它的逻辑**：
    1.  **灵活地址**：它不仅需要 `repo`，还需要 `api_base`（服务器地址）。
    2.  **过滤测试版**：它会拿到一个 Release 列表，然后用 `r.get("prerelease", False)` 过滤掉所有的“预发布版/测试版”。
    3.  **取第一条**：在剩下的正式版里取最上面（最新）的一个。
*   **返回结果**：`{"version": "1.0.1"}`
*   **优点**：支持非 GitHub 平台的软件更新检测。

这四个“专家”函数是脚本中最核心的“情报员”，它们专门负责去不同的平台抓取最新的版本信息。

---

### 总结对比

| 专家 | 针对平台 | 抓取目标 | 典型返回 |
| :--- | :--- | :--- | :--- |
| **Release 专家** | GitHub | 发布的 Tag | `v1.2` |
| **Commit 专家** | GitHub | 最新的代码修改 | `a1b2c3d` + `20231027` |
| **AUR 专家** | Arch AUR | `.SRCINFO` / `PKGBUILD` 里的简单变量 | `3.4.5`、`_build`、`pkgdate` |
| **Gitea 专家** | 自建 Git | 稳定版的 Tag | `v2.0` |

**脚本的高明之处在于**：无论这些专家在外面跑业务有多辛苦（调 API、爬网页、搜正则），它们回到 `fetch_upstream_data` 函数时，都会统一把情报装进一个**字典**里交上去，让主脚本可以不用关心细节，直接进行下一步。

---

# 返回值
`fetch_upstream_data` 的返回结果就是一个 **Python 字典**。根据不同的包类型（Type），字典里的内容也不一样。

注意：这里说的是脚本内部拿到的完整上游数据。`check_upstream.py` 最后输出给 GitHub Actions 的 JSON 会再经过 `compact_upstream_data()` 压缩，只保留 `transforms` 需要的字段和少量元数据。

以下是针对 `packages/packages.toml` 里的四个典型包，脚本运行后返回的“情报”样子：

---

### 1. 针对 `github_release` 类型 (以 `cc-switch-cli` 为例)
这个最简单，只带回一个版本号。

*   **输入配置**：`{"type": "github_release", "repo": "SaladDay/cc-switch-cli"}`
*   **返回字典**：
```python
{
    "version": "v1.0.5"
}
```

---

### 2. 针对 `github_commit` 类型 (以 `cto2api` 为例)
这个内容非常丰富，因为它要把所有关于“代码快照”的信息都存下来。

*   **输入配置**：`{"type": "github_commit", "repo": "wyeeeee/cto2api"}`
*   **返回字典**：
```python
{
    "sha": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
    "git_commit": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
    "short": "a1b2c3d",
    "git_short": "a1b2c3d",
    "date": "20240419",
    "commit_date": "20240419",
    "msg": "feat: add new api endpoint"
}
```
*(注：它故意存了重复的键，比如 `sha` 和 `git_commit` 其实是一样的，这是为了让后面的脚本无论用哪个名字都能读到数据，增加兼容性。)*

---

### 3. 针对 `aur` 类型
AUR 类型会从 `.SRCINFO` 和 `PKGBUILD` 中解析简单变量，因此内部返回的完整字典可能字段比较丰富。

*   **输入配置**：`{"type": "aur", "repo": "antigravity"}`
*   **返回字典示例**：
```python
{
    "pkgver": "2.0.10",
    "version": "2.0.10",
    "_build": "5119448496078848",
    "build": "5119448496078848"
}
```

对于只有 `pkgver` 的普通 AUR 包，返回结果可能仍然很简单：

```python
{
    "pkgver": "7.0.3",
    "version": "7.0.3"
}
```

---

### 4. 针对 `gitea_release` 类型 (以 `um-cli` 为例)
虽然服务器不同，但返回格式和 GitHub Release 是一致的，方便统一处理。

*   **输入配置**：`{"type": "gitea_release", "repo": "um/cli", "api_base": "https://git.um-react.app"}`
*   **返回字典**：
```python
{
    "version": "2.1.0"
}
```

---

### 这个返回结果最后去了哪里？
在主脚本 `check_upstream.py` 中，这个返回的字典会被存进 `to_update` 列表，最后通过 `json.dumps()` 打印成这样：

```json
[
  {
    "name": "cc-switch-cli",
    "data": {"version": "v1.0.5"}
  },
  {
    "name": "cto2api",
    "data": {"sha": "a1b2c3d...", "short": "a1b2c3d", "date": "20240419", ...}
  }
]
```

**一句话总结**：`fetch_upstream_data` 的使命就是把那些抽象的网页数据，变成这种 **“键: 值”** 对齐的清晰表格（字典），让后面的程序可以直接拿来用。

这四个函数在 `fetch_upstream_data` 里被统一调用，不管它们内部是怎么抓数据的（有的调 API，有的读网页，有的算日期），它们最后都返回一个**字典**交给主脚本。

主脚本拿到这个字典后，就会和本地旧的版本号对比：“咦，AUR 专家说现在是 2.0 了，我本地 packages/packages.toml 还是 1.9，得更新了！”
