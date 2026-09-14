# AGENTS.md

## 项目定位与边界

- 默认使用中文与用户沟通。
- 本仓库只维护项目级 Codex Skill `integrated-scraper`，不开发独立前端、控制平面、云服务、平台账号系统或平台适配器体系。
- 用户每次用自然语言指定目标来源、对象、时间范围和用途；不得把 Magewell、抖音、X、Facebook、YouTube、Reddit 或其他历史任务写成默认目标或产品边界。
- 只读抓取公开信息或用户已获授权访问的信息；不得自动发布、评论、私信、关注、购买或修改账号设置。
- 绝不收集、输出、提交或同步密码、Cookie、验证码、MFA、Token 或浏览器 Profile。原始公开评论、OpenCLI trace、本地配置和本地报告不得提交到 GitHub。
- 登录、验证码、设备验证和 CDP 授权只能由用户在本机项目专属浏览器中完成；遇到这些状态必须进入 `awaiting_human`，用户完成后继续同一 `task_id`。

## 固定运行契约

`runtime.contract.json` 是机器可读的唯一运行参数真源。任何任务、脚本或 Agent 都不得临时覆盖以下设置：

| 项目 | 固定值 |
| --- | --- |
| 操作系统 | Windows |
| 项目 Chrome | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| Chrome CDP 地址 | `127.0.0.1` |
| Chrome CDP 端口 | `9222` |
| Chrome CDP URL | `http://127.0.0.1:9222` |
| Chrome Profile | `<repo>\runtime\chrome-public-profile` |
| 禁止使用的端口 | `9223`，该端口属于汽水项目 |
| OpenCLI 固定 Profile | `integrated-scraper-9222` |
| OpenCLI daemon | `19825` |
| OpenCLI cache | `<repo>\runtime\opencli-cache` |
| OpenCLI 窗口模式 | `background` |
| OpenCLI 连接超时 | `45` 秒 |
| OpenCLI 命令超时 | `60` 秒 |
| OpenCLI 输出格式 | `json` |
| OpenCLI trace | 仅失败时保留 |
| OpenCLI 页面会话 | `persistent`，保留任务标签页 |
| Facebook 群组批次 | 每批 `20` 个 |
| BrowserHarness CDP | `http://127.0.0.1:9222` |
| BrowserHarness workspace | `<repo>\runtime\browser-harness-workspace` |
| BrowserHarness domain skills | 关闭 |
| 项目 Python | `<repo>\runtime\python-env\Scripts\python.exe` |
| Playwright 浏览器 | `<repo>\runtime\ms-playwright` |
| Scrapling 入口 | `<repo>\runtime\bin\scrapling-project.cmd` |
| yt-dlp 入口 | `<repo>\runtime\bin\yt-dlp.cmd` |
| Cloakbrowser 模式 | `conditional` |
| Cloakbrowser CDP | `http://127.0.0.1:9242` |
| 浏览器控制并发 | `execution.browser_controller_concurrency=1`，所有浏览器控制器严格串行 |
| 本地数据输出 | `D:\integrated-scraper-output` |

- 禁止随机端口、自动递增端口、冲突后静默换端口、借用其他项目端口或关闭其他项目进程。
- 启动前必须检查 `9222` 的占用者和 Chrome Profile 所有权；如果被非本项目进程占用，停止并报告。
- 本项目不得连接、占用、关闭或修改 `9223` 的进程。
- Cloakbrowser 只有出现明确的指纹、Cloudflare 或反自动化兼容错误时才能使用 `9242`；不得用于绕过登录、验证码或 MFA。无触发条件时状态必须为 `compliant_skip`。
- OpenCLI 的稳定标识是固定别名 `integrated-scraper-9222`。contextId 由本机扩展产生，任务脚本不得依赖旧电脑的随机 contextId；扩展安装后必须把本机 contextId 绑定到同一固定别名。
- 不得修改 OpenCLI 全局默认 Profile；所有调用都必须通过项目入口显式选择 `integrated-scraper-9222`。
- 不得在任务执行中移动或重命名仓库。仓库路径变化后必须重新生成本机配置并完成全量验收，不能继续使用旧绝对路径。

## 固定版本验收基线

Chrome 一栏是历史验证记录，不是要求每台电脑安装同一版本。新电脑在初始化时
确认本机 Chrome 路径和实际版本，完成连接、页面读取及本次所需工具验收后再使用。
浏览器升级后重新做兼容验证，不自动降级浏览器，也不凭版本号相同宣称兼容。
当前电脑已登记端口/Profile仍固定，不因浏览器版本变化调整。

| 组件 | 已验收版本 |
| --- | --- |
| Chrome | `151.0.7922.108` |
| Node.js | `24.15.0` |
| OpenCLI | `1.8.6` |
| OpenCLI Browser Bridge | `1.0.24` |
| BrowserHarness | `0.1.8` |
| last30days | `3.3.2` |
| last30days-cn | `3.0.0-cn` |
| Python | `3.13.13` |
| Scrapling | `0.4.13` |
| Playwright | `1.62.0` |
| yt-dlp | `2026.07.04` |

- 依赖来源、许可证、安装动作和确认边界以 `dependencies.manifest.json` 为准。
- 不得静默升级、降级或改用全局依赖。版本发生变化时，先停止任务，重新验证，再经用户确认更新 `runtime.contract.json`、本文件和测试。
- 在未获得用户逐项确认前，不执行任何新的上游安装动作。

## 固定启动与调用入口

- 初始化或完整能力库存检查运行：

  ```powershell
  powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_runtime.ps1
  ```

- 每次正式任务先生成 `execution_plan.json`，再运行任务范围检查：

  ```powershell
  powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_runtime.ps1 -PlanPath <execution_plan.json>
  ```

- 只有任务范围检查返回 `success` 才能执行计划中的主工具。未选工具的缺失或未登录不得阻塞本次任务；`awaiting_human`、`blocked_dependency`、`invalid_config` 和 `failed` 都不是成功。
- OpenCLI 必须通过 `.agents/skills/integrated-scraper/scripts/invoke_opencli.ps1` 调用。
- BrowserHarness 必须通过 `.agents/skills/integrated-scraper/scripts/invoke_browser_harness.ps1` 调用。
- Playwright 或其他项目 Python 任务必须通过 `.agents/skills/integrated-scraper/scripts/invoke_project_python.ps1` 调用。
- 不得直接调用全局 OpenCLI 默认 Profile、全局 Python、全局 Playwright 浏览器缓存或其他项目的浏览器。
- `config/collection.local.json` 只保存当前电脑的无凭据绝对路径，并被 Git 忽略；不得手工加入密码、Cookie、session、Token 或验证码。

## 动态采集与报告规则

- 每次任务先拆成可独立验收的原子需求，再按 `runtime.contract.json` 对全部工具执行硬门槛和八维评分。每个工具必须进入候选或排除列表并写明理由。
- 默认每个原子需求只执行得分最高的主工具；只有执行失败或结果未通过验收时才按排名降级。高风险、用户明确要求或证据冲突时才交叉核验。
- 未选工具不生成执行 manifest、不阻塞任务，也不影响总体状态。每次实际尝试必须独立记录 `execution_manifest.json`，不得把一个工具的结果冒充另一个工具成功。
- Scrapling 优先处理公开 URL、Sitemap、批量公开页面、结构化字段和自适应选择器；OpenCLI 优先处理已有适配器的平台业务对象；BrowserHarness 负责登录交互和页面可见验收；last30days 系列负责近期趋势；Cloakbrowser 只处理明确指纹兼容问题。
- 单工具最多恢复两次；通过验收后立即停止。切换降级工具前只检查该工具及辅助依赖。
- 恢复两次是首次实际执行加两次恢复；人工/缺依赖待办不计执行次数。新记录按当前证据契约验收，历史记录不补造证据。
- Python 控制项目 Chrome 时调用 `invoke_project_python.ps1 -BrowserControl`；锁覆盖命令生命周期，禁止后台控制器在命令结束后继续操作浏览器。
- 新计划绑定任务/运行契约指纹；成功必须关联非空原始证据文件、SHA256、来源、采集时间及逐项验收理由。机器校验不替代内容复核。
- 空数组、空正文、超时、403、权限不足、解析失败、登录墙、页面未渲染或浏览器错位都不是“没有数据”。只有页面或接口正常完成采集并明确显示 0 条时才允许使用 `empty_verified`。
- 报告先写实际需求、机会和可执行结论，再写来源、原话、URL、时间、原子任务与执行器状态、覆盖范围和限制；不得用执行日志代替情报内容。
- 总体状态只按原子需求验收计算。主工具失败但降级工具通过验收时可保持业务 `success`，同时保留失败审计记录。
- 运行结束前必须使用 `validate_run.py --run-dir` 验证计划、执行顺序、降级、证据和总体状态；未通过不得声明任务完成。

## 开发与发布验收

- 正式任务必交付独立的分析报告和源数据MD。源数据覆盖全部已采内容，原文不改写；
  公共说明只写一次，采集时间与校验信息集中索引。最终运行validate_run.py时必须
  使用--final-delivery及两份文档、源内容清单参数，不能用仅结构检查代替交付验收。

- 修改 Skill、运行脚本、运行契约或状态逻辑后，执行对应单元测试、PowerShell 语法检查、`git diff --check` 和可用的 `quick_validate.py`。
- 运行时代码或依赖入口变化时，必须补充与风险匹配的真实本机 smoke test；只有静态检查不能声明运行链路可用。
- GitHub 发布前检查 `.gitignore`、工作树、测试、Skill 验证和敏感信息；未经用户明确最终确认不得提交、推送、创建或合并 PR。
