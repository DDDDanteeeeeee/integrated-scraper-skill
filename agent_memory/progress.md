# 当前任务进度

## 目标

将已验证的抖音公开情报流程固化为可一键初始化、可由用户逐次自定义研究任务
的项目级 Codex Skill Pack。

## 当前状态

- 项目级 Skill、六轮采集契约、无凭据环境检查、完整依赖检查和运行校验脚本已完成。
- 17 项单元测试通过；官方 `quick_validate.py` 在 UTF-8 模式下通过。
- 示例配置的完整依赖检查正确返回 `blocked_dependency`：未配置 OpenCLI、BrowserHarness 或 Scrapling 时不会误启动采集。
- 本地 Git 已初始化；`data/`、`reports/`、`runtime/`、本机配置、trace 和 `.env` 均已由 Git 忽略规则实测覆盖。
- 已新增 `dependencies.manifest.json` 与无凭据初始化器；首次运行无需手改 JSON，初始化器不会自动安装、写入凭据或覆盖现有本机配置。
- 初始化器仅允许写入仓库内的 `config/collection.local.json`；CDP 地址仅允许本机回环地址，避免误连远端浏览器。
- 新增 Windows GitHub Actions 校验；本地完整依赖检查、初始化边界、17 项单元测试和官方校验均已通过。
- GitHub CLI 已重新授权，首次提交 `7b7742f` 已在本地 `main` 分支创建，并使用仓库级 GitHub noreply 提交身份。
- 公开仓库已更名为：`https://github.com/DDDDanteeeeeee/douyin-intelligence-skill`。仓库保持 PUBLIC、MIT 和 `main`；本机 `origin` 已同步到新规范地址，旧 GitHub 地址仍解析到新仓库。
- GitHub Actions 的 `validate-skill-pack` 已在该提交上成功完成。
- 已新增 `docs/delivery-guide.zh-cn.md`，覆盖 Codex Desktop、Git、Node.js、Python、仓库下载、Skill 发现、六轮依赖初始化、专属浏览器与 CDP 授权、抖音人工登录、首次任务、结果验收、更新迁移和故障排查。
- README 已增加交付手册入口；Codex 安装、登录和 Skill 调用方式按当前 OpenAI 官方文档复核，未再沿用“必须订阅 ChatGPT Plus”等过时或不准确表述。
- 文档结构检查、代码围栏检查、相对链接检查和 `git diff --check` 均通过；17 项单元测试及官方 Skill 校验再次通过。
- 通用化与交付手册改动已提交为 `1ed829b`，推送到
  `agent/generalize-douyin-intelligence`，并创建草稿 PR
  `https://github.com/DDDDanteeeeeee/douyin-intelligence-skill/pull/1`。
- 用户指出交付手册错误地把 Magewell 示例写成产品边界；已追溯到 Skill 名称、
  元数据、默认目录和报告名同样存在业务硬编码。
- Skill 已从 `magewell-douyin-intelligence` 通用化为
  `douyin-intelligence`；任务对象支持账号、品牌、产品、关键词、话题和
  具体作品 URL，业务视角由用户当次输入。
- 每次运行新增独立 `task_id` 和 `task.json`；六轮 manifest 与 summary
  必须匹配同一任务 ID 和研究对象，避免不同用户或同日多任务串数据。
- README、交付手册、依赖清单、配置样例、元数据、契约、脚本和测试已同步
  使用通用命名；Magewell 仅保留在明确标注的示例任务中。
- 通用化后 19 项单元测试全部通过，其中包含与官方 Skill 校验器一致的
  frontmatter 名称、字段、长度和字符约束；文档结构、代码围栏、相对链接和
  `git diff --check` 已通过。官方 `quick_validate.py` 当前因验证环境缺少
  PyYAML 未能直接运行，尚不能把该命令写为本轮通过。
- 草稿 PR #1 的 GitHub Actions `validate-skill-pack / test` 已通过，
  PR 合并状态为 `CLEAN`；`main` 尚未合并该 PR。

## 下一步

1. 由用户审阅并合并草稿 PR #1。
2. 合并后在一台新电脑上按交付手册完成一次端到端安装、登录、采集和报告
   验收。
