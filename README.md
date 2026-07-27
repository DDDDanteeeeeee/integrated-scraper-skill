# Magewell Douyin Intelligence Skill

用于 Codex 的项目级 Skill：以只读方式采集“美乐威 Magewell”抖音作品与公开评论，识别真实用户需求、机会信号与未评估项。

## 功能与边界

- 每次由用户在 Codex 输入本次目标；Skill 只分析本次任务，不把旧日报、示例或历史结论伪装成新增结果。
- 固定按六个独立轮次执行：OpenCLI、last30days、last30days-cn、BrowserHarness、Scrapling、Cloakbrowser。OpenCLI 是作品与热门评论主通道；BrowserHarness 只补具体作品评论。
- 未登录、验证码、设备验证或 CDP 未授权时，状态为 `awaiting_human`。用户在专属浏览器完成操作后，在**同一任务**回复“已登录”即可续跑。
- 所有报告都必须附来源、时间、作品链接、采集器、置信度、轮次状态和未评估项；无内容的页面、断连或工具阻塞不等于“没有变化”。
- 只读采集公开信息。不私信、评论、关注、购买、改账号设置、自动安装依赖或启动定时任务。
- 原始公开评论和报告只写入用户配置的本机输出目录（例如 `D:\\magewell-douyin-output`），不会写入本仓库或 GitHub。

## 前置条件

- 当前发行目标为 Windows 10/11、Codex 和 Python 3.12+。若需要安装 last30days 系列，还需要 Node.js 与 `npx`。
- 初始化会检查 OpenCLI、BrowserHarness、last30days、last30days-cn 和 Scrapling；Cloakbrowser 是条件化依赖，未遇到明确的指纹/反自动化错误时保持 `compliant_skip`。
- 每个目标平台均使用本机专属浏览器保存登录态；不向本仓库或 Skill 提供密码、Cookie、验证码、MFA 或浏览器 Profile。
- 缺少任一实际需要的组件时，该轮必须标为 `blocked_dependency`，不得静默改用其他工具或把运行写成成功。

## 一键初始化

1. 安装 Codex，克隆并打开本仓库。
2. 在 Codex 中调用：

   ```text
   @magewell-douyin-intelligence 初始化这个 Skill Pack。
   ```

3. Skill 会先展示全部依赖的状态、官方来源和安装动作；任何安装都必须由用户逐项确认。它只询问本机 OpenCLI Profile 名称，随后预览并创建不含凭据的 `config/collection.local.json`。
4. Skill 运行全量检查。必要依赖全部就绪后，若 BrowserHarness 仍待 CDP 授权，则在专属浏览器完成登录、验证码或 CDP 授权，并在**同一任务**回复“已登录”。
5. 只有全量检查返回 `success` 后，才输入任意业务任务：

   ```text
   @magewell-douyin-intelligence 在美乐威 Magewell 的抖音内容与评论中寻找真实用户需求和千视机会。
   ```

## 高级：非交互初始化

仅在已确认本机 OpenCLI Profile 名称时使用。第一条命令只预览，第二条才写入本机配置：

   ```powershell
   python .agents/skills/magewell-douyin-intelligence/scripts/initialize.py --opencli-profile <profile>
   python .agents/skills/magewell-douyin-intelligence/scripts/initialize.py --opencli-profile <profile> --write-config
   ```

随后检查整个 Skill Pack：

   ```powershell
   python .agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py --config config/collection.local.json
   ```

## 依赖分发

所有执行依赖都写入 [`dependencies.manifest.json`](dependencies.manifest.json)。本仓库不复制第三方二进制，也不会自动安装：

| 依赖 | 获取方式 | 初始化时的处理 |
| --- | --- | --- |
| OpenCLI | 使用者已获授权的本机安装 | 仅验证命令和 Profile，不迁移账号或 Profile。 |
| BrowserHarness | [上游项目](https://github.com/browser-use/browser-harness)（MIT） | 用户确认后按上游 `install.md` 安装；CDP 授权仍由用户完成。 |
| last30days | [上游项目](https://github.com/mvanhorn/last30days-skill)（MIT） | 用户确认后按上游 `npx skills add` 安装。 |
| last30days-cn | [上游项目](https://github.com/Jesseovo/last30days-skill-cn)（MIT） | 用户确认后安装公开 Skill；不配置其可选 API 凭据。 |
| Scrapling | [官方文档](https://scrapling.readthedocs.io/en/latest/)（BSD-3-Clause） | 用户确认后在隔离虚拟环境安装；不传 Cookie、代理凭据或 API Key。 |
| Cloakbrowser | [官方渠道](https://cloakbrowser.dev/) | 只在明确兼容错误时提示用户自行获取；不得捆绑、预装或重分发。 |

## 分发边界

本仓库分发主 Skill、初始化器、安装清单、检查脚本、配置样例和契约。`dependencies.manifest.json` 声明外部依赖的来源、许可证、版本策略和确认边界，不复制或静默安装第三方组件。所有 `data/`、`reports/`、浏览器 Profile、OpenCLI trace、本地配置和账号会话均为本机数据，禁止提交。

## 发布状态

本项目以 [MIT License](LICENSE) 公开发布。MIT 仅适用于本仓库自身的代码与文档；外部执行依赖仍按其各自的来源、许可证和安装条款处理。
