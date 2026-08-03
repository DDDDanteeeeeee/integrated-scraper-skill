# 采集契约

本契约定义综合抓取任务的输入隔离、状态、文件布局、证据和隐私边界。

## 任务输入

每次运行必须创建独立 `task_id`，并保存用户本次输入的 `target`、`objective`、
`time_range`、`decision_context` 和 `success_criteria`。`target` 可以是账号、
品牌、产品、关键词、话题或具体 URL，也可以自然包含目标网站或平台。示例
任务、历史任务和上次报告都不能为本次任务提供隐含来源、对象或业务视角。

## 本机配置

优先使用 `scripts/initialize.py` 创建 `config/collection.local.json`，不要要求
用户手工编辑 JSON。该文件只能保存可执行文件路径、OpenCLI Profile 名称、
本机 CDP 地址和本地输出目录；它被 Git 忽略。初始化器必须先预览、经显式
`--write-config` 才写入，且绝不覆盖现有配置。配置只能写入项目内
`config/collection.local.json`，CDP 只能是 `http://127.0.0.1`、
`http://localhost` 或 `http://[::1]`。

完成配置后必须运行 `scripts/pack_doctor.py`。只有 OpenCLI、
BrowserHarness、last30days、last30days-cn 和 Scrapling 全部就绪才可
开始采集；Cloakbrowser 没有明确触发条件时固定为 `compliant_skip`。

禁止字段或内容：密码、Cookie、session、token、验证码、OTP、MFA、浏览器 Profile 导出、OpenCLI trace。

## 任务状态

每个轮次和总体运行只能使用以下状态。

| 状态 | 含义 | 后续动作 |
| --- | --- | --- |
| `success` | 主证据已采集且所有必需轮次完成。 | 输出报告。 |
| `partial_success` | 有可用证据，但至少一轮失败或未评估。 | 输出报告和精确限制。 |
| `awaiting_human` | 登录、验证码、设备验证或 CDP 授权待用户在本机完成。 | 停止对应采集，等待“已登录”。 |
| `blocked_user_action` | 需要用户操作，但不是登录流程可自动恢复的状态。 | 说明所需动作。 |
| `blocked_dependency` | 本机缺少获准的依赖或配置。 | 说明缺失项；不自动安装。 |
| `compliant_skip` | 条件化工具没有触发条件。 | 保留跳过原因。 |
| `failed` | 已限次尝试仍失败。 | 保存错误、trace 路径和恢复条件。 |

## 文件布局

按日期和独立任务保存证据，避免不同研究对象相互覆盖。

```text
<output-root>/
  raw/<YYYY-MM-DD>/<task-id>/task.json
  raw/<YYYY-MM-DD>/<task-id>/rounds/01-opencli/round_manifest.json
  raw/<YYYY-MM-DD>/<task-id>/rounds/02-last30days/round_manifest.json
  ...
  processed/<YYYY-MM-DD>/<task-id>/summary.json
  reports/<YYYY-MM-DD>-<task-slug>-integrated-scraper.md
```

每个 manifest 至少记录：`round`、`skill`、`task_id`、`status`、
`timestamp`、`target`、`result` 和恢复条件（若不成功）。`summary.json`
至少记录 `task_id`、`target`、`overall_status` 与
`current_primary_evidence`。校验器必须拒绝跨任务的 `task_id` 或
研究对象。

## 证据与隐私

所有报告结论都必须回溯到本次任务的公开证据。

- 每条可报告证据必须有来源 URL、采集时间、采集器、原始公开文本和来源轮次。
- 历史数据必须标为历史基线，不能说成今日新增。
- 公开昵称只能用于去重和人工复核；不能推断姓名、联系方式、采购权或身份。
- 任何主通道空载荷、连接中断、页面壳结构或未渲染评论都表示“未评估”，
  不是“没有内容”。
