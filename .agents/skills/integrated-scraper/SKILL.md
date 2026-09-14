---
name: integrated-scraper
description: 集成 OpenCLI、last30days、last30days-cn、BrowserHarness、Scrapling 和 Cloakbrowser，先把自然语言抓取任务拆成原子需求，再按成功率、数据质量、可用性、登录条件、成本、就绪度、权限风险和历史效果选择最强工具，失败或验收不通过时才降级。用于跨网站、平台、账号、关键词、话题或 URL 采集公开及已授权内容、评论和趋势，保留原始证据并提炼需求、问题、线索和机会；需要登录、验证码或 CDP 授权时由用户在本机项目浏览器完成。
---

# 综合抓取

把多个现成抓取 Skill 作为能力池。围绕用户本次任务选择最合适的执行器，不固定
来源、平台、对象、受益方或工具轮次。默认每个原子需求只运行一个主工具；只有
主工具失败或结果未通过验收时才按排名降级。高风险结论、证据冲突或用户明确
要求时才交叉核验。

始终把真实内容与评论当作证据，把执行动作当作审计记录。空载荷、壳页面、403、
超时或权限阻塞不是“没有数据”。

## 首次初始化

当用户提到“初始化”“新电脑”或本机配置不存在时：

1. 读取项目根目录 `runtime.contract.json`、`dependencies.manifest.json` 和
   `references/collection-contract.md`。
2. 先展示依赖的官方来源、版本、许可证和安装动作；外部安装前取得用户明确确认。
   使用 `scripts/bootstrap_pack.py` 预览项目本地准备动作；详细参数见
   `docs/bootstrap.zh-cn.md`。不得把预览或生成配置当成依赖已安装。
3. 使用固定运行契约，不再询问端口或 Profile：主 Chrome/CDP 为
   `127.0.0.1:9222`，OpenCLI Profile 为 `integrated-scraper-9222`，daemon 为
   `19825`，输出目录为 `D:\integrated-scraper-output`。严禁使用其他项目的
   `9223`。
4. 先预览再创建无凭据本机配置：

   ```powershell
   python .agents/skills/integrated-scraper/scripts/initialize.py
   python .agents/skills/integrated-scraper/scripts/initialize.py --write-config
   ```

5. 初始化阶段运行完整能力库存检查：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_runtime.ps1
   ```

6. 完整能力库存可以报告尚未安装的工具；正式任务是否可执行只取决于该任务计划
   选中的工具。Cloakbrowser 没有明确指纹兼容触发条件时保持
   `compliant_skip`。

## 任务规划

每次调用创建独立 `task_id`，从用户自然语言提取并保存：

- `target`：本次来源和对象。
- `objective`：需要回答的问题。
- `time_range`：用户指定或明确说明的默认时间范围。
- `decision_context`：结果使用者和决策用途；缺失时写 `not_provided`。
- `success_criteria`：整份任务必须满足的交付条件。
- `work_items`：不可再独立验收拆分的原子需求。

每个 `work_item` 必须包含独立 `id`、需求描述、验收标准、风险级别、是否交叉
核验、可执行候选工具和被排除工具。不得沿用上一任务的来源、对象、受益方或结论。

### 路由规则

按以下顺序规划每个原子需求：

1. 先执行硬门槛：工具必须具备对应能力、授权边界允许、能产生验收所需证据且
   当前电脑存在补齐运行条件的路径。未通过者放入 `excluded_tools` 并写明原因。
2. 对剩余工具按 `runtime.contract.json` 的八个维度评分：成功率、数据质量、输出
   直接可用性、浏览器/登录匹配度、成本效率、运行时就绪度、权限风险适配度和
   历史真实效果。
3. 每个已登记工具必须出现在候选或排除列表中，不能因为固定轮次或路由偏好被
   静默忽略。
4. 使用 `scripts/plan_run.py` 生成 `execution_plan.json`；分数第一名为主工具，
   其他工具按得分成为降级顺序。
5. 正常任务只把主工具列入本次必需依赖。高风险、用户要求或证据冲突的任务预先
   选择独立核验工具。

工具能力基线：

| 原子需求 | 首选工具 |
| --- | --- |
| 公开 URL 正文、Sitemap、整站发现、批量页面、结构化字段、自适应选择器 | Scrapling |
| 已有适配器的平台搜索、帖子、评论和业务对象 | OpenCLI |
| 登录核验、点击、滚动、条件切换、页面可见性和截图 | BrowserHarness |
| 近 30 天海外趋势 | last30days |
| 近 30 天中文趋势 | last30days-cn |
| 已明确发生的浏览器指纹、Cloudflare 或兼容问题 | Cloakbrowser |

需要登录交互的页面不要交给 Scrapling；明确指纹兼容问题不要笼统归为普通
Scrapling 反爬；Cloakbrowser 绝不能用于绕过登录、验证码或 MFA。

生成计划后运行任务范围检查：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/invoke_project_python.ps1 .agents/skills/integrated-scraper/scripts/plan_run.py --task <task.json> --output <execution_plan.json>
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_runtime.ps1 -PlanPath <execution_plan.json>
```

未选工具即使缺失也不阻塞任务。计划选中的工具缺依赖时写
`blocked_dependency`；需要登录或 CDP 授权时写 `awaiting_human`。

## 登录待办

续跑前读取 [续跑与内容验收](references/resume-and-quality.md)。复用原目标标签页，
不要用首页通过验证推定搜索/详情页也已通过。中文 BrowserHarness 脚本使用
`invoke_browser_harness.ps1 -ScriptPath <UTF-8脚本>`，不经默认编码管道传输。

只有目标数据确实要求登录且当前会话不可用时才暂停：

1. 记录平台、登录页和用户只需完成的一个动作。
2. 在项目专属浏览器打开登录页，让用户完成登录、验证码、设备验证或 CDP 授权。
3. 不读取或记录密码、Cookie、Token、验证码、MFA 或 Profile 内容。
4. 用户回复“已登录”后复检同一 Profile/CDP，并继续同一 `task_id` 和原子任务。
5. 不用公开弱结果冒充必须登录才能取得的数据；如果不登录也能完整满足验收，
   则不制造登录步骤。

## 执行与降级

1. 每个原子任务先执行 `primary_tool`。每次尝试独立写
   `execution_manifest.json`，记录工具、顺序、状态、结果和是否通过验收。
2. 工具命令返回成功不代表原子任务成功。只有结果满足该项全部
   `acceptance_criteria` 才设置 `acceptance_passed=true`。
3. 主工具执行失败或验收失败时先定位根因；单工具最多恢复两次。仍不通过才按
   `fallback_tools` 顺序切换。
4. 降级前只检查即将使用的工具及辅助依赖，例如：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/invoke_project_python.ps1 .agents/skills/integrated-scraper/scripts/pack_doctor.py --config config/collection.local.json --plan <execution_plan.json> --work-item <work-id> --require-tool <fallback-tool>
   ```

5. 主工具通过验收后停止该原子任务；没有交叉核验要求时禁止再运行其他工具。
6. 只有一个工具可完成需求时，执行到通过验收；缺依赖则申请补齐，需登录则暂停
   等待用户，限次恢复仍失败则保留明确阻塞，绝不拿较弱结果冒充成功。
7. 所有浏览器控制器严格串行，同一时间只允许一个控制器操作项目 Chrome。

所有 OpenCLI 调用通过 `scripts/invoke_opencli.ps1` 并显式使用
`integrated-scraper-9222`。BrowserHarness 通过 `scripts/invoke_browser_harness.ps1`
连接固定 `9222`。项目 Python、Playwright、Scrapling 和 yt-dlp 通过项目独立入口。
YouTube 评论必须保留明确 `comment_count` 或可见零结果证据；OpenCLI 空数组不能
单独证明评论为零。

Python 代码需要控制项目 Chrome 时，必须在 `invoke_project_python.ps1` 后加
`-BrowserControl`。此入口与 OpenCLI/BrowserHarness 共用跨进程锁；忙碌时明确报错，
不得另开绕过锁的控制器。锁覆盖当前命令生命周期，不允许命令返回后遗留后台控制器。

恢复上限指首次实际执行后最多两次恢复（合计三次）；未执行工具的依赖/人工阻塞
不计入执行次数。人工待办后只能先复检同一工具，续跑记录附 `resume`，再决定结果。

执行状态允许：`success`、`empty_verified`、`partial_success`、
`awaiting_human`、`blocked_user_action`、`blocked_dependency`、`unassessed` 和
`failed`。未选工具不生成执行状态，只在计划中保留排除理由。

## 分析、报告与验收

每次交付必须同时提供两份独立文件：分析报告.md 和源数据.md，不能以原始JSON、
链接清单或报告中的精选引文代替源数据文档。源数据涵盖本次已采正文、评论、
楼中楼、弹幕等内容；不因缺少分析价值、时间较旧或日期待确认而静默删去。
排版按平台和来源页面分组，原文不润色；重复免责声明只在文首说明一次，
采集时间、文件路径和SHA256集中到文末索引。具体记录规范见下方引用。

评论采集和原文文档交付须读取 [续跑与内容验收](references/resume-and-quality.md)，
使用 `collection_quality.py` 做格式解析、数量核对与原文渲染。新评论采集尝试
保存数量检查输入并通过 `result.collection_check.evidence_id` 接入验收；不得
把工具退出成功或结构校验通过当成内容完整。旧任务不补造字段或修改原始证据。

只将明确的第一人称使用、故障、选型、价格、试用、部署或替代诉求归为需求或
线索。公开昵称不是身份、采购权或联系方式。机会判断必须围绕本次
`decision_context`；缺少业务视角时输出中性机会。

报告按以下顺序输出：

1. 已证实的需求、机会和可执行建议。
2. 来源原话、URL、时间、采集器和置信度。
3. 已确认、推断、待确认和未评估边界。
4. 原子任务状态、实际使用工具、降级记录、覆盖范围、限制、人工待办和本地路径。

使用短句和常用词，先结论后证据；不使用执行日志代替结果。humanizer 只调整
说明文字，不改写原始证据、URL、状态或机器字段。

只有页面或接口正常完成采集并明确显示零条时才允许 `empty_verified`。空数组、
空正文、超时、403、登录墙、解析失败或浏览器错位必须是 `unassessed`、失败或
阻塞。

总体状态按原子需求验收计算：全部通过为 `success`；部分通过为
`partial_success`；全部未通过时保留真实阻塞或失败状态。主工具失败但降级工具
通过验收，不降低最终业务状态，但必须保留失败记录。

运行结束前执行：

```powershell
& ./.agents/skills/integrated-scraper/scripts/invoke_project_python.ps1 -PythonArguments @('.agents/skills/integrated-scraper/scripts/validate_run.py','--run-dir','<本次raw任务目录>','--summary','<summary.json>','--final-delivery','--analysis-report','<分析报告.md>','--source-document','<源数据.md>','--source-records','<源内容清单.json>')
```

校验未通过不得声明完成。不得自动发布、私信、评论、关注、购买、修改账号、
安装依赖或启动定时任务；这些动作需要用户单独确认。

新运行须使用当前计划生成器保存任务/契约指纹。每条证据附相对文件路径、SHA256、
来源 URL 和采集时间；每条验收标准附证据 ID 和判断理由。完整格式见采集契约。
旧运行记录保持原样，不补造证据、不覆盖历史报告；不满足新契约的旧数据只能标为
历史未重新验收。离线校验验证文件完整性和记录一致性，不代替对原文的真实性、
覆盖范围、登录墙/壳页面和结论质量的内容复核。

## 资源

- 读取 `references/collection-contract.md` 确定计划、状态、证据和隐私契约。
- 读取 `dependencies.manifest.json` 确定依赖来源和安装确认边界。
- 读取 `runtime.contract.json` 作为端口、路径、能力、评分和版本真源。
- 使用 `scripts/plan_run.py` 生成并验证动态执行计划。
- 使用 `scripts/start_runtime.ps1 -PlanPath` 和 `scripts/pack_doctor.py --plan`
  进行任务范围检查。
- 使用固定 `invoke_*.ps1` 入口执行浏览器、OpenCLI 和项目 Python 工具。
- 使用 `scripts/validate_run.py` 验证原子需求、执行顺序、降级和总体状态。
