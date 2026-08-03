# 问题与风险

## 当前风险

- 当前 Codex 内置 Python 缺少 PyYAML，官方 `quick_validate.py` 尚未补跑；
  19 项单元测试和其中的元数据约束测试已经通过。
- 已安装旧调用名的电脑需要更新仓库并重启 Codex；现有本机配置和历史输出
  不会自动改名或迁移。
- `current_primary_evidence` 是对旧输出键
  `current_douyin_primary_evidence` 的通用化改名；旧运行目录不应在没有迁移的
  情况下用新版校验器重新声明为成功。
- OpenCLI Profile 可能失效或连接中断；空载荷必须标为未评估，不得声称无变化。
- BrowserHarness 本机后台可能在单次调用后超时；不得把该故障归为登录失败或
  内容不存在。
- 原始评论可能包含公开昵称和业务表述，属于本地运行数据，不得进入 GitHub。
- 外部依赖的安装方式、版本和许可证可能变化；运行时仍须以依赖清单和上游
  官方说明为准，并在安装前取得用户确认。

## 已处理问题

- GitHub CLI 在受限网络环境中曾把 API 不可达误报为令牌无效；在获准的联网
  环境中复检后确认授权有效，并已完成仓库更名、推送和 PR 操作。
- GitHub 连接器对该仓库返回 `403 Resource not accessible by integration`；
  已按发布 Skill 的回退规则使用已授权 GitHub CLI 完成旧 PR 关闭和新 PR 创建。
- 旧草稿 PR #1 已关闭；新综合抓取定位由 PR #3 承载，避免误合并旧边界。
- 已撤回把目标平台设计成强制字段、平台一致性校验和平台系统命名的错误方向。
- 已将项目定位收窄为综合抓取 Skill，明确不是独立应用或平台管理系统。
- 已移除 Magewell 作为产品定位或默认任务的表达。
- 已保留登录、验证码、MFA、CDP、本机数据和只读抓取安全边界。
- 示例占位配置不会被误判为可用；敏感配置字段会被本机检查拒绝。
- 完整依赖检查继续覆盖 OpenCLI、BrowserHarness、last30days、
  last30days-cn、Scrapling 和条件化 Cloakbrowser。
