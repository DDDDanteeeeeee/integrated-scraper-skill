# 新电脑先看这里

这是 Windows 版综合抓取 Skill Pack，供 Codex 使用，不是独立 EXE，也不是离线软件合集。初始化会按清单下载所需依赖；PyYAML 已列入初始化依赖。

## 只需这样做

1. 在新电脑安装并登录 Codex。官方入口：https://openai.com/codex/ 。
2. 将 ZIP 完整解压到固定目录，例如 `D:\CodexProjects\integrated-scraper-skill`。不要直接在压缩包里运行，也不要只复制 SKILL.md。
3. 在 Codex 中打开包含本文件、AGENTS.md 和 runtime.contract.json 的项目目录。
4. 复制下面的话发送给 Codex：

```text
请读取本项目 AGENTS.md、.agents/skills/integrated-scraper/SKILL.md 和 docs/bootstrap.zh-cn.md，初始化综合抓取 Skill Pack。
先检查这台电脑，列出缺失依赖并让我确认安装，然后按项目初始化入口执行。所有依赖、配置和浏览器数据必须项目独立，不影响其他项目。
使用项目声明的固定端口，发现占用冲突就停止，不随机改端口。自动发现本机路径，不套用旧电脑的路径或浏览器 contextId。
完成依赖安装和项目浏览器绑定后，验证工具能正常读取一个公开页面。需要我安装扩展、授权或登录时，打开对应页面并告诉我具体动作。
```

5. 根据提示确认安装、安装扩展、完成授权。仅当目标信息需要登录时才登录。
6. 输入实际任务，例如：

```text
$integrated-scraper 抓取我指定网站近30天的公开内容和评论，整理真实需求与机会，输出分析报告和单独的原文记录，附来源链接。
```

如果暂时选不到 Skill，直接要求 Codex 读取 `.agents/skills/integrated-scraper/SKILL.md` 执行，不要另建项目或丢弃整个包的目录结构。

## 环境说明

- 当前包的安装器要求 Python 3.13.13；浏览器使用新电脑实际安装的 Chrome 并验证兼容，不要求照抄旧电脑版本。
- 输出约定为 `D:\integrated-scraper-output`，因此需要 D 盘。无 D 盘或固定端口有冲突时，让 Codex 说明情况后再决定，不静默改设置。
- 完整外部工具安装来源、版本和授权要求见 `dependencies.manifest.json`。OpenCLI、BrowserHarness、上游 Skills 依清单在新电脑安装；不复制旧电脑虚拟环境或浏览器 Profile。
- 包内没有账号、密码、Cookie、Token、本机配置或历史采集数据。新电脑需要的登录和授权由你完成。
- 详细手把手说明见 [交付手册](docs/delivery-guide.zh-cn.md)，命令步骤见 [初始化说明](docs/bootstrap.zh-cn.md)。

`PACKAGE-MANIFEST.json` 记录每个文件的 SHA256；ZIP 同目录另有整个压缩包的 SHA256 校验文件。
