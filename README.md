# Douyin Intelligence Skill

用于 Codex 的项目级 Skill：根据你每次输入的研究对象和目标，以只读方式
采集抖音公开作品与评论，识别真实用户需求、问题、机会信号和待复核线索。

Skill 固定的是可审计的六轮采集流程、安全边界和报告标准，不固定品牌、
账号、关键词、受益公司或分析结论。文中出现的具体品牌和受益方都只是示例。

## 从零开始的交付手册

如果你要在一台新 Windows 电脑上交付或使用本项目，请从
[《抖音公开情报 Skill Pack 新电脑交付与使用手册》](docs/delivery-guide.zh-cn.md)
开始。手册覆盖 Codex 安装、仓库下载、依赖初始化、专属浏览器登录、
自定义任务、报告验收、升级、迁移和故障排查。

## 功能与边界

每次运行都从当前任务提取研究对象、分析目标、时间范围、业务视角和成功
条件。研究对象可以是抖音账号、品牌、产品、关键词、话题或具体作品 URL。

- 固定按六个独立轮次执行：OpenCLI、last30days、last30days-cn、
  BrowserHarness、Scrapling、Cloakbrowser。
- OpenCLI 是作品与热门评论主通道；BrowserHarness 只补具体作品评论和
  登录态证据。
- 未登录、验证码、设备验证或 CDP 未授权时，状态为 `awaiting_human`。
  你在专属浏览器完成操作后，在同一任务回复“已登录”即可续跑。
- 所有报告都附来源、时间、作品链接、采集器、置信度、轮次状态和未评估项。
  空页面、断连或工具阻塞不等于“没有变化”。
- 只读采集公开信息。不私信、评论、关注、购买、改账号设置、自动安装依赖
  或启动定时任务。
- 原始公开评论和报告只写入你配置的本机输出目录，例如
  `D:\douyin-intelligence-output`，不会写入本仓库或 GitHub。

## 前置条件

当前发行目标为 Windows 10/11、Codex 和 Python 3.12+。安装 last30days
系列还需要 Node.js 与 `npx`。

- 初始化检查 OpenCLI、BrowserHarness、last30days、last30days-cn 和
  Scrapling。
- Cloakbrowser 是条件化依赖，未遇到明确指纹或反自动化兼容错误时保持
  `compliant_skip`。
- 每个目标平台使用本机专属浏览器保存登录态；不要向本仓库或 Skill 提供
  密码、Cookie、验证码、MFA 或浏览器 Profile。
- 缺少任一实际需要的组件时，该轮必须标为 `blocked_dependency`，不得
  静默替代或把运行写成成功。

## 一键初始化

初始化只准备本机执行环境，不预设任何研究对象。

1. 安装 Codex，克隆并打开本仓库。
2. 在 Codex 中调用：

   ```text
   @douyin-intelligence 初始化这个 Skill Pack。
   ```

3. 查看 Skill 展示的依赖状态、官方来源和安装动作。
4. 对每项安装分别确认，并提供本机 OpenCLI Profile 名称。
5. 在专属浏览器完成登录、验证码或 CDP 授权。
6. 等待全量检查返回 `success`。
7. 输入你自己的任务，例如：

   ```text
   @douyin-intelligence
   分析抖音账号“美乐威 Magewell”近 30 天的作品和公开评论，
   找到真实用户需求，并提炼可供千视参考的产品、销售和内容机会。
   ```

上例只演示如何写清研究对象、时间范围、分析目标和业务视角。你可以把它
替换为自己的账号、品牌、产品、关键词、话题、时间范围和决策问题。

## 高级：非交互初始化

仅在已确认本机 OpenCLI Profile 名称时使用。第一条命令只预览，第二条
才写入本机配置：

```powershell
python .agents/skills/douyin-intelligence/scripts/initialize.py --opencli-profile <profile>
python .agents/skills/douyin-intelligence/scripts/initialize.py --opencli-profile <profile> --write-config
```

随后检查整个 Skill Pack：

```powershell
python .agents/skills/douyin-intelligence/scripts/pack_doctor.py --config config/collection.local.json
```

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
| Cloakbrowser | [官方渠道](https://cloakbrowser.dev/) | 只在明确兼容错误时提示用户自行获取；不得捆绑、预装或重分发。 |

## 分发边界

本仓库分发主 Skill、初始化器、安装清单、检查脚本、配置样例和契约。
`dependencies.manifest.json` 声明外部依赖的来源、许可证、版本策略和确认
边界，不复制或静默安装第三方组件。所有 `data/`、`reports/`、浏览器
Profile、OpenCLI trace、本地配置和账号会话均为本机数据，禁止提交。

## 发布状态

本项目以 [MIT License](LICENSE) 公开发布。MIT 仅适用于本仓库自身的代码
与文档；外部执行依赖仍按其各自来源、许可证和安装条款处理。
