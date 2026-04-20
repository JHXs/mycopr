这份文档专门解释 GitHub Actions 工作流文件：

- `.github/workflows/copr-update.yml`

它是这个仓库自动化更新流程的总调度器。

如果说：

- `check_upstream.py` 是“侦察兵”
- `update_spec.py` 是“施工队”

那么 `copr-update.yml` 就是：

> “项目经理 + 调度中心”

它负责决定：

- 什么时候开始巡检
- 哪些包需要处理
- 先改哪些文件
- 什么时候提交变更
- 最后怎么触发 Copr 构建

---

## 1. 这个工作流整体要做什么

这份 workflow 的使命可以浓缩成一句话：

> 定时检查上游是否有新版本；如果有，就自动更新对应的 `.spec` 文件，提交到仓库，并触发 Copr 构建。

它大致分成 3 个阶段：

1. 找出哪些包需要更新
2. 更新这些包的 `.spec`
3. 对这些包逐个触发 Copr 构建

你可以把它想成一条流水线：

```text
检查上游 -> 生成待更新列表 -> 更新 spec -> 提交变更 -> 触发构建
```

---

## 2. 工作流的文件头是什么意思

```yaml
name: Unified Copr Update
```

这只是 GitHub Actions 页面里显示的工作流名字。

你在 GitHub 网页上看到的就是这个标题。

---

## 3. `on:` 这一段在讲“什么时候触发”

```yaml
on:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:
    inputs:
      force_build:
        description: 'Force build even if no update'
        required: false
        type: boolean
        default: false
```

它定义了两种触发方式。

### 方式 1：定时触发

```yaml
schedule:
  - cron: "0 0 * * *"
```

这表示每天按 cron 定时执行一次。

GitHub Actions 的 `cron` 默认按 **UTC** 计算。  
所以：

```text
0 0 * * *
```

表示每天 UTC 00:00 运行一次。

如果换算成中国时区，通常是每天早上 8 点左右。

### 方式 2：手动触发

```yaml
workflow_dispatch:
```

这表示你可以在 GitHub Actions 页面上手动点“Run workflow”。

而且这里还定义了一个输入参数：

```yaml
force_build
```

它的意思是：

> 即使没有检测到更新，也强制走一遍更新/构建流程

这在调试 workflow 时特别有用。

---

## 4. `permissions:` 在控制什么

```yaml
permissions:
  contents: write
```

这表示这个 workflow 需要对仓库内容有写权限。

为什么要写权限？

因为后面的 `update-specs` job 会：

- 修改 `.spec` 文件
- 提交变更回仓库

如果没有 `contents: write`，自动 commit 那一步通常会失败。

---

## 5. 整个 workflow 一共有几个 job

这份 workflow 里有 3 个 job：

- `setup-matrix`
- `update-specs`
- `trigger-builds`

你可以把它们理解成 3 个车间：

- `setup-matrix`：先做“侦察和排产”
- `update-specs`：再做“文件更新和提交”
- `trigger-builds`：最后做“逐包触发 Copr 构建”

---

## 6. `setup-matrix` 做什么

这一段：

```yaml
setup-matrix:
  runs-on: ubuntu-latest
  outputs:
    matrix: ${{ steps.set-matrix.outputs.matrix }}
    has_updates: ${{ steps.set-matrix.outputs.has_updates }}
```

说明这个 job 会产出两个结果给后面的 job 使用：

- `matrix`
- `has_updates`

### `matrix` 是什么

它是一个 JSON 数组，里面列出“哪些包需要更新，以及它们对应的上游数据”。

例如可能长这样：

```json
[
  {
    "name": "obsidian",
    "data": {"version": "v1.12.8"}
  },
  {
    "name": "krunner-pinyin-search",
    "data": {
      "sha": "abcdef123456",
      "short": "abcdef1",
      "date": "20260420"
    }
  }
]
```

### `has_updates` 是什么

它只是一个布尔信号，告诉后续 job：

- 有更新：`true`
- 没更新：`false`

这样后续 job 就能决定要不要继续跑。

---

## 7. `setup-matrix` 里的步骤逐个解释

### 第一步：检出仓库

```yaml
- uses: actions/checkout@v5
```

作用：

- 把仓库代码拉到 GitHub Actions 的运行环境里

没有这一步，后面脚本根本没有代码可执行。

---

### 第二步：安装 `uv`

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@...
```

作用：

- 安装 `uv`
- 后面所有 `uv run ...` 才能正常工作

这里还开启了：

```yaml
enable-cache: true
```

意思是尽量复用依赖缓存，加快 workflow 执行速度。

---

### 第三步：真正检测上游并生成矩阵

```yaml
- name: Fetch upstream data and set matrix
  id: set-matrix
  run: |
    FORCE_ARG=""
    if [ "${{ github.event.inputs.force_build }}" == "true" ]; then
      FORCE_ARG="--force"
    fi
```

这段先处理手动触发时的 `force_build` 输入。

意思是：

- 如果用户手动勾选了 `force_build`
- 就给 `check_upstream.py` 加上 `--force`

这会让脚本把所有包都当作“需要处理”。

### 关键命令

```bash
PACKAGES=$(uv run scripts/check_upstream.py $FORCE_ARG)
```

这一步会运行 `check_upstream.py`，得到一个 JSON 数组。

然后把它写到 job output：

```bash
echo "matrix=$PACKAGES" >> $GITHUB_OUTPUT
```

这就是为什么后面的 job 能用：

```yaml
needs.setup-matrix.outputs.matrix
```

来取到这个值。

### 判断有没有更新

```bash
if [ "$PACKAGES" == "[]" ]; then
  echo "has_updates=false" >> $GITHUB_OUTPUT
else
  echo "has_updates=true" >> $GITHUB_OUTPUT
fi
```

逻辑很简单：

- 如果结果是空数组 `[]`
  - 说明没有包需要更新
- 否则
  - 说明至少有一个包要处理

同时还会把待更新包名打印出来，方便看 Actions 日志。

---

## 8. `update-specs` 做什么

这一段：

```yaml
update-specs:
  needs: setup-matrix
  if: needs.setup-matrix.outputs.has_updates == 'true'
```

意思是：

- 必须等 `setup-matrix` 完成
- 只有检测到更新时才执行

所以它的职责很明确：

> 根据待更新列表，批量运行 `update_spec.py`，然后把改动提交回仓库。

---

## 9. 为什么这里有 `needs`

```yaml
needs: setup-matrix
```

`needs` 的作用是：

1. 建立执行顺序
2. 允许读取前一个 job 的 outputs

所以这个 job 才能读到：

```yaml
needs.setup-matrix.outputs.matrix
```

---

## 10. `update-specs` 的步骤逐个解释

### 检出仓库

```yaml
- uses: actions/checkout@v5
```

还是为了拿到代码。

### 安装 `uv`

```yaml
- name: Install uv
```

为了后续运行 Python 脚本。

### `uv sync --locked`

```yaml
- name: Sync dependencies
  run: uv sync --locked
```

意思是：

- 按锁文件安装依赖
- 保证运行环境和仓库预期一致

### 批量更新 spec

```yaml
echo '${{ needs.setup-matrix.outputs.matrix }}' | jq -c '.[]' | while read pkg; do
  name=$(echo "$pkg" | jq -r '.name')
  data=$(echo "$pkg" | jq -c '.data')
  echo "Processing $name..."
  uv run scripts/update_spec.py --pkg "$name" --upstream-data "$data" || echo "::warning::Failed to update $name"
done
```

这段是 `update-specs` 最核心的循环。

### 它在做什么

假设 `matrix` 是：

```json
[
  {"name":"obsidian","data":{"version":"v1.12.8"}},
  {"name":"zotero","data":{"version":"7.1.0"}}
]
```

那这段 shell 会逐个取出每一项：

#### 第 1 次循环

- `name=obsidian`
- `data={"version":"v1.12.8"}`

执行：

```bash
uv run scripts/update_spec.py --pkg "obsidian" --upstream-data '{"version":"v1.12.8"}'
```

#### 第 2 次循环

- `name=zotero`
- `data={"version":"7.1.0"}`

执行：

```bash
uv run scripts/update_spec.py --pkg "zotero" --upstream-data '{"version":"7.1.0"}'
```

### 为什么用了 `|| echo "::warning::..."`

这表示：

- 如果某个包更新失败
- 记录一个 warning
- 但不要让整个循环立刻中断

这是一种偏“尽量继续处理其他包”的策略。

---

## 11. 自动提交是怎么工作的

```yaml
- name: Commit changes
  id: commit
  uses: stefanzweifel/git-auto-commit-action@v7
  with:
    commit_message: "chore: unified spec update [skip ci]"
```

这个 Action 会：

- 检查工作区是否有改动
- 如果有，就自动 `git add` + `git commit` + `git push`

### commit message 里的 `[skip ci]` 是什么意思

```text
[skip ci]
```

通常用于避免这次自动提交再次触发一轮新的 CI 工作流，造成循环。

---

## 12. `new_sha` 为什么重要

```yaml
outputs:
  new_sha: ${{ steps.commit.outputs.commit_hash || github.sha }}
```

这里的意思是：

- 如果 `git-auto-commit-action` 产生了一个新 commit
  - 就输出那个新 commit 的 hash
- 如果没有新 commit
  - 就退回当前 workflow 对应的 `github.sha`

后面的 `trigger-builds` 需要知道：

> 到底应该用哪个 commit 去触发 Copr 构建

因为 Copr 应该构建“更新后的代码”，而不是旧代码。

---

## 13. `trigger-builds` 做什么

这一段：

```yaml
trigger-builds:
  needs: [setup-matrix, update-specs]
```

说明它同时依赖两个 job：

- `setup-matrix`
- `update-specs`

它的职责是：

> 对每个需要更新的包，逐个触发 Copr 的 `buildscm`

---

## 14. 这段复杂的 `if:` 条件是什么意思

```yaml
if: |
  always() &&
  needs.setup-matrix.result == 'success' &&
  (needs.update-specs.result == 'success' || needs.update-specs.result == 'skipped') &&
  needs.setup-matrix.outputs.has_updates == 'true'
```

逐条翻译：

- `always()`
  - 即使前面有 job 被跳过，也继续评估条件

- `needs.setup-matrix.result == 'success'`
  - 必须成功拿到待更新列表

- `(needs.update-specs.result == 'success' || needs.update-specs.result == 'skipped')`
  - 更新 spec 这一步要么成功，要么因为没有更新而被跳过

- `needs.setup-matrix.outputs.has_updates == 'true'`
  - 只有真的有更新时才触发构建

总结一下：

> 只有在“待更新列表成功生成，并且确实有更新”的情况下，才去触发 Copr。

---

## 15. `strategy.matrix` 在做什么

```yaml
strategy:
  fail-fast: false
  matrix:
    package: ${{ fromJson(needs.setup-matrix.outputs.matrix) }}
```

这里把上一个 job 生成的 JSON 数组，变成 GitHub Actions 的 matrix。

例如：

```json
[
  {"name":"obsidian","data":{"version":"v1.12.8"}},
  {"name":"zotero","data":{"version":"7.1.0"}}
]
```

会变成两次独立的 matrix 运行：

### 第一次

```yaml
matrix.package.name == "obsidian"
```

### 第二次

```yaml
matrix.package.name == "zotero"
```

这样每个包都能单独触发构建。

### `fail-fast: false` 是什么意思

表示：

- 即使某个包构建失败
- 其他包也继续执行

这对于批量构建很重要。

---

## 16. 为什么这里 checkout 要指定 `ref`

```yaml
- uses: actions/checkout@v5
  with:
    ref: ${{ needs.update-specs.outputs.new_sha || github.sha }}
```

原因是：

- `update-specs` 可能已经生成并 push 了一个新 commit
- `trigger-builds` 必须基于这个“最新 commit”去触发构建

否则 Copr 构建拿到的就还是旧代码。

---

## 17. `Get Package Info` 这一步在干什么

```yaml
INFO=$(uv run python -c "
from pathlib import Path
...
config_path = Path('packages/packages.toml')
with config_path.open('rb') as f:
    pkg_config = tomllib.load(f).get('${{ matrix.package.name }}', {})
    print(f\"spec_file={pkg_config.get('spec', '')}\")
    print(f\"copr_repos={','.join(pkg_config.get('copr_repos', []))}\")
")
echo "$INFO" >> $GITHUB_OUTPUT
```

这一步的目标是：

> 根据当前 matrix 包名，取出它对应的 spec 路径和 Copr 仓库列表。

例如对于 `obsidian`，可能得到：

```text
spec_file=packages/obsidian/obsidian.spec
copr_repos=ikunji/mycopr,ikunji/obsidian
```

这些值会成为这个 step 的 outputs，供下一步使用。

---

## 18. `Trigger Copr Build` 是怎么工作的

这一段是 workflow 的最终落地点：

```bash
NEW_SHA=$(git rev-parse HEAD)

IFS=',' read -ra ADDR <<< "$REPOS"
for REPO in "${ADDR[@]}"; do
  echo "🚀 Building ${{ matrix.package.name }} in $REPO..."
  SUBDIR=$(dirname "$SPEC_FILE")
  SPEC_NAME=$(basename "$SPEC_FILE")

  uv run copr-cli --config <(echo "${COPR_CLI_CONFIG}") buildscm \
    --clone-url "https://github.com/${{ github.repository }}" \
    --commit "${NEW_SHA}" \
    --subdir "${SUBDIR}" \
    --spec "${SPEC_NAME}" \
    --type git \
    --method rpkg \
    "${REPO}"
done
```

### `REPOS` 是什么

前一步拿到的 `copr_repos`，例如：

```text
ikunji/mycopr,ikunji/obsidian
```

这段代码会把它拆成数组，然后循环：

- 第一次构建到 `ikunji/mycopr`
- 第二次构建到 `ikunji/obsidian`

### `SPEC_FILE` 是什么

例如：

```text
packages/obsidian/obsidian.spec
```

然后拆成：

- `SUBDIR=packages/obsidian`
- `SPEC_NAME=obsidian.spec`

### `buildscm` 的核心含义

`copr-cli buildscm` 的意思是：

> 让 Copr 自己从 Git 仓库拉指定 commit 的代码，并按指定 spec 构建

这里关键参数分别表示：

- `--clone-url`
  - Copr 去哪个 Git 仓库克隆源码

- `--commit`
  - 构建哪个 commit

- `--subdir`
  - spec 文件位于仓库里的哪个子目录

- `--spec`
  - spec 文件名是什么

- `--type git`
  - 源代码类型是 Git 仓库

- `--method rpkg`
  - 用 rpkg 风格构建

---

## 19. 一次完整执行示例

假设今天 `setup-matrix` 检测到两个包要更新：

```json
[
  {"name":"obsidian","data":{"version":"v1.12.8"}},
  {"name":"zotero","data":{"version":"7.1.0"}}
]
```

那么整个 workflow 的执行过程大致是：

### 阶段 1：`setup-matrix`

- 调用 `check_upstream.py`
- 生成 matrix
- 输出：
  - `has_updates=true`
  - `matrix=[...]`

### 阶段 2：`update-specs`

- 对 `obsidian` 调用：
  ```bash
  uv run scripts/update_spec.py --pkg obsidian --upstream-data '{"version":"v1.12.8"}'
  ```
- 对 `zotero` 调用：
  ```bash
  uv run scripts/update_spec.py --pkg zotero --upstream-data '{"version":"7.1.0"}'
  ```
- 自动提交改动
- 输出新 commit hash

### 阶段 3：`trigger-builds`

matrix 分裂成两个独立任务：

#### 任务 A：`obsidian`

- 读取：
  - `spec_file=packages/obsidian/obsidian.spec`
  - `copr_repos=ikunji/mycopr,ikunji/obsidian`
- 分别触发两个 Copr 构建

#### 任务 B：`zotero`

- 读取：
  - `spec_file=packages/zotero/zotero.spec`
  - `copr_repos=ikunji/mycopr`
- 触发对应 Copr 构建

---

## 20. 这份 workflow 最核心的设计思想

这份 workflow 有 3 个很重要的设计思想。

### 1. 用 `setup-matrix` 先做“排产”

先决定有哪些包需要处理，再把这个结果传给后面的 job。

好处是：

- 逻辑清晰
- 不需要每个 job 自己再查一遍上游

### 2. 用 job outputs 串联数据流

例如：

- `setup-matrix.outputs.matrix`
- `setup-matrix.outputs.has_updates`
- `update-specs.outputs.new_sha`

这让 workflow 形成了一条清晰的数据传递链。

### 3. 用 matrix 并行触发不同包构建

这样：

- 一个包失败，不影响另一个包
- 构建更快
- 日志更清晰

---

## 21. 一句话总结

如果你以后只记一句话，记这个就够了：

> `copr-update.yml` 会先生成“待更新包清单”，再批量更新 spec，最后按包逐个触发 Copr 构建。

再压缩一点：

> 这份 workflow 是整个自动更新系统的总调度器。
