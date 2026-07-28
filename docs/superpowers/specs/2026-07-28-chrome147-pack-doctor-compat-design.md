# Chrome 147+ Pack Doctor 兼容设计

## 背景

当前本机环境已满足 BrowserHarness 的实际运行条件：

- `browser-harness` 0.1.8 可以连接已授权的标准 Chrome；
- `page_info()` 已返回真实页面状态；
- `browser-harness --doctor` 报告 daemon 正常且活动浏览器连接数为 1。

但是 Chrome 147+ 在默认用户数据目录下会对
`http://127.0.0.1:9222/json/version` 返回 HTTP 404。BrowserHarness 已通过
`DevToolsActivePort` 兼容这一行为，而项目的 `doctor.py` 仍把该 404 直接判为
CDP 未授权，导致 `pack_doctor.py` 错误返回 `awaiting_human`。

## 目标

让 `pack_doctor.py` 在 Chrome 147+ 的 404 场景中根据 BrowserHarness 的真实连接
健康状态作出正确判断，同时保留现有安全边界：

- CDP 地址必须是本机 HTTP 回环地址；
- 普通连接失败、超时、403 或没有活动浏览器连接时仍不得判定成功；
- 不读取、导出或记录 Cookie、凭据、验证码、浏览器 Profile 内容或 OpenCLI trace；
- 不把任意占用 9222 端口并返回 404 的服务误判为可用 CDP。

## 非目标

- 不修改 `SKILL.md`、依赖清单或采集流程；
- 不改变 OpenCLI、Scrapling、last30days 或 Cloakbrowser 的检查逻辑；
- 不启动新的云浏览器、后台服务或定时任务；
- 不为其他 HTTP 状态码添加宽松兜底。

## 方案

新增一个可单独测试的 BrowserHarness 健康检查函数。它以无 shell 的子进程方式运行：

```text
browser-harness --doctor
```

只有输出同时满足以下两个条件才返回健康：

1. `daemon alive` 为 `[ok]`；
2. `active browser connections` 为 `[ok]`，且连接数至少为 1。

可选的 Browser Use Cloud 登录失败不影响本机 BrowserHarness 健康判定。
命令缺失、超时、进程错误或输出不完整都返回不健康。

`check_pack()` 保留现有 CDP 探测作为主判定。仅当所有条件同时成立时启用兼容兜底：

1. BrowserHarness Skill 与本机命令已安装；
2. 配置中的 CDP 地址已通过现有回环地址校验；
3. 主 CDP 探测失败原因明确为 HTTP 404；
4. 新增的 BrowserHarness 健康检查确认 daemon 正常且活动连接数至少为 1。

兼容兜底通过后，BrowserHarness 检查状态为 `success`，详情明确说明使用了
Chrome 147+ 404 兼容验证。任何条件不满足时保留原始错误和
`awaiting_human` 状态。

为保持单元测试可控，`check_pack()` 接收可注入的健康检查函数；默认实现才执行
真实 `browser-harness --doctor`。

## 数据流

```text
本机配置
  -> doctor.check() 严格探测 /json/version
  -> 成功：沿用原逻辑
  -> HTTP 404：
       -> BrowserHarness Skill 与命令存在？
       -> browser-harness --doctor
       -> daemon alive 且 active connections >= 1？
       -> 是：Chrome 147+ 兼容成功
       -> 否：保留 awaiting_human
  -> 其他错误：保留原逻辑
```

## 错误处理

- 子进程执行设置有限超时，超时后返回不健康，不抛出未处理异常；
- 不依赖 `browser-harness --doctor` 的退出码单独判定，因为可选云登录检查可能失败；
- 只解析固定健康行和数字连接数，不解析或保存活动页面标题、URL；
- 诊断详情不得包含浏览器 Profile 路径、WebSocket 标识或敏感页面内容。

## 测试策略

遵循 RED-GREEN-REFACTOR：

1. 先新增失败测试：CDP 探测返回 HTTP 404，但 BrowserHarness 健康检查为真时，
   `check_pack()` 必须返回 `success`；
2. 新增保护测试：同样的 HTTP 404 在健康检查为假时必须保持
   `awaiting_human`；
3. 运行目标测试并确认第一项在生产代码修改前按预期失败；
4. 实施最小代码修改，使新增测试通过；
5. 运行全部单元测试；
6. 运行仓库提供的 `quick_validate.py`；若仓库没有该脚本，记录缺失事实；
7. 在已连接的本机环境重新运行 `pack_doctor.py`，要求总体状态为 `success`，
   BrowserHarness 为 `success`，Cloakbrowser 为 `compliant_skip`；
8. 检查 Git 工作树，确保本机配置和运行证据没有被提交。

## 验收标准

- Chrome 147+ 的 `/json/version` 404 不再造成假 `awaiting_human`；
- 只有 BrowserHarness daemon 和至少一个活动连接都真实健康时才使用 404 兼容；
- 其他依赖检查行为不变；
- 新增与既有测试全部通过；
- 实际 `pack_doctor.py` 返回 `success`；
- 不提交本机配置、浏览器数据、原始报告、trace 或临时安装文件。
