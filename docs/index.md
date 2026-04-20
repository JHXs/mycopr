# 学习文档总索引

这个目录下的文档，主要是为了帮助你逐步理解这个仓库的自动化更新与构建流程。

如果你把整个系统想成一条流水线，那么推荐的学习顺序是：

1. 先理解配置文件怎么被读取
2. 再理解上游数据怎么抓
3. 再理解怎么判断“要不要更新”
4. 再理解怎么真正修改 `.spec`
5. 最后理解 GitHub Actions 如何把这些步骤串起来

---

## 推荐阅读顺序

### 1. 配置文件是怎么读进来的

- [load_toml.md](/home/hansel/Documents/ITProject/copr/docs/load_toml.md)

适合解决的问题：

- `packages/packages.toml` 读进 Python 后长什么样
- `for name, cfg in packages.items()` 到底是什么意思
- 包配置字典在后续脚本里是怎么被使用的

---

### 2. 上游数据是怎么抓回来的

- [fetch_upstram_data.md](/home/hansel/Documents/ITProject/copr/docs/fetch_upstram_data.md)

适合解决的问题：

- `github_release`、`github_commit`、`aur`、`gitea_release` 这几种类型分别怎么获取版本
- `fetch_upstream_data()` 返回的数据结构长什么样
- 为什么有的包返回 `version`，有的返回 `sha` / `short` / `date`

---

### 3. 怎么判断一个包需不需要更新

- [is_update_needed.md](/home/hansel/Documents/ITProject/copr/docs/is_update_needed.md)
- [update_detection_helpers.md](/home/hansel/Documents/ITProject/copr/docs/update_detection_helpers.md)

两篇的区别：

- `is_update_needed.md` 更偏整体思路
- `update_detection_helpers.md` 更细讲 `get_default_transforms()`、`pick_upstream_value()`、`is_update_needed()` 这 3 个函数

适合解决的问题：

- 为什么脚本不是比较整个文件，而是比较关键 `%global` 宏
- `transforms` 到底在做什么
- 宏名和上游字段是怎么对应起来的

---

### 4. 怎么把上游数据真正写回 `.spec`

- [update_spec_script.md](/home/hansel/Documents/ITProject/copr/docs/update_spec_script.md)

适合解决的问题：

- `update_spec.py` 到底改了 `.spec` 里的哪些地方
- `%global` 宏替换的正则怎么理解
- `%changelog` 是怎么自动插入的
- 为什么 release 型包会重置 `Release`

---

### 5. 怎么生成“待更新清单”

- [check_upstream_script.md](/home/hansel/Documents/ITProject/copr/docs/check_upstream_script.md)

适合解决的问题：

- `check_upstream.py` 怎么遍历所有包
- 它怎么把“是否需要更新”的结果整理成 JSON 列表
- `--force` 为什么有用
- 为什么错误输出要走 `stderr`

---

### 6. GitHub Actions 怎么把整条链路串起来

- [copr_update_workflow.md](/home/hansel/Documents/ITProject/copr/docs/copr_update_workflow.md)

适合解决的问题：

- workflow 为什么要拆成 3 个 job
- `outputs`、`needs`、`matrix` 怎么传递数据
- 为什么要先更新 spec，再触发 Copr 构建
- `copr-cli buildscm` 最后是怎么被调用的

---

## 如果你只想快速建立整体理解

建议按这个最短路径阅读：

1. [load_toml.md](/home/hansel/Documents/ITProject/copr/docs/load_toml.md)
2. [fetch_upstram_data.md](/home/hansel/Documents/ITProject/copr/docs/fetch_upstram_data.md)
3. [update_detection_helpers.md](/home/hansel/Documents/ITProject/copr/docs/update_detection_helpers.md)
4. [update_spec_script.md](/home/hansel/Documents/ITProject/copr/docs/update_spec_script.md)
5. [copr_update_workflow.md](/home/hansel/Documents/ITProject/copr/docs/copr_update_workflow.md)

---

## 如果你只想排查某一类问题

### 问题：为什么某个包没有进入待更新列表？

先看：

- [check_upstream_script.md](/home/hansel/Documents/ITProject/copr/docs/check_upstream_script.md)
- [update_detection_helpers.md](/home/hansel/Documents/ITProject/copr/docs/update_detection_helpers.md)

### 问题：为什么 spec 没被正确改掉？

先看：

- [update_spec_script.md](/home/hansel/Documents/ITProject/copr/docs/update_spec_script.md)

### 问题：为什么 workflow 没触发 Copr 构建？

先看：

- [copr_update_workflow.md](/home/hansel/Documents/ITProject/copr/docs/copr_update_workflow.md)

### 问题：为什么某个上游版本抓不对？

先看：

- [fetch_upstram_data.md](/home/hansel/Documents/ITProject/copr/docs/fetch_upstram_data.md)

---

## 一句话总结

这个 `docs/` 目录里的教学文档，实际上是在解释同一条链路：

> 配置文件 -> 抓取上游数据 -> 判断是否需要更新 -> 修改 spec -> GitHub Actions 调度 -> Copr 构建

如果你以后忘了从哪篇开始看，就从这篇索引回来找。
