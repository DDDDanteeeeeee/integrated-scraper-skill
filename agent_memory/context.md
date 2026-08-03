# 项目上下文

## 当前有效信息

- 交付物是可发布、可一键初始化的项目级综合抓取 Codex Skill Pack，不是
  独立应用、云服务、平台管理系统、账号管理系统或平台适配器体系。
- Skill 调用名为 `integrated-scraper`，公开仓库名为
  `integrated-scraper-skill`，中文名称为“综合抓取”。
- 核心能力是把 OpenCLI、last30days、last30days-cn、BrowserHarness、
  Scrapling 和 Cloakbrowser 编排成六个独立抓取轮次，保留原始证据并生成
  结构化数据和基于证据的报告。
- 用户在每次任务中用自然语言指定目标网站或平台、抓取对象、时间范围和用途；
  不使用强制 `platform` 字段，不维护平台白名单或平台注册表。
- 目标来源需要登录时，用户在本机专属浏览器完成对应账号登录、验证码或设备
  验证，然后在原 Codex 任务回复“已登录”继续执行。
- 抖音和 X 只是首批任务示例，不是产品边界、默认平台或硬编码规则。
- `dependencies.manifest.json` 是依赖角色、来源、许可证、版本策略和人工安装
  确认边界的唯一来源；所有运行数据和浏览器会话必须保留在本机并被 Git 忽略。
- `docs/delivery-guide.zh-cn.md` 是面向新电脑和非技术用户的标准交付路径。
