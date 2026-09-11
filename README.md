# Integrated Scraper Skill

`integrated-scraper` 是一个供 Codex 调用的项目级综合抓取 Skill。它把
OpenCLI、last30days、last30days-cn、BrowserHarness、Scrapling、yt-dlp 和
Cloakbrowser 组成一个动态能力池。Skill 会先把任务拆成原子需求，再为每项选择
最强工具；只有主工具失败或结果未通过验收时才降级。它从公开来源获取内容与
评论、保留原始证据，并输出结构化数据和基于证据的分析报告。

本项目交付的是抓取能力，不是独立软件、云端控制台、平台管理系统或账号管理
系统。目标网站、平台和抓取对象由用户在每次任务中自然说明；如果目标页面要求
登录，用户只需在本机专属浏览器中登录对应账号，再回到原任务继续执行。

## 从零开始的交付手册

如果你要在一台新 Windows 电脑上交付或使用本项目，请从
[《综合抓取 Skill Pack 新电脑交付与使用手册》](docs/delivery-guide.zh-cn.md)
开始。手册覆盖 Codex 安装、仓库下载、依赖初始化、专属浏览器登录、任务输入、
结果验收、升级、迁移和故障排查。

## 交付能力

用户提供目标来源、抓取对象、时间范围和用途后，Skill 会执行以下工作：

- 把任务拆成可独立验收的原子需求，并比较全部工具的能力、质量、成本、登录
  条件、就绪度、权限风险和历史执行效果。
- 每项默认只执行得分最高的主工具；失败或验收不通过时才按排名降级。
- 获取与当次任务相关的公开页面、内容、评论和近期趋势补充。
- 保存原始公开文本、来源 URL、采集时间、采集器、置信度和实际执行状态。
- 从证据中提取需求、问题、比较、使用场景和机会；执行动作只作为审计记录。
- 面向用户的报告先给结论，再给证据、限制和下一步；使用直接、易懂的语言，原始证据和技术字段保持原样。
- 白话表达只调整说明文字，不改变证据、字段、状态值、表格列、JSON 键或校验文件。
- 空数组或空正文只有在页面明确证明 0 条时才算“无数据”；采集失败导致的空结果必须标为未评估、失败或阻塞。
- 将不同任务保存在独立 `task_id` 下，避免跨任务混用对象、证据或结论。
- 在登录过期、验证码、设备验证或 CDP 未授权时暂停，等待用户完成操作后继续
  同一任务。

Skill 不维护平台白名单、平台注册表、平台适配器体系或账号库。抖音、X、论坛、
新闻网站和产品页面都只是可能的任务来源；实际可抓取范围取决于目标页面的公开
可访问性、已集成工具的能力和用户在本机完成的必要授权。

## 安全与数据边界

以下规则适用于所有目标来源：

- 只读抓取公开或用户已获授权访问的信息。
- 不私信、评论、关注、购买、发布或修改账号设置。
- 不读取、保存或上传密码、Cookie、验证码、MFA、Token 或浏览器 Profile。
- 不绕过登录、验证码或 MFA。出现这些页面时返回 `awaiting_human`。
- 空页面、断连、登录墙或工具阻塞表示“未评估”，不等于“没有内容”。
- 原始证据和报告只写入本机输出目录，例如
  `D:\integrated-scraper-output`，不会写入本仓库或 GitHub。

## 前置条件

当前发行目标为 Windows 10/11、Codex 和 Python 3.12+。安装 last30days
系列还需要 Node.js 与 `npx`。

- 初始化可以检查完整能力库存；正式任务只要求动态计划选中的主工具、交叉核验
  工具及辅助依赖就绪。YouTube 评论必须保留明确的 `comment_count`，不能把
  OpenCLI 空数组当成 0 条评论。
- Cloakbrowser 是条件化依赖，未遇到明确指纹或反自动化兼容错误时保持
  `compliant_skip`。
- 每个需要登录的目标来源使用本机专属浏览器保存登录态。
- 缺少实际需要的组件时，对应原子任务必须标为 `blocked_dependency`，不得用
  其他工具的结果冒充成功。

## 一键初始化

初始化只准备本机执行环境，不预设平台、账号、品牌或研究对象。

稳定版准备器及离线验证说明见 [初始化操作说明](docs/bootstrap.zh-cn.md)。
执行验收使用证据文件、哈希和逐项标准，不再只检查成功标记；旧报告保持原样，
不自动升级为新标准下的成功结果。

1. 安装 Codex，克隆并打开本仓库。
2. 在 Codex 中发送：

   ```text
   @integrated-scraper 初始化这个 Skill Pack。
   ```

3. 查看 Skill 展示的依赖状态、官方来源和安装动作。
4. 对每项外部安装分别确认。端口和 OpenCLI Profile 不再临时填写，项目会按
   固定运行契约准备。
5. 在专属浏览器完成 CDP 授权。
6. 如果目标来源要求登录，在对应页面完成登录或验证码。
7. 输入实际任务。Skill 会生成动态执行计划，并只检查本次选中的工具；未选工具
   不会阻塞任务。

## 任务示例

下面的抖音和 X 任务只演示输入方式，不表示 Skill 仅支持这些平台。

```text
@integrated-scraper
抓取抖音中与“露营投影仪”相关的近 30 天公开内容和评论，找到用户在亮度、
续航和户外连接方面的真实需求，并给出附来源链接的产品机会。
```

```text
@integrated-scraper
抓取 X 上最近 14 天关于“wireless video latency”的公开讨论，区分真实使用
问题、方案比较和普通转发，并输出证据表和机会摘要。
```

```text
@integrated-scraper
抓取我提供的产品页面、帮助中心和公开论坛链接，整理反复出现的安装问题，
保留原文与 URL，并生成供客服团队使用的 FAQ 机会清单。
```

## 高级：非交互初始化

固定参数见 [`runtime.contract.json`](runtime.contract.json) 和
[《固定运行参数》](docs/runtime-parameters.zh-cn.md)。第一条命令只预览，第二条
才写入本机配置：

```powershell
python .agents/skills/integrated-scraper/scripts/initialize.py
python .agents/skills/integrated-scraper/scripts/initialize.py --write-config
```

随后检查整个 Skill Pack：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_runtime.ps1
```

正式任务会先创建 `task.json` 和 `execution_plan.json`，再执行任务范围检查：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/invoke_project_python.ps1 .agents/skills/integrated-scraper/scripts/plan_run.py --task <task.json> --output <execution_plan.json>
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_runtime.ps1 -PlanPath <execution_plan.json>
```

本项目运行时固定使用仓库内的 `runtime/chrome-public-profile`、OpenCLI Profile
`integrated-scraper-9222` 和本机 `http://127.0.0.1:9222`。`9223` 明确保留给
其他项目，脚本不会连接、关闭或复用它。需要单独重新打开浏览器时运行：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_project_chrome.ps1
```

脚本发现 9222 被其他 Chrome 占用时会停止并提示，不会关闭其他项目的浏览器。

## 依赖分发

所有执行依赖都写入
[`dependencies.manifest.json`](dependencies.manifest.json)。本仓库不复制
第三方二进制，也不会自动安装。

| 依赖 | 获取方式 | 初始化时的处理 |
| --- | --- | --- |
| OpenCLI | 使用者已获授权的本机安装 | 仅验证命令和 Profile，不迁移账号或 Profile。 |
| BrowserHarness | [上游项目](https://github.com/browser-use/browser-harness)（MIT） | 用户确认后按上游 `install.md` 安装；CDP 授权仍由用户完成。 |
| last30days | [上游项目](https://github.com/mvanhorn/last30days-skill)（MIT） | 用户确认后按上游 `npx skills add` 安装。 |
| last30days-cn | [上游项目](https://github.com/Jesseovo/last30days-skill-cn)（MIT） | 用户确认后安装公开 Skill；不配置其可选 API 凭据。 |
| Scrapling | [官方文档](https://scrapling.readthedocs.io/en/latest/)（BSD-3-Clause） | 用户确认后在隔离虚拟环境安装；不传 Cookie、代理凭据或 API Key。 |
| yt-dlp | [上游项目](https://github.com/yt-dlp/yt-dlp)（Unlicense） | 用户确认后安装到项目独立 Python 环境，用于 YouTube 搜索、字幕和评论计数。 |
| Cloakbrowser | [官方渠道](https://cloakbrowser.dev/) | 只在明确兼容错误时提示用户自行获取；不得捆绑、预装或重分发。 |

## 分发边界

本仓库分发主 Skill、初始化器、安装清单、检查脚本、配置样例和采集契约。
`dependencies.manifest.json` 声明外部依赖的来源、许可证、版本策略和确认
边界，不复制或静默安装第三方组件。所有 `data/`、`reports/`、浏览器
Profile、OpenCLI trace、本地配置和账号会话均为本机数据，禁止提交。

## 发布状态

本项目以 [MIT License](LICENSE) 公开发布。MIT 仅适用于本仓库自身的代码与
文档；外部执行依赖仍按其各自来源、许可证和安装条款处理。
