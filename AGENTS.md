# AGENTS.md

- 默认用中文。
- 本仓库只维护项目级 Codex Skill，不开发独立前端、控制平面或云服务。
- 绝不收集、输出、提交或同步密码、Cookie、验证码、MFA 或浏览器 Profile。原始公开评论、OpenCLI trace 和本地报告仅作为本机证据，禁止提交或同步；报告可引用必要的公开原话及来源。
- 登录、验证码、设备验证和 CDP 授权只能在用户本机专属浏览器中处理；遇到这些状态必须进入 `awaiting_human`。
- OpenCLI 是作品/热门评论主通道；BrowserHarness 仅用于具体作品的可见评论补充；Cloakbrowser 仅在有明确指纹/反自动化证据时使用，不能绕过验证码。
- 依赖以 `dependencies.manifest.json` 为准；在未获得用户逐项确认前，不执行任何上游安装动作。必要依赖未全部通过 `pack_doctor.py` 时不得开始采集。
- 改动脚本或 Skill 后运行对应单元测试和 `quick_validate.py`。
- GitHub 发布前检查 `.gitignore`、工作树、测试与 Skill 验证；未经用户明确最终确认不得推送。
