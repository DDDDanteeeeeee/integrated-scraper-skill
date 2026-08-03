# 当前任务进度

## 目标

在不新增平台系统化逻辑、不改变现有六轮抓取工作流的前提下，把项目定位、
Skill 名称和交付材料统一为通用的 `integrated-scraper` 综合抓取能力。

## 当前状态

- 用户已确认 Skill 调用名 `integrated-scraper`、仓库名
  `integrated-scraper-skill` 和中文名“综合抓取”。
- 已把项目级 Skill 文件夹和元数据从 `douyin-intelligence` 改为
  `integrated-scraper`。
- 已保持六轮顺序、状态枚举、依赖检查、人工登录和证据安全边界不变。
- 已明确不新增强制 `platform` 字段、平台注册表、平台适配器或账号管理逻辑。
- 已把输出契约中的 `current_douyin_primary_evidence` 改为通用的
  `current_primary_evidence`，语义仍是总体成功必须有本次主证据。
- README、交付手册、依赖清单、配置样例和测试已完成本地定位改写；抖音与 X
  仅保留为明确标注的任务示例。
- 19 项单元测试已通过；8 个 Markdown 文件的代码围栏和相对链接检查通过，
  `git diff --check` 通过。
- 示例配置的全量检查正确返回 `blocked_dependency`，不会把占位 OpenCLI、
  BrowserHarness 或 Scrapling 误判为可抓取状态；Cloakbrowser 正确保持
  `compliant_skip`。
- 官方 `quick_validate.py` 因当前 Codex 内置 Python 缺少 PyYAML 而未执行
  完成；元数据单元测试已覆盖其名称、frontmatter 字段、长度和字符约束。
- 定位改动已提交到 `agent/integrated-scraper-positioning`；GitHub 推送和仓库
  更名因现有 `gh` 授权令牌失效而暂停，已打开可见的设备授权窗口等待用户完成。
- 远程仓库仍为 `douyin-intelligence-skill`；草稿 PR #1 基于旧定位，尚未处理。

## 下一步

1. 用户完成 GitHub 设备授权后复检 `gh auth status`。
2. 将 GitHub 仓库更名为 `integrated-scraper-skill`，同步本机 `origin` 并推送
   当前分支。
3. 处理旧草稿 PR #1，并确认新提交的 GitHub Actions 状态。
4. 后续在具备 PyYAML 的环境补跑官方 `quick_validate.py`。
