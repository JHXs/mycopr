# CI/CD 重构方案

## 背景

当前仓库中的 GitHub Actions 基本采用“一软件包对应一个 workflow 文件”的方式维护。这个方案在包数量较少时可以工作，但随着仓库中软件包数量增加，维护成本会明显上升。

目前的主要问题：

- 新增一个软件包时，通常需要复制并修改一个新的 `.github/workflows/*.yml` 文件。
- 多个 workflow 的结构高度相似，重复逻辑较多。
- 相同能力分散在多个文件中，后续调整例如 `copr-cli` 版本、触发条件、提交逻辑时，需要逐个修改。
- 不同包的差异混在 workflow 里，导致“配置”和“执行逻辑”没有分离。

## 重构目标

将当前“每个软件包一个 workflow”的模式，逐步收敛为“单一主 workflow + 配置驱动 + 脚本化更新策略”的模式。

目标效果：

- 新增软件包时，尽量不再新增 workflow 文件。
- 包的差异通过配置文件描述，而不是复制 workflow。
- 检查上游版本、更新 spec、提交变更、触发 Copr 构建这些公共逻辑统一复用。
- 后续维护时，优先修改脚本和配置，而不是批量修改多个 workflow。

## 可借鉴的参考

`test/copr` 目录中的方案值得借鉴，核心思路不是照抄具体实现，而是借鉴其结构设计：

- 使用统一的包配置文件，例如 `packages.json`。
- 使用统一脚本批量检查上游版本。
- 使用统一 workflow 处理更新、提交和构建。
- 将“每个包的差异”集中在配置层。

这套思路比当前仓库更适合长期扩展。

## 为什么不能直接照搬 `test/copr`

虽然 `test/copr` 的总体方向适合本仓库，但不能直接原样迁移，原因是当前仓库的软件包更新方式并不统一。

本仓库中至少存在以下几类 spec 更新模式：

- `package_version` 宏更新
  例如 `cc-switch-cli`、`proxybridge`、`zotero`、`reframe`、`um-cli`、`maple-mono`
- `commit` 宏更新
  例如 `cto2api`
- 多字段联动更新
  例如 `krunner-pinyin-search` 需要同时更新 `git_commit`、`git_short`、`commit_date`
- 版本号和派生字段联动更新
  例如 `ge-proton` 需要同时更新 `package_version` 与 `proton_ver`

而 `test/copr` 中的脚本更偏向处理标准化较高的包结构，例如直接修改 `Version:` 和 `Release:`。因此本仓库应当借鉴其“配置驱动”的方向，但需要结合现有 spec 格式实现自己的更新策略。

## 目标架构

建议逐步收敛到以下结构：

```text
.github/workflows/
  update-copr.yml

scripts/
  check_upstream.py
  update_spec.py
  build_copr.py

packages.json
```

说明：

- `update-copr.yml`
  统一入口 workflow，负责调度检查、提交、构建。
- `packages.json`
  描述每个包的目录、spec、上游来源、更新策略、构建目标仓库等信息。
- `scripts/check_upstream.py`
  统一查询上游版本、tag、commit 或其他来源。
- `scripts/update_spec.py`
  根据包的更新策略修改 spec 文件中的目标字段。
- `scripts/build_copr.py`
  统一封装 `copr-cli buildscm` 调用逻辑，避免 workflow 中堆积大量 shell。

## 建议的配置模型

`packages.json` 建议至少描述以下字段：

- `name`
- `subdir`
- `spec`
- `build_repos`
- `source_type`
- `update_strategy`

可选扩展字段：

- `upstream_url`
- `github_repo`
- `github_branch`
- `tag_prefix`
- `npm_package`
- `aur_package`
- `spec_fields`
- `enabled`

示例结构：

```json
{
  "packages": [
    {
      "name": "cc-switch-cli",
      "subdir": "cc-switch-cli",
      "spec": "cc-switch-cli.spec",
      "build_repos": ["ikunji/mycopr", "ikunji/cc-switch-cli"],
      "source_type": "github_release",
      "github_repo": "SaladDay/cc-switch-cli",
      "tag_prefix": "v",
      "update_strategy": "package_version"
    },
    {
      "name": "cto2api",
      "subdir": "cto2api",
      "spec": "cto2api.spec",
      "build_repos": ["ikunji/mycopr", "ikunji/cto2api"],
      "source_type": "git_commit",
      "github_repo": "wyeeeee/cto2api",
      "github_branch": "main",
      "update_strategy": "commit"
    }
  ]
}
```

## 统一 workflow 的职责

统一后的 workflow 建议负责以下事情：

1. 读取 `packages.json`
2. 批量检查所有已纳管软件包的上游状态
3. 找出需要更新的包
4. 调用脚本更新对应 spec 文件
5. 自动提交并推送变更
6. 仅对发生变化的软件包触发 Copr 构建
7. 支持手动触发 `force_build`

这样新增软件包时，只需要：

- 增加软件包目录和 spec 文件
- 在 `packages.json` 中增加一条配置

不再需要新增单独的 workflow 文件。

## 更新策略建议

考虑到当前仓库包类型不统一，建议显式定义更新策略，而不是把逻辑写死在 workflow 中。

建议至少支持以下策略：

- `package_version`
  适用于修改 `%global package_version`
- `commit`
  适用于修改 `%global commit`
- `git_snapshot`
  适用于同时更新 `git_commit`、`git_short`、`commit_date`
- `ge_proton`
  适用于同时更新 `package_version` 和 `proton_ver`

如果后续出现特殊包，可以继续追加新的策略类型，而不需要新建一个 workflow。

## 迁移建议

建议分阶段进行，而不是一次性替换全部现有 workflow。

### 第一阶段：建立基础设施

- 新增 `packages.json`
- 新增统一脚本目录 `scripts/`
- 新增统一 workflow `update-copr.yml`
- 先接入一两个结构简单的软件包进行验证

优先选择：

- `cc-switch-cli`
- `proxybridge`
- `reframe`
- `maple-mono`

这些包的 spec 更新方式较接近，适合先打通流程。

### 第二阶段：纳入中等复杂度软件包

- 纳入 `zotero`
- 纳入 `um-cli`
- 纳入 `cto2api`

这一阶段主要验证不同来源的数据抓取方式，例如 GitHub release、第三方 API、commit 追踪。

### 第三阶段：处理特殊更新逻辑

- 纳入 `krunner-pinyin-search`
- 纳入 `ge-proton`

这一阶段要补齐联动字段更新能力，确保脚本可维护，而不是回退到“为特殊包单独写 workflow”。

### 第四阶段：收尾

- 对照新 workflow 的覆盖范围，删除已被替代的旧 workflow 文件
- 清理重复的 shell 逻辑
- 统一 secrets、变量命名和构建输出

## 实施原则

- 优先减少重复，而不是一次追求最复杂的抽象。
- 配置应尽量描述“包是什么”，脚本负责描述“如何执行”。
- 如果某个包确实特殊，也应优先通过新增一种 `update_strategy` 解决，而不是回到单包单 workflow。
- 保持迁移过程可回滚，避免一次性大改导致所有包构建中断。

## 预期收益

完成重构后，预期可以获得以下收益：

- 新增软件包的成本显著降低
- workflow 数量减少，仓库结构更清晰
- CI/CD 修改点集中，维护负担更低
- 更容易观察哪些包已纳入自动化管理，哪些仍是特例
- 后续如需加入更多包，扩展路径更明确

## 当前结论

这个仓库的 CI/CD 体系可以明确借鉴 `test/copr` 的设计方向，尤其是：

- 配置驱动
- 单一主 workflow
- 统一脚本处理更新和构建

但实现时必须结合当前仓库已有 spec 结构，补齐多种更新策略，不能直接按 `test/copr` 的现有脚本照搬。
