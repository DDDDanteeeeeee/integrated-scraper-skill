---
name: magewell-douyin-intelligence
description: 在美乐威 Magewell 抖音作品和公开评论中执行可审计的只读需求、机会与线索情报采集。用户提到美乐威、Magewell、抖音评论、竞争情报、用户需求、潜客线索、日报或增量复查时使用；需要 OpenCLI 主采集、可选 BrowserHarness 评论补充，以及本机人工登录/验证码/CDP 授权边界。
---

# 美乐威抖音情报

执行以证据为中心的抖音情报任务。将作品和公开评论当作主证据；把外部趋势当作补充；不把空结果、壳页面或阻塞写成“没有变化”。

## 首次初始化

当用户提到“初始化”“新电脑”“配置 Skill Pack”或本机配置不存在时：

1. 读取项目根目录的 `dependencies.manifest.json` 和 `references/collection-contract.md`。
2. 说明这是检查与引导，不是自动安装。先展示每项依赖的官方来源、版本策略、许可证和安装动作；对任何外部依赖，安装前都必须取得用户明确确认。
3. 只询问一个必要的非敏感值：本机 OpenCLI Profile 名称。默认使用 `opencli`、`http://127.0.0.1:9222`、`scrapling` 和 `D:\\magewell-douyin-output`；用户可修改这些本机路径/地址。
4. 先预览再写入本机配置：

   ```powershell
   python .agents/skills/magewell-douyin-intelligence/scripts/initialize.py --opencli-profile <profile>
   python .agents/skills/magewell-douyin-intelligence/scripts/initialize.py --opencli-profile <profile> --write-config
   ```

5. 初始化器绝不覆盖 `config/collection.local.json`，绝不创建账号、安装依赖、读取凭据或写入浏览器 Profile。
6. 写入配置后运行全量检查：

   ```powershell
   python .agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py --config config/collection.local.json
   ```

7. 任一必要依赖缺失时写 `blocked_dependency` 并列出清单中的官方安装动作；不要开始任务。BrowserHarness 已安装但 CDP 未授权时写 `awaiting_human`。Cloakbrowser 在无明确指纹/反自动化错误时必须为 `compliant_skip`。

## 进入条件

1. 若 `config/collection.local.json` 不存在，走“首次初始化”，不要要求用户手工编辑 JSON。
2. 读取 `references/collection-contract.md`。
3. 从当前任务提取本次目标、时间范围、目标账号和成功条件；不要复用旧日报当作本次结果。
4. 运行项目根目录的全量环境检查：

   ```powershell
   python .agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py --config config/collection.local.json
   ```

5. 只有全量检查返回 `success` 时才能开始六轮采集。`awaiting_human`、`blocked_dependency` 和 `invalid_config` 都不是成功。
6. 只读取 `config/collection.local.json` 中的本机路径、OpenCLI Profile、CDP URL 和输出目录。CDP 只允许本机 `http://127.0.0.1`、`http://localhost` 或 `http://[::1]`。绝不请求、读取、记录或输出密码、Cookie、验证码、MFA 或浏览器 Profile 内容。

## 登录待办

当目标平台未登录、会话失效、出现验证码/设备验证，或 CDP 未授权时：

1. 将本次任务状态写为 `awaiting_human`，写明平台、登录页、所需人工动作与时间。
2. 在专属浏览器打开该平台的登录页；用户在本机完成登录、验证码和 CDP 授权。
3. 停止内容采集；不要尝试绕过验证，也不要改用其他工具凑出结果。
4. 用户回复“已登录”后，复检同一 Profile/CDP 会话并继续**同一任务**。不要创建重复任务，不要重置本次时间窗口。

## 采集顺序

每个 Skill 独立执行、独立写 `round_manifest.json`；不得把一个工具的结果伪装成另一个工具的成功。

1. `01-opencli`：使用配置的 Profile 抓取目标账号作品和每条作品的热门公开评论。这是主通道。先作品、后评论；评论请求中断时保留 trace，写 `unassessed`，不要说“无评论变化”。
2. `02-last30days`：仅补充近 30 天的海外工作流/竞品上下文。保存 query plan、raw 输出和外部补充；排除 score-0 entity-miss。
3. `03-last30days-cn`：仅补充中文公开平台上下文。记录日期、来源、已确认与弱证据。
4. `04-browser-harness`：只在具体作品的评论补充、登录态核验或可见页面证据需要时使用。先截图，再读取；出现登录墙或验证码立即进入 `awaiting_human`。不要用主页壳 DOM 推断没有作品或评论。
5. `05-scrapling`：仅用于已知公开 URL。先 `get`，正文为空时限次 `fetch`；空正文不等于无内容。
6. `06-cloakbrowser`：只有明确出现 Cloudflare、设备/指纹检测或反自动化兼容错误时才运行。绝不用于绕过登录、验证码或 MFA；没有触发条件则记 `compliant_skip`。

允许状态只有：`success`、`partial_success`、`awaiting_human`、`blocked_user_action`、`blocked_dependency`、`compliant_skip`、`failed`。任何主证据缺失的运行必须是 `partial_success` 或阻塞状态。

## 分析与报告

只将明确的第一人称使用、故障、选型、价格、试用、部署或替代诉求归为需求/线索。公开昵称不是身份、采购权或联系方式。

报告顺序：

1. 本次已证实的需求、机会和可执行建议。
2. 逐条来源、原话、作品链接、时间、采集器和置信度。
3. 本次新增与历史基线的严格区分。
4. 轮次状态、覆盖范围、局限和人工待办。

运行结束前执行：

```powershell
python .agents/skills/magewell-douyin-intelligence/scripts/validate_run.py --rounds-dir <rounds-dir> --summary <summary.json>
```

只有通过校验后才声明运行完成。不得自动发布、私信、评论、关注、购买、修改账号设置、安装依赖或启动定时任务；这些动作都需要用户单独确认。

## 资源

- 读取 `references/collection-contract.md` 以确定状态、文件布局、证据和隐私契约。
- 读取项目根目录的 `dependencies.manifest.json` 以确定依赖角色、官方来源、版本策略与安装确认边界。
- 使用 `scripts/initialize.py` 生成不可覆盖、无凭据的本机配置。
- 使用 `scripts/doctor.py` 进行无凭据的本机环境检查。
- 使用 `scripts/pack_doctor.py` 验证全部必要依赖和条件化 Cloakbrowser 状态。
- 使用 `scripts/validate_run.py` 验证六轮状态与总体状态是否诚实一致。
