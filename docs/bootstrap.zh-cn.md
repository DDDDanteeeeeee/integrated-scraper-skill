# 稳定 Skill Pack 初始化

此准备器补齐项目启动文件，不携带账号、浏览器 Profile、Cookie 或密钥。
当前支持 Windows。保留登记端口 9222、19825、9242，禁止借用汽水的 9223。

## 在 Codex 中使用

打开仓库后输入 `@integrated-scraper 初始化这个 Skill Pack`。
Codex 应先预览安装计划，取得安装确认，再执行对应步骤。登录和扩展授权仍由用户完成。

## 命令步骤

先用本机已安装 Python 运行（项目已经有独立 Python 时可使用它）：

```powershell
python .agents/skills/integrated-scraper/scripts/bootstrap_pack.py
```

只创建缺失的项目相对路径包装入口，不联网、不修改已有文件：

```powershell
python .agents/skills/integrated-scraper/scripts/bootstrap_pack.py --apply
```

批准 Python 工具安装后，使用符合运行契约版本的 Python 绝对路径：

```powershell
python .agents/skills/integrated-scraper/scripts/bootstrap_pack.py --apply --install-python-tools --base-python "<本机Python绝对路径>" --confirm-install
python .agents/skills/integrated-scraper/scripts/initialize.py --write-config
```

`--confirm-install` 只在用户已确认安装时传入。首次创建项目 venv，安装固定版本的
Scrapling、Playwright、yt-dlp 与清单中的 PyYAML 验证依赖，检查依赖冲突，再准备项目独立 Chromium。
现有 venv 版本不符或入口文件不同会停止，不自动删除、迁移或覆盖。

后续按主手册配置 OpenCLI、BrowserHarness 和需要的上游 Skills，再运行任务范围检查。
准备器返回 `prepared` 仅表示文件已创建，不表示浏览器、登录或整套能力已就绪。

## 可复现边界

### 每台电脑的浏览器适配

1. 发现本机 Chrome 路径和版本；版本号只记录，不把本机152或历史151写成所有人的安装要求。
2. 在初始化预览时通过 `initialize.py --chrome-executable "<本机chrome.exe绝对路径>"`
   指定路径，再确认写入无凭据本机配置。已存在配置不覆盖。
3. 检查登记端口无冲突、Profile归属正确；不得随机换端口或关闭别的项目进程。
4. 在固定入口运行OpenCLI doctor，再用独立公开测试页验证打开、状态、正文读取和会话释放。
5. 按实际任务补测BrowserHarness、动态页面和必要的登录续跑。通过哪些能力就记录哪些，不能从公开页通过推断所有平台都通过。
6. 未通过时保留本机失败原因及人工待办；不要把版本检查失败误写成没数据。

历史版本记录保留，兼容测试结果单独记录，不静默改变其他依赖版本。

- 新机器的绝对路径由本机初始化生成，不复制其他电脑的 collection.local.json。
- 现有运行契约仍要求 D 盘；没有 D 盘时明确停止，不能偷偷换输出目录。
- 目前锁定直接 Python 包版本，不是完整传递依赖锁或离线安装包。
- OpenCLI/BH 与上游 Skills 仍需遵循已审核的安装清单；本脚本不猜测安装方式或全局安装它们。
- 9222 包装入口有互斥和归属检查；19825 daemon 和条件性9242仍需单独运行时验收。
- 在另一台干净 Windows 完成真实安装和采集验收前，不能宣称全新电脑端到端已通过。
