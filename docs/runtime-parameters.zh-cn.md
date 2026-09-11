# 综合抓取 Skill 固定运行参数

这份文件是 `runtime.contract.json` 的人类可读说明。JSON 是机器执行真源；本文
用于交付和排查。除当前电脑上的可执行文件绝对路径外，运行时不得临时改值。

## 固定参数

| 项目 | 固定值 | 说明 |
| --- | --- | --- |
| 主 Chrome | `C:\Program Files\Google\Chrome\Application\chrome.exe` | 项目专属浏览器。 |
| 主 CDP 地址 | `127.0.0.1` | 只监听本机。 |
| 主 CDP 端口 | `9222` | 综合抓取 Skill 唯一主端口。 |
| 禁止端口 | `9223` | 属于汽水等其他项目，不能连接、占用或关闭。 |
| Chrome Profile | `<仓库>\runtime\chrome-public-profile` | 登录态只保存在这个项目目录。 |
| OpenCLI Profile | `integrated-scraper-9222` | 每条命令显式指定，不使用全局默认值。 |
| OpenCLI daemon | `19825` | OpenCLI 本机服务端口。 |
| OpenCLI 窗口模式 | `background` | 默认后台持久会话。 |
| OpenCLI 连接超时 | `45` 秒 | 浏览器连接等待上限。 |
| OpenCLI 命令超时 | `60` 秒 | 单条浏览器命令等待上限。 |
| BrowserHarness CDP | `http://127.0.0.1:9222` | 连接同一个项目 Chrome。 |
| 浏览器控制并发 | `1` | OpenCLI、BrowserHarness、Playwright 串行。 |
| 项目 Python | `<仓库>\runtime\python-env\Scripts\python.exe` | 不与其他项目共用依赖。 |
| Playwright 浏览器 | `<仓库>\runtime\ms-playwright` | 不使用全局浏览器缓存。 |
| Scrapling | `<仓库>\runtime\bin\scrapling-project.cmd` | 调用项目 Python 环境。 |
| yt-dlp | `<仓库>\runtime\bin\yt-dlp.cmd` | 调用项目 Python 环境。 |
| Cloakbrowser CDP | `127.0.0.1:9242` | 仅在明确触发条件成立时使用。 |
| 数据输出 | `D:\integrated-scraper-output` | 原始证据、处理结果和报告。 |

## 固定执行入口

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_runtime.ps1
```

该入口依次执行三件事：加载项目环境变量；启动或复检 `9222` 的项目 Chrome；
运行 `pack_doctor.py`。任何固定值不匹配都会停止，不会自动改用其他端口或其他
浏览器。

上述命令用于初始化和完整能力库存检查。正式任务先生成动态计划，再只检查本次
选择的工具：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/invoke_project_python.ps1 .agents/skills/integrated-scraper/scripts/plan_run.py --task <task.json> --output <execution_plan.json>
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_runtime.ps1 -PlanPath <execution_plan.json>
```

如果计划不需要 OpenCLI 或 BrowserHarness，该入口不会为了形式完整而启动项目
Chrome。未选工具的依赖状态不会阻塞本次任务。

只做检查、不启动 Chrome：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/integrated-scraper/scripts/start_runtime.ps1 -CheckOnly
```

## 登录和任务规则

登录不是每次任务的固定步骤。目标页面公开可读时直接采集；只有页面确实要求
登录、验证码或设备确认时，才在上述项目 Chrome 内由用户完成。完成后继续同一
任务和同一 `task_id`。

OpenCLI 命令必须显式使用固定 Profile，例如：

```powershell
powershell -ExecutionPolicy Bypass -File `
  .agents\skills\integrated-scraper\scripts\invoke_opencli.ps1 <命令>
```

该入口会自动且显式添加 `--profile integrated-scraper-9222`。BrowserHarness 和
项目 Python 分别使用 `invoke_browser_harness.ps1` 与
`invoke_project_python.ps1`。不得运行会修改全局默认 Profile 的命令来“方便执行”。

## 空结果和失败

页面正常加载、目标区域定位成功、采集动作完成且页面明确显示 0 条，才是
`empty_verified`。超时、403、登录墙、解析失败、浏览器错位或命令空载荷属于
`unassessed`、`failed` 或阻塞状态，不能写成“没有数据”。
