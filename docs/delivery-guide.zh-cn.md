# 综合抓取 Skill Pack 新电脑交付与使用手册

这份手册面向第一次接触 Codex 的使用者。你可以从一台没有安装
Codex、Git、Python 和 Node.js 的 Windows 电脑开始，完成项目下载、本机
依赖配置、目标账号登录、首次抓取任务和结果验收。

完成本手册后，你会得到一个由 Codex 驱动的本机工作流。你在 Codex
中输入每次不同的目标来源、抓取对象和用途，项目内的
`@integrated-scraper` Skill 负责检查环境、调用六种抓取能力、保存公开证据，
并输出结构化数据和基于证据的报告。

<!-- prettier-ignore -->
> [!IMPORTANT]
> 交付物是一个集成多个抓取 Skill 的综合抓取 Skill，不是平台系统。它固定
> 抓取、证据、安全和审计规则，不固定网站、平台、品牌、账号、关键词、受益
> 公司或分析结论。后文出现的抖音、X 和其他来源都只是任务示例。

<!-- prettier-ignore -->
> [!IMPORTANT]
> “一键初始化”表示 Codex 会检查环境、说明缺失项、给出官方安装动作，
> 并在获得你的确认后继续。它不代表绕过软件安装确认、账号登录、验证码、
> CDP 授权或 OpenCLI Profile 交付。

## 模块一：先确认这套交付能做什么

当前交付是一个项目级 Codex Skill Pack。它不是独立桌面软件、云端控制台、
平台管理系统、账号管理系统或平台注册表。

### 1.1 交付后的完整能力

完成初始化后，你可以执行以下工作：

- 用自然语言指定网站、平台、账号、品牌、产品、关键词、话题或具体 URL。
- 每次指定不同的分析目标、时间范围、业务视角和成功条件。
- 读取与当次任务相关的公开页面、内容和可见公开评论。
- 从公开内容中提取真实使用场景、故障、选型、价格、试用、部署和替代需求。
- 按你本次指定的决策场景识别产品、销售、内容或市场机会。
- 按原子需求动态选择最强工具，并保留实际执行状态、来源、时间和恢复条件。
- 将原始证据、处理中间文件和专业报告保存在指定的本机目录。
- 在登录过期或出现验证码时暂停，等你完成操作后继续同一个任务。
- 根据目标来源选择已集成工具能够执行的抓取路径，不要求你配置平台适配器。

### 1.2 当前交付明确不做的事情

这套 Skill Pack 不会执行以下动作：

- 不读取、保存或上传密码、Cookie、验证码、MFA、Token 或浏览器 Profile。
- 不自动私信、评论、关注、购买或修改平台账号设置。
- 不把空页面、断连、登录墙或工具阻塞写成“没有变化”。
- 不在未确认的情况下安装外部软件或扩大系统权限。
- 不自动创建每 24 小时运行一次的定时任务。

<!-- prettier-ignore -->
> [!NOTE]
> 当前版本先保证“人工启动一次任务，完整跑通并得到可信报告”。定时任务要在
> 新电脑完成真实验收后单独配置，并再次确认运行时间、登录恢复和失败通知规则。

### 1.3 使用者和交付方分别准备什么

交付前先明确责任边界，能避免使用者下载项目后卡在账号或专有依赖上。

| 项目 | 由谁准备 | 验收标准 |
| --- | --- | --- |
| Windows 电脑 | 使用者 | Windows 11 推荐；Windows 10 需为较新版本。 |
| Codex 桌面应用 | 使用者 | 能登录并打开本地项目目录。 |
| Git、Python、Node.js | 使用者或 IT | 命令行版本检查成功。 |
| OpenCLI 命令 | 交付方或获授权管理员 | 本机能执行 OpenCLI。 |
| OpenCLI Profile | Codex 按项目契约绑定 | 固定别名为 `integrated-scraper-9222`，不接收密码或 Cookie。 |
| 目标账号登录 | 使用者 | 在需要登录的目标页面中人工完成。 |
| 验证码、设备验证 | 使用者 | 只在平台页面中操作。 |
| 抓取任务 | 使用者 | 每次说明来源、对象、时间范围和结果用途。 |

<!-- prettier-ignore -->
> [!WARNING]
> OpenCLI 是主采集通道，但它不是本仓库可再分发的软件。交付方必须另外提供
> 已获授权的 OpenCLI 安装方式。项目 Chrome 连接后，由 Codex 将该连接绑定为
> 固定别名 `integrated-scraper-9222`。缺少安装或固定连接时，环境检查会返回
> `blocked_dependency`，这是正确结果。

## 模块二：安装 Codex 和基础工具

推荐新手使用 Windows 桌面应用。它提供项目选择、聊天、终端、文件预览、
权限确认和 Skill 发现界面，比从纯命令行开始更直观。

### 2.1 检查 Windows 版本

执行以下步骤确认电脑符合基础要求：

1. 按 `Win + R`。
2. 输入 `winver`。
3. 按 Enter。
4. 确认系统为 Windows 11，或已完全更新的 Windows 10。

OpenAI 当前推荐 Windows 11。Windows 10 属于尽力支持，实际使用至少需要
版本 1809 或更新版本。企业电脑还可能受到管理员策略限制。

### 2.2 安装 Codex 桌面应用

你可以使用图形安装或 PowerShell 安装，二选一即可。

**方式 A：使用官方安装页面**

1. 打开
   [OpenAI 官方 Windows 应用下载页](https://get.microsoft.com/installer/download/9PLM9XGG6VKS?cid=website_cta_psi)。
2. 按页面提示安装应用。
3. 安装完成后，从 Windows **开始**菜单打开 ChatGPT。
4. 进入应用中的 **Codex** 工作区。

**方式 B：使用 PowerShell**

1. 打开 PowerShell。
2. 运行：

   ```powershell
   winget install --id 9PLM9XGG6VKS -s msstore
   ```

3. 等待安装完成。
4. 从 Windows **开始**菜单打开应用。

<!-- prettier-ignore -->
> [!NOTE]
> OpenAI 官方手册把它称为“ChatGPT desktop app”，应用中的本地项目工作区
> 是 Codex。本手册后文统一称为“Codex 桌面端”。

### 2.3 登录 Codex

Codex 本地工作支持 ChatGPT 登录或 API Key 登录。对普通使用者，推荐使用
ChatGPT 账号登录。

1. 在未登录页面选择 **Continue to sign in**。
2. 在打开的浏览器中登录 ChatGPT。
3. 如果账号属于多个工作区，选择有 Codex 使用权限的工作区。
4. 返回桌面应用。
5. 打开个人资料菜单，确认账号和工作区正确。

<!-- prettier-ignore -->
> [!IMPORTANT]
> 截图中的“必须购买 ChatGPT Plus”已经不是准确的通用要求。Codex 可用性取决于
> 当前 ChatGPT 方案、工作区权限或 API Key。不要在交付文档中固定承诺某个套餐。
> 以 [OpenAI 当前方案说明](https://learn.chatgpt.com/docs/pricing) 为准。

如果普通浏览器登录无法返回 Codex，可以在 Codex CLI 中使用设备码登录：

```powershell
codex login --device-auth
```

完整认证说明见
[OpenAI Codex authentication](https://learn.chatgpt.com/docs/auth)。

### 2.4 安装 Git、Node.js 和 Python

本项目需要 Git 获取代码，需要 Python 3.12 或更高版本运行本机检查脚本，
需要 Node.js 和 `npx` 安装 last30days 系列 Skill。

在 PowerShell 中依次运行：

```powershell
winget install --id Git.Git -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Python.Python.3.12 -e
```

安装完成后，关闭并重新打开 PowerShell，再运行：

```powershell
git --version
node --version
npm --version
python --version
```

预期结果如下：

- `git --version` 显示 Git 版本。
- `node --version` 显示 Node.js 版本。
- `npm --version` 显示 npm 版本。
- `python --version` 显示 Python 3.12 或更高版本。

如果 `python` 命令不可用，再运行：

```powershell
py -3.12 --version
```

如果该命令成功，后文所有以 `python` 开头的命令都可以替换为
`py -3.12`。

### 2.5 可选安装 Codex CLI

桌面端已经足够使用本项目。只有在你还想从纯终端调用 Codex 时，才安装
Codex CLI。

```powershell
npm install --global @openai/codex
codex --version
codex login
```

如果 PowerShell 报告 `npm.ps1` 或 `npx.ps1` 被执行策略阻止，改用：

```powershell
npm.cmd install --global @openai/codex
```

### 2.6 保留安全确认

打开项目后，Codex 可能请求读取、写入、联网或运行安装命令。你必须检查动作
目标，再决定是否允许。

推荐采用以下原则：

- 保持 **Ask for approval**，不要长期使用全访问模式。
- 只允许当前项目目录和明确的本机输出目录。
- 安装依赖时，核对来源是否与
  [`dependencies.manifest.json`](../dependencies.manifest.json)
  一致。
- 登录、验证码和 MFA 只在平台页面中输入。
- 不把 `%USERPROFILE%\.codex\auth.json` 上传到聊天、工单或 GitHub。

OpenAI 的 Windows 安全说明见
[Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)。

## 模块三：下载并打开项目

项目已经发布在公开 GitHub 仓库。下载代码不需要 GitHub 登录，也不需要
配置 API Key。

### 3.1 创建本机项目目录

在 PowerShell 中运行：

```powershell
$projectParent = Join-Path $env:USERPROFILE "Documents\CodexProjects"
New-Item -ItemType Directory -Force -Path $projectParent
Set-Location $projectParent
```

预期结果是进入：

```text
C:\Users\<你的Windows用户名>\Documents\CodexProjects
```

### 3.2 克隆公开仓库

运行：

```powershell
git clone https://github.com/DDDDanteeeeeee/integrated-scraper-skill.git
Set-Location .\integrated-scraper-skill
```

确认当前目录：

```powershell
Get-Location
git status -sb
```

预期结果是：

- 当前目录以 `integrated-scraper-skill` 结尾。
- Git 分支为 `main`。
- 工作树没有未提交改动。

### 3.3 检查关键文件

运行：

```powershell
Test-Path .\README.md
Test-Path .\dependencies.manifest.json
Test-Path .\.agents\skills\integrated-scraper\SKILL.md
```

三条命令都必须返回 `True`。

关键目录结构如下：

```text
integrated-scraper-skill/
├── .agents/
│   └── skills/
│       └── integrated-scraper/
│           ├── SKILL.md
│           ├── agents/
│           ├── references/
│           └── scripts/
├── config/
│   └── collection.example.json
├── docs/
│   └── delivery-guide.zh-cn.md
├── tests/
├── dependencies.manifest.json
├── README.md
└── LICENSE
```

### 3.4 在 Codex 中打开项目

执行以下步骤：

1. 打开 Codex 桌面端。
2. 按 `Ctrl + O`，或选择 **Add new project**。
3. 选择刚才克隆的 `integrated-scraper-skill` 文件夹。
4. 确认窗口中的项目根目录就是该文件夹。
5. 如果 Codex 请求信任项目，先检查仓库地址和关键文件，再确认。

Codex 从项目根目录的 `.agents/skills` 发现仓库级 Skill。官方规则见
[Build skills](https://learn.chatgpt.com/docs/build-skills)。

### 3.5 确认 Skill 已被发现

在新聊天的输入框中输入 `@`，搜索：

```text
integrated-scraper
```

如果列表中出现 **综合抓取**，说明项目级 Skill 已加载。

如果没有出现：

1. 确认打开的是仓库根目录，不是它的父目录。
2. 确认
   `.agents\skills\integrated-scraper\SKILL.md`
   存在。
3. 关闭项目后重新打开。
4. 仍未出现时，完全退出并重启 Codex。

在 Codex CLI 或 IDE 扩展中，可以运行 `/skills`，或使用
`$integrated-scraper` 显式调用。

## 模块四：理解动态工具工作流

首次初始化负责建立可信的本机运行条件和完整能力库存。正式任务不会要求所有
工具同时运行或同时就绪，只检查本次计划真正选择的工具。

### 4.1 从原子需求到最强工具

每次业务任务采用以下流程：

```text
理解任务
   ↓
拆成可独立验收的原子需求
   ↓
排除能力、授权或证据不匹配的工具
   ↓
按成功率、数据质量、可用性、登录条件、成本、就绪度、风险和历史效果评分
   ↓
只执行第一名
   ↓
结果通过验收？── 是：停止该项
   │
   否
   ↓
按排名切换下一工具
```

每个工具都必须在计划中标为“候选”或写明“排除原因”。未选工具不会执行，也
不会因为缺失而把任务变成失败。一个工具失败时，不能把另一个工具的结果写成
它的成功；但降级工具真实通过验收后，原子需求可以成功，同时保留前一次失败记录。

### 4.2 依赖角色

依赖清单是
[`dependencies.manifest.json`](../dependencies.manifest.json)。
初始化时以该文件为准。

| 依赖 | 任务中何时必需 | 作用 | 初始化行为 |
| --- | --- | --- | --- |
| OpenCLI | 被选中处理已有平台适配器对象时 | 平台搜索、帖子和评论 | 只检查，不由仓库安装。 |
| BrowserHarness | 被选中处理登录交互或页面可见验收时 | 登录、点击、滚动、截图 | 确认后按上游安装。 |
| last30days | 被选中处理海外近 30 天趋势时 | 海外趋势研究 | 确认后安装 Skill。 |
| last30days-cn | 被选中处理中文近 30 天趋势时 | 中文趋势研究 | 确认后安装 Skill。 |
| Scrapling | 被选中处理公开网页、整站或结构化字段时 | 公开网页抓取 | 确认后在隔离环境安装。 |
| yt-dlp | 计划中的 YouTube 原子需求明确需要时 | 字幕和评论计数辅助依赖 | 确认后安装到项目独立 Python 环境。 |
| Cloakbrowser | 条件化 | 指纹兼容问题处理 | 默认不安装、不启动。 |

### 4.3 什么情况下允许开始采集

先生成 `execution_plan.json`，再对计划选择的主工具和辅助依赖执行任务范围检查。
只有该检查返回：

```json
{"status": "success"}
```

才允许开始执行第一个原子需求。

以下结果都表示不能开始：

- `blocked_dependency`：本次选中的软件、命令、Profile 或 Skill 缺失。
- `awaiting_human`：需要登录、验证码、设备验证或 CDP 授权。
- `invalid_config`：本机配置无效或包含禁止字段。

## 模块五：推荐的一键初始化流程

推荐通过 Codex 聊天完成初始化。Codex 会读取仓库内清单和脚本，按当前电脑的
真实状态给出下一步。

### 5.1 发送初始化指令

在已经打开该项目的 Codex 新聊天中，复制并发送：

```text
@integrated-scraper 初始化这个 Skill Pack。

要求：
1. 先检查全部依赖，不要直接开始采集。
2. 展示每个依赖的状态、官方来源和安装动作。
3. 任何外部安装都先向我确认。
4. 不读取或要求密码、Cookie、验证码、MFA 或浏览器 Profile。
5. 如果本机没有 D 盘，先停止初始化并让维护人员准备 D 盘；不要临时更改固定输出路径。
```

### 5.2 识别第一次暂停

如果本机还没有配置，Skill 通常会先返回：

```text
awaiting_human
固定 OpenCLI Profile integrated-scraper-9222 尚未连接
```

这表示项目 Chrome 尚未被 OpenCLI 扩展识别，或者其连接还没有绑定为固定别名。

回复示例：

```text
已在项目 Chrome 中允许远程调试并启用 OpenCLI 扩展，请绑定固定 Profile 后复检。
```

不要输入临时 Profile 名称，也不要把其他项目的 Profile 写进配置。

### 5.3 逐项批准依赖安装

Codex 会列出缺失依赖。每次只批准一个明确目标，回复示例：

```text
允许按 dependencies.manifest.json 中的官方来源安装 BrowserHarness。
安装后运行它的 doctor 检查，不要开始采集。
```

```text
允许安装 last30days 和 last30days-cn 两个公开 Skill。
安装完成后只复检，不要开始业务任务。
```

```text
允许在本项目被 Git 忽略的 runtime 目录中创建独立 Python 环境，
并安装 Scrapling。不要安装到系统 Python。
```

如果 Codex 展示的来源、路径或安装动作与清单不一致，拒绝并要求重新核对。

### 5.4 预览本机配置

初始化器第一次运行只预览，不写文件。预期状态是：

```text
ready_to_write
```

预览内容只允许包含：

- 本机输出目录。
- OpenCLI 命令。
- 固定 OpenCLI Profile `integrated-scraper-9222`。
- 本机 CDP 地址。
- 项目 Python 和 Playwright 浏览器路径。
- Scrapling 可执行文件路径。
- yt-dlp 可执行文件路径。

预览中不得出现密码、Cookie、Token、session、验证码或 MFA。

确认预览正确后回复：

```text
配置预览正确，允许写入 config/collection.local.json。
写入后运行 pack_doctor.py 全量复检。
```

初始化器不会覆盖已存在的 `config/collection.local.json`。

### 5.5 固定输出目录

默认输出目录是：

```text
D:\integrated-scraper-output
```

输出目录属于运行契约，普通任务不能临时改到 C 盘。电脑没有 D 盘时，初始化
应返回阻塞状态，由维护人员先创建或挂载 D 盘，再重新验收。

## 模块六：必要时手工安装和配置依赖

优先让 Codex 按清单引导安装。本模块用于 IT 预装、故障恢复或人工复核，不会
改变“安装前需要确认”的规则。

### 6.1 准备 OpenCLI

OpenCLI 不是本仓库的一部分。交付方需要提供：

1. 获授权的安装包或内部安装方法。
2. 可执行命令名称或绝对路径。
3. 获准访问的目标来源范围。

安装后在 PowerShell 中测试交付方提供的命令。不要在本手册中猜测 OpenCLI
参数，也不要把账号凭据写入 `collection.local.json`。项目 Chrome 启动并被
OpenCLI 扩展识别后，该连接必须绑定为固定别名 `integrated-scraper-9222`；后续
每条 OpenCLI 命令显式传入该 Profile，不修改全局默认 Profile。

### 6.2 安装 BrowserHarness

BrowserHarness 的来源必须是
[browser-use/browser-harness](https://github.com/browser-use/browser-harness)。

1. 按上游仓库的 `install.md` 安装。
2. 完成后运行：

   ```powershell
   browser-harness --doctor
   ```

3. 确认命令存在并能检查本机浏览器。
4. 如果报告 CDP 未授权，继续执行“模块七”。

不要把“BrowserHarness Skill 文件存在”等同于“浏览器已经连接”。项目会同时
检查 Skill、命令和本机 CDP。

### 6.3 安装 last30days

在 PowerShell 中运行：

```powershell
npx skills add mvanhorn/last30days-skill -g
```

如果 `npx.ps1` 被 PowerShell 执行策略阻止，运行：

```powershell
npx.cmd skills add mvanhorn/last30days-skill -g
```

安装后确认文件存在：

```powershell
$last30daysFound = `
  (Test-Path (Join-Path $env:USERPROFILE ".codex\skills\last30days\SKILL.md")) -or `
  (Test-Path (Join-Path $env:USERPROFILE ".agents\skills\last30days\SKILL.md"))
$last30daysFound
```

预期返回 `True`。Codex 会同时检查 `.codex\skills` 和
`.agents\skills` 两个用户级目录。

### 6.4 安装 last30days-cn

在 PowerShell 中运行：

```powershell
npx skills add Jesseovo/last30days-skill-cn -g
```

PowerShell 执行策略阻止时，运行：

```powershell
npx.cmd skills add Jesseovo/last30days-skill-cn -g
```

安装后确认文件存在：

```powershell
$last30daysCnFound = `
  (Test-Path (Join-Path $env:USERPROFILE ".codex\skills\last30days-cn\SKILL.md")) -or `
  (Test-Path (Join-Path $env:USERPROFILE ".agents\skills\last30days-cn\SKILL.md"))
$last30daysCnFound
```

预期返回 `True`。

这两个 Skill 的可选 API 凭据不属于本 Skill Pack。不要为了通过检查而向
本项目配置添加 API Key。

### 6.5 在隔离环境安装 Scrapling

推荐优先使用 [稳定版初始化准备器](bootstrap.zh-cn.md)，它会生成下面所需的
项目包装入口，并在明确确认后安装 Python 工具。以下手动步骤仅供维护排查使用；
单独执行 pip 不会生成项目自定义的 `.cmd` 入口。

在项目根目录运行：

```powershell
python -m venv .\runtime\python-env
.\runtime\python-env\Scripts\python.exe -m pip install --upgrade pip
.\runtime\python-env\Scripts\python.exe -m pip install "scrapling[all]==0.4.13" "playwright==1.62.0" "yt-dlp==2026.7.4"
$env:PLAYWRIGHT_BROWSERS_PATH = (Resolve-Path .\runtime).Path + "\ms-playwright"
.\runtime\python-env\Scripts\python.exe -m playwright install chromium
```

确认可执行文件存在：

```powershell
python .agents/skills/integrated-scraper/scripts/bootstrap_pack.py --apply
& .\runtime\bin\scrapling-project.cmd --version
```

预期返回 Scrapling 版本且退出码为 0。已有自定义入口与模板不同则停止，先人工审查，不覆盖。

`runtime\` 已被 Git 忽略，不会进入公开仓库。初始化配置必须指向这个真实的
可执行文件，而不是只写一个不存在的 `scrapling` 占位值。

### 6.6 在项目独立环境安装 yt-dlp

YouTube 评论不能只依赖 OpenCLI 的空数组。需要在项目独立 Python 环境安装
yt-dlp，并保留返回的 `comment_count`。它与 Scrapling、Playwright 共用该项目
专属 Python 环境，但不与其他项目共用：

```powershell
& .\runtime\bin\yt-dlp.cmd --version
```

初始化配置中的 `yt_dlp.executable` 必须指向项目内的 `runtime\bin\yt-dlp.cmd`
或该独立环境的真实可执行文件。只有明确返回 `comment_count: 0`，才可以写
`empty_verified`；空数组、超时或页面未渲染都要写 `unassessed`。

### 6.7 不要预装 Cloakbrowser

Cloakbrowser 是条件化路径。正常初始化时，它的正确状态是：

```text
compliant_skip
```

只有出现明确的 Cloudflare、设备指纹或反自动化兼容错误时，才由用户确认后
从 [Cloakbrowser 官方渠道](https://cloakbrowser.dev/) 获取。

它不能用于绕过登录、验证码或 MFA。

### 6.8 手工创建本机配置

只有在 Codex 引导不可用时才执行本节。所有运行参数已经固定，不再手工定义：

```powershell
python .agents\skills\integrated-scraper\scripts\initialize.py
```

预期状态是 `ready_to_write`。确认无敏感字段后，再写入：

```powershell
python .agents\skills\integrated-scraper\scripts\initialize.py --write-config
```

预期状态是 `configured`。

### 6.9 运行全量检查

在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File `
  .agents\skills\integrated-scraper\scripts\start_runtime.ps1
```

如果全部就绪，最外层状态为：

```text
success
```

如果命令返回非零退出码，同时输出 `blocked_dependency` 或
`awaiting_human`，按输出中的 `checks` 和 `resolution` 逐项处理，不要
跳过检查开始采集。

## 模块七：绑定专属浏览器并完成目标账号登录

平台登录态保存在本机专属浏览器中，不保存在 Skill 或 GitHub 仓库中。新电脑
必须重新登录一次。

### 7.1 使用专属浏览器

为这套工作流只使用项目固定 Chrome 和固定 Profile：主端口是 `9222`，Profile
目录是仓库内 `runtime\chrome-public-profile`。`9223` 属于其他项目，禁止连接、
占用或关闭。不要将个人日常浏览器 Profile 导出或复制到项目目录。

专属浏览器需要满足：

- BrowserHarness 可以连接。
- 远程调试只监听本机回环地址。
- 任务所需的平台登录态保留在该浏览器本机 Profile。
- 执行任务时保持浏览器运行。

### 7.2 允许本机远程调试

在专属 Chrome 中执行：

1. 打开：

   ```text
   chrome://inspect/#remote-debugging
   ```

2. 勾选 **Allow remote debugging for this browser instance**。
3. 如果浏览器弹出确认，选择允许。
4. 确认页面显示类似：

   ```text
   Server running at: 127.0.0.1:9222
   ```

<!-- prettier-ignore -->
> [!WARNING]
> 远程调试让获授权的本机工具控制浏览器并读取该浏览器中的页面和站点数据。
> 只对专属浏览器开启，只允许本机 `127.0.0.1:9222`，并只向可信项目授权。

### 7.3 登录任务需要的账号

需要登录时，只能由使用者在专属浏览器中完成。Codex 负责打开目标页面和
登录后复检，不接收账号凭据。目标页面不要求登录时，不需要执行本节。

1. 让 Codex 使用 BrowserHarness 打开本次目标网站或平台的登录页。
2. 在专属浏览器中人工输入账号信息。
3. 人工完成二维码、短信验证码、设备确认或其他平台验证。
4. 确认目标页面已经进入登录后状态。
5. 保持浏览器窗口打开。
6. 回到原来的 Codex 任务，回复：

   ```text
   已登录
   ```

Codex 会复检同一个 Profile 和 CDP 会话，然后继续同一个任务。不要新建一个
重复任务，也不要重新定义时间范围。

### 7.4 理解 `awaiting_human`

看到 `awaiting_human` 不是程序失败。它表示 Skill 正确地停在必须由人完成的
安全边界。

常见原因包括：

- 本次目标账号未登录或会话过期。
- 页面出现验证码。
- 平台要求设备验证。
- Chrome 远程调试未允许。
- 专属浏览器已经关闭。

完成页面操作后回复“已登录”，不要把密码或验证码发给 Codex。

## 模块八：执行第一次真实任务

第一次任务用于验收完整链路。目标是获得一份有真实证据和明确局限的报告，
不是追求尽可能多的数据。

### 8.1 先理解哪些内容由你决定

Skill 不自带固定平台、品牌和商业结论。每次任务都以你当前输入的自然语言
为准，至少需要能判断以下内容：

- **目标来源与对象**：网站、平台、账号、品牌、产品、关键词、话题或具体 URL。
- **分析目标**：你想发现需求、问题、竞品比较、内容机会还是潜客信号。
- **时间范围**：例如最近 7 天、30 天或指定日期。
- **业务视角**：谁要使用结果，以及准备用它做什么决策。
- **成功条件**：报告必须提供哪些证据和结论。

你不需要填写固定表格。只要自然语言已经表达清楚，Skill 会直接提取这些
信息；只有关键歧义会改变采集路径时，它才会询问一个必要问题。

### 8.2 输入你自己的第一次任务

在同一个项目中创建新聊天，发送：

```text
@integrated-scraper

任务：
分析抖音中与“露营投影仪”相关的公开作品和评论，找到用户在亮度、
续航、便携性和户外连接方面的真实需求，并为新品策划团队提炼产品
定义和内容选题机会。

时间范围：
优先检查最近 30 天；必要时引用更早内容作为历史基线，但必须明确标注。

成功条件：
1. 每条结论附作品链接、采集时间、采集器和置信度。
2. 用户原话与分析结论分开。
3. 公开昵称只作为线索，不推断真实身份或采购权。
4. 主证据未取得时写“未评估”，不能写“没有变化”。
5. 输出原子任务、实际执行工具、降级记录、覆盖范围、局限和人工待办。

不要私信、评论、关注、购买或修改账号设置。
```

这只是一个结构完整的抖音任务示范。将目标来源、研究对象、分析目标、时间
范围和业务视角换成自己的内容，就会形成一个新的独立任务。

### 8.3 平台只是任务来源

如果下一次需要抓取 X，可以直接更换目标来源，不需要配置新的平台模块：

```text
@integrated-scraper

抓取 X 上最近 14 天关于“wireless video latency”的公开讨论，区分真实使用
问题、方案比较和普通转发，并输出证据表和机会摘要。
```

这段内容只展示如何指定“目标来源 + 研究对象 + 时间范围 + 结果用途”。
抖音和 X 都只是示例，不会成为默认平台，也不会限制用户抓取其他公开来源。

### 8.4 每次任务都可以不同

Skill 固定的是抓取、证据和安全工作流，不是平台或问题。后续可以更换任务，
例如：

```text
@integrated-scraper
检查抖音账号“某品牌官方旗舰店”最近 14 天评论中关于安装复杂度和售后
响应的负面需求，按紧急程度和品牌团队可行动性排序。
```

```text
@integrated-scraper
围绕关键词“无线图传延迟”寻找正在比较不同解决方案的真实用户表达，
区分明确采购意图、技术调研和普通讨论。
```

```text
@integrated-scraper
抓取我提供的产品页面、帮助中心和公开论坛 URL，找出适合客服团队制作 FAQ
的高频问题，不要扩展到未提供的来源。
```

### 8.5 运行中需要人工操作时

如果 Codex 在任务中返回 `awaiting_human`：

1. 阅读它说明的平台和页面。
2. 在专属浏览器完成人工动作。
3. 保持原聊天打开。
4. 回复“已登录”或说明已完成的具体动作。

如果返回 `blocked_dependency`，先修复依赖，再让 Codex复检。不要要求它用
其他工具伪装成被阻塞工具的成功结果。

### 8.6 判断结果是否合格

合格报告以抓取证据和证据分析为主，执行动作只作为审计记录。

报告必须回答：

- 用户具体遇到了什么问题或表达了什么需求。
- 该表达为什么与本次分析目标和业务视角有关。
- 用户指定的团队或决策者可以采取什么动作。
- 证据来自哪个页面、内容或评论。
- 哪些内容是已确认、合理推断或待确认。
- 本次有哪些页面、评论或原子需求没有得到充分评估。

只有“执行了哪些工具”，没有真实需求、原话、链接和机会分析的报告不合格。

## 模块九：理解本机输出

所有运行证据和报告保存在初始化时配置的 `output_root` 中。它们不会自动进入
GitHub。

### 9.1 输出目录结构

每次运行都创建独立 `task-id`。即使同一天执行多个不同对象的任务，原始
证据、摘要和报告也不会互相覆盖：

```text
<output-root>/
├── raw/
│   └── <YYYY-MM-DD>/
│       └── <task-id>/
│           ├── task.json
│           ├── execution_plan.json
│           └── work-items/
│               └── <work-id>/
│                   └── executions/
│                       └── <attempt-tool>/
│                           └── execution_manifest.json
├── processed/
│   └── <YYYY-MM-DD>/
│       └── <task-id>/
│           └── summary.json
└── reports/
    └── <YYYY-MM-DD>-<task-slug>-integrated-scraper.md
```

`task.json` 保存本次研究对象、分析目标、时间范围、业务视角和成功条件。
它不能从示例任务或上一次运行中静默继承这些字段。

### 9.2 原子任务和执行状态

每个实际运行的 `execution_manifest.json` 使用以下状态之一；没有被选中的工具
只保留在计划的排除记录中，不生成执行状态：

| 状态 | 含义 | 你要做什么 |
| --- | --- | --- |
| `success` | 该次执行取得证据并通过原子需求验收。 | 查看结果。 |
| `empty_verified` | 正常完成采集并明确证明为 0 条。 | 查看零结果证据。 |
| `partial_success` | 有证据，但覆盖不完整。 | 阅读局限和恢复条件。 |
| `awaiting_human` | 等待登录或验证。 | 在浏览器操作后回复“已登录”。 |
| `blocked_user_action` | 等待其他人工操作。 | 按说明处理。 |
| `blocked_dependency` | 缺依赖或配置。 | 修复后复检。 |
| `unassessed` | 没有取得足够数据，不能判断。 | 查看根因或降级条件。 |
| `failed` | 限次重试后仍失败。 | 查看错误和恢复条件。 |

### 9.3 最终校验

运行结束前，Skill 会执行：

```powershell
powershell -ExecutionPolicy Bypass -File .agents\skills\integrated-scraper\scripts\invoke_project_python.ps1 `
  .agents\skills\integrated-scraper\scripts\validate_run.py `
  --run-dir <本次raw任务目录> `
  --summary <本次summary.json>
```

只有校验通过后，才可以把本次运行写成完成。

总体状态按原子需求验收计算。主工具失败但降级工具通过验收，不会自动拖累总体
状态；只有部分原子需求完成时总体状态必须是 `partial_success`。

## 模块十：日常使用、升级和迁移

初始化完成后，日常使用只需要打开项目、确认专属浏览器登录状态，再输入本次
任务。

### 10.1 每次开始任务

每次使用前完成以下检查：

1. 打开 Codex 和 `integrated-scraper-skill` 项目。
2. 启动专属浏览器。
3. 确认本次需要访问的目标账号仍为登录状态。
4. 确认远程调试仍为 `127.0.0.1:9222`。
5. 使用 `@integrated-scraper` 输入本次新任务。
6. 检查报告中的时间范围和“本次新增”是否准确。

### 10.2 更新项目

在项目根目录运行：

```powershell
git status -sb
git pull --ff-only
```

`config\collection.local.json`、`runtime\` 和运行数据被 Git 忽略，正常更新不会
上传这些本机内容。

如果 `git status -sb` 显示你修改了仓库源文件，先让维护人员检查，不要直接
覆盖。

### 10.3 从旧调用名升级

早期版本使用 `@magewell-douyin-intelligence` 或 `@douyin-intelligence`。
升级后按以下步骤切换：

1. 运行 `git pull --ff-only`。
2. 完全关闭并重新打开 Codex 项目。
3. 输入 `@`，确认出现 `integrated-scraper`。
4. 后续任务改用 `@integrated-scraper`。
5. 保留现有 `config\collection.local.json`，不需要为了改名而覆盖配置。

已有本机配置会继续使用原来的输出目录，历史数据不会自动移动或改名。新电脑
或新配置才默认使用 `D:\integrated-scraper-output`。如需迁移历史数据，
先备份并由维护人员确认源目录和目标目录，不要在初始化过程中自动搬移。

### 10.4 更换新电脑

新电脑迁移时：

1. 重新安装 Codex、Git、Python 和 Node.js。
2. 重新克隆公开仓库。
3. 重新安装获准的外部依赖。
4. 启动项目 Chrome，并将新连接绑定为固定 OpenCLI Profile `integrated-scraper-9222`。
5. 在新电脑专属浏览器中重新登录任务需要的账号。
6. 重新运行初始化和全量检查。

不要复制：

- Codex `auth.json`。
- 浏览器 Profile。
- Cookie、Token、验证码或 MFA。
- OpenCLI 账号凭据。

历史报告可以作为普通文件备份，但必须与新电脑产生的“本次新证据”分开。

### 10.5 停止使用

停止使用前先备份需要保留的本机报告。删除项目目录不会自动卸载 Git、
Python、Node.js、BrowserHarness、Scrapling 或其他用户级 Skill，也不会删除
浏览器 Profile。

如需彻底移除，由维护人员分别确认以下目标：

- 项目克隆目录。
- 本机输出目录。
- `runtime\python-env` 和 `runtime\ms-playwright`。
- 用户级 last30days Skill。
- 专属浏览器 Profile。

不要使用模糊的批量删除命令。

## 模块十一：常见问题排查

本节按状态和症状定位问题。先看全量检查输出，再处理对应依赖。

### 11.1 Codex 中找不到 Skill

检查：

```powershell
Get-Location
Test-Path .\.agents\skills\integrated-scraper\SKILL.md
```

处理方法：

1. 在 Codex 中重新打开仓库根目录。
2. 确认 `Test-Path` 返回 `True`。
3. 重启 Codex。
4. 输入 `@` 搜索 `integrated-scraper`。

### 11.2 `python` 不是可识别命令

先运行：

```powershell
py -3.12 --version
```

如果成功，将文档中的 `python` 替换为 `py -3.12`。如果也失败，重新安装
Python 3.12，并重新打开终端和 Codex。

### 11.3 `npx.ps1` 被执行策略阻止

将：

```powershell
npx skills add ...
```

替换为：

```powershell
npx.cmd skills add ...
```

不需要为了这个问题把整个 PowerShell 执行策略改为无限制。

### 11.4 OpenCLI 返回 `blocked_dependency`

确认：

- OpenCLI 可执行命令或绝对路径真实存在。
- 固定 Profile `integrated-scraper-9222` 出现在 `opencli profile list` 中并为 `connected`。
- 命令显式传入固定 Profile，没有依赖全局默认 Profile。
- 当前 Windows 用户有权运行该命令。

不要把密码、Cookie 或 Token 添加到项目配置。

### 11.5 BrowserHarness 返回 `blocked_dependency`

这表示 Skill 文件或本机命令缺失。检查：

```powershell
browser-harness --doctor
```

如果命令不存在，按上游 `install.md` 重新安装。只复制
`browser-harness` 的 Skill 文件不足以通过检查。

### 11.6 BrowserHarness 返回 `awaiting_human`

这通常表示 CDP 没有连接。检查：

1. 专属浏览器是否运行。
2. `chrome://inspect/#remote-debugging` 是否已允许。
3. 页面是否显示 `127.0.0.1:9222`。
4. `config\collection.local.json` 中的 CDP 是否为本机 HTTP 地址。

不要把 CDP 改成公网或其他电脑地址。

### 11.7 Scrapling 返回 `blocked_dependency`

检查：

```powershell
& .\runtime\bin\scrapling-project.cmd --version
```

如果返回 `False`，重新执行 Scrapling 隔离环境安装。如果返回 `True`，确认
`config\collection.local.json` 中的 `scrapling.executable` 指向同一个文件。

### 11.8 初始化器返回 `already_configured`

这是防覆盖保护。不要重复写入。

先运行全量检查：

```powershell
powershell -ExecutionPolicy Bypass -File .agents\skills\integrated-scraper\scripts\invoke_project_python.ps1 `
  .agents\skills\integrated-scraper\scripts\pack_doctor.py `
  --config .\config\collection.local.json
```

Profile、主端口和输出目录属于固定运行契约，普通任务不得更换。只有发布新的
运行契约版本时，维护人员才能修改 `runtime.contract.json` 并同步测试与文档。

### 11.9 初始化器返回 `invalid_config`

常见原因包括：

- 配置试图写到项目外的其他路径。
- JSON 根节点无效。
- 配置包含 password、cookie、session、token、secret、OTP 或 MFA 等禁止字段。
- CDP 地址不是固定的 `http://127.0.0.1:9222`，或误用了禁止端口 `9223`。

删除敏感字段并重新预览配置。账号凭据必须留在平台或获授权工具自身的安全
存储中。

### 11.10 页面打开但没有正文或评论

不要把这种情况写成“没有评论”或“没有变化”。它可能表示：

- 页面只有壳结构，内容尚未渲染。
- 登录状态失效。
- 评论请求断开。
- 页面要求验证码。
- 当前工具没有取得正文。

正确状态是 `partial_success`、`awaiting_human`、`failed` 或
“本次未评估”，具体取决于证据。

### 11.11 默认 D 盘不存在

这是固定运行条件不满足，不是可以临时换路径继续执行的警告。由维护人员先创建
或挂载 D 盘，确认 `D:\integrated-scraper-output` 可写，再重新运行初始化和
`start_runtime.ps1`。如果产品未来需要支持无 D 盘电脑，应发布新的运行契约
版本并同步代码、测试和文档，不能只改本机 JSON。

### 11.12 Git 下载失败

先确认：

```powershell
git --version
```

然后在浏览器中确认
[项目仓库](https://github.com/DDDDanteeeeeee/integrated-scraper-skill)
可以访问。公开克隆不需要 GitHub 登录。

如果企业网络阻止 GitHub，由 IT 提供允许的代理或内部镜像。不要从不明来源
下载项目压缩包。

## 模块十二：交付验收清单

交付人员和使用者应一起完成一次真实验收。只完成安装而没有跑出受审计的结果，
不算交付完成。

### 12.1 基础环境验收

先确认电脑、Codex 和项目目录已经形成可用的基础工作环境。

- [ ] Windows 版本符合要求。
- [ ] Codex 桌面端可以登录。
- [ ] Git、Node.js、npm 和 Python 版本检查成功。
- [ ] 公开仓库克隆成功。
- [ ] Codex 打开的是仓库根目录。
- [ ] `@integrated-scraper` 可以被选择。

### 12.2 依赖验收

再确认完整能力库存及条件化边界符合契约。正式任务只要求计划选择的组件就绪。

- [ ] OpenCLI 命令可用。
- [ ] 固定 OpenCLI Profile `integrated-scraper-9222` 已连接。
- [ ] BrowserHarness Skill 和命令都可用。
- [ ] last30days Skill 已被发现。
- [ ] last30days-cn Skill 已被发现。
- [ ] Scrapling 独立环境可执行文件存在。
- [ ] Playwright 安装在项目独立 Python 环境，浏览器位于 `runtime\ms-playwright`。
- [ ] Cloakbrowser 在无触发条件时为 `compliant_skip`。
- [ ] `pack_doctor.py` 最外层状态为 `success`。

### 12.3 登录和安全验收

登录验收只检查会话是否可用，不收集或导出任何账号凭据。

- [ ] 专属浏览器已经绑定。
- [ ] CDP 只监听本机 `127.0.0.1:9222`。
- [ ] `9223` 未被本项目连接、占用或关闭。
- [ ] 任务需要的目标账号由使用者人工登录。
- [ ] 验证码和 MFA 没有发送给 Codex。
- [ ] `config\collection.local.json` 不含敏感字段。
- [ ] 本机配置、运行数据和报告不会被 Git 提交。

### 12.4 第一次任务验收

最后使用一次真实任务验证证据、分析和状态闭环。

- [ ] `task.json` 已拆成可独立验收的原子需求。
- [ ] `execution_plan.json` 已记录全部工具的候选或排除理由、主工具和降级顺序。
- [ ] 只有实际运行的工具产生 `execution_manifest.json`；未选工具没有阻塞任务。
- [ ] 报告首先给出真实需求和机会，不是只汇报执行动作。
- [ ] 每条关键结论有来源、链接、时间、采集器和置信度。
- [ ] 历史基线和本次新增明确分开。
- [ ] 未取得主证据时没有声称“没有变化”。
- [ ] `validate_run.py` 校验通过。
- [ ] 报告保存在配置的本机输出目录。

### 12.5 交付完成定义

只有同时满足以下条件，才可以写“交付完成”：

1. 使用者能在 Codex 中选择并调用 Skill。
2. 全量环境检查成功。
3. 使用者完成专属浏览器登录。
4. 一次真实任务完成，或以真实的部分成功状态输出。
5. 报告包含有效内容、来源和局限。
6. 本机敏感数据没有进入仓库或聊天。

## 官方参考和项目真源

以下来源用于核对 Codex 安装、认证、Windows 和 Skill 行为。项目本身的执行
边界以仓库文件为准。

- [OpenAI Windows desktop app](https://learn.chatgpt.com/docs/windows/windows-app)
- [OpenAI Codex authentication](https://learn.chatgpt.com/docs/auth)
- [OpenAI Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)
- [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills)
- [项目 README](../README.md)
- [依赖安装清单](../dependencies.manifest.json)
- [项目级 Skill](../.agents/skills/integrated-scraper/SKILL.md)
- [采集与状态契约](../.agents/skills/integrated-scraper/references/collection-contract.md)

## 下一步

新电脑通过本手册验收后，再单独评估是否创建定时任务。评估时必须明确运行
频率、浏览器登录恢复、验证码通知、失败重试、数据保留期限和报告交付方式，
不能把人工可恢复链路直接当作无人值守链路。
