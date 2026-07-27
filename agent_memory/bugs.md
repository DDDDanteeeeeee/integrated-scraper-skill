# 问题与风险

## 当前风险

- OpenCLI Profile 可能失效或连接中断；空载荷必须标为未评估，不得声称无变化。
- BrowserHarness 本机后台可能在单次调用后超时；不得把该故障归为登录失败或内容不存在。
- 原始评论可能包含公开昵称和业务表述，属于本地运行数据，不得进入 GitHub。
- 外部依赖的代码、安装方式与许可证不能假定可再分发；Skill Pack 只锁定其角色和确认边界，不能静默复制或安装。
- 公开发布仍缺少用户选定的 `LICENSE`；在此之前只能称为本地发布候选，不能称为可公开再分发仓库。

## 已处理问题

- 已将独立前端和云端控制平面从当前交付范围移除。
- 示例占位配置不会被误判为可用；敏感配置字段会被本机检查拒绝。
- 原 `dependencies.lock.json` 容易被误解为第三方可复现锁定；已更正为含来源、许可证、版本策略和人工确认动作的 `dependencies.manifest.json`。
- 依赖检查此前只强制验证 OpenCLI；已替换为完整 `pack_doctor.py`，并覆盖 BrowserHarness、last30days、last30days-cn、Scrapling 和 Cloakbrowser 的边界状态。
- CDP 曾可接受任意 HTTP 地址，初始化器也可写入任意路径；现已限制为本机回环 CDP 与项目内本机配置文件。
- 官方校验器在 Windows 默认 GBK 环境无法读取 UTF-8 中文文件；以 `PYTHONUTF8=1` 运行后已通过，属于工具编码兼容性而非 Skill 结构错误。
