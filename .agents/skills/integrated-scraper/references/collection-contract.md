# 采集契约

本契约定义综合抓取任务的输入隔离、动态路由、状态、文件布局、证据和隐私边界。

## 任务与原子需求

每次运行创建独立 `task_id`，保存本次 `target`、`objective`、`time_range`、
`decision_context`、`success_criteria` 和 `work_items`。每个原子需求必须能够独立
验收，并包含：

- `id`、`requirement` 和非空 `acceptance_criteria`。
- `risk_level` 与 `cross_validation_required`。
- 通过硬门槛的 `candidates`，以及所有其他工具的 `excluded_tools` 和排除原因。
- 每个候选工具的八维评分、说明和额外辅助依赖。

示例任务、历史任务和上次报告不能提供隐含来源、对象、受益方或结论。

## 动态路由

`runtime.contract.json` 是工具能力、评分权重和运行参数真源。路由顺序固定为：

```text
识别任务 → 拆成原子需求 → 硬门槛 → 候选评分 → 主工具 → 结果验收
                                              ↓ 失败或未通过
                                           按排名降级
```

- 每个已登记工具必须进入候选或排除列表，不能静默跳过。
- 默认只运行得分最高的主工具。工具命令成功但结果不满足验收标准，仍属于验收失败。
- 主工具通过验收后停止；只有高风险、用户明确要求或证据冲突时运行独立核验工具。
- 未选工具缺失、未登录或不可用，不影响本次总体状态。
- 只有一个工具可执行时，缺依赖就申请补齐，需登录就暂停，限次恢复仍失败就保留明确阻塞。
- 降级工具通过验收后，原主工具的失败作为审计记录保留，但不自动降低业务结果状态。

Scrapling 负责公开 URL、Sitemap、批量公开页面、结构化字段和自适应选择器；
OpenCLI 负责已有适配器的平台业务对象；BrowserHarness 负责登录交互和页面可见
验收；last30days 系列负责近期趋势；Cloakbrowser 仅处理已经确认的浏览器指纹
兼容问题。需要登录的交互不能用 Scrapling 或 Cloakbrowser 绕过。

## 本机配置

主 Chrome/CDP 固定为 `127.0.0.1:9222`，OpenCLI Profile 固定为
`integrated-scraper-9222`，daemon 固定为 `19825`，项目 Chrome Profile 固定为
`runtime/chrome-public-profile`，输出目录固定为 `D:\integrated-scraper-output`。
`9223` 属于其他项目，禁止连接、占用或关闭；Cloakbrowser 仅在触发条件成立时
使用独立 `9242`。

使用 `scripts/initialize.py` 创建被 Git 忽略的无凭据
`config/collection.local.json`。初始化可以检查完整能力库存；正式任务必须使用
`pack_doctor.py --plan <execution_plan.json>`，只让计划中的主工具、交叉核验工具
及其辅助依赖影响总体就绪状态。切换降级工具使用 `--plan <plan> --work-item <id>
--require-tool <tool>`，仅检查该候选和它声明的辅助依赖，不保留已失败主工具。

所有浏览器控制器严格串行，并发数固定为 1。禁止字段或内容：密码、Cookie、
session、token、验证码、OTP、MFA、浏览器 Profile 导出和 OpenCLI trace 正文。

## 状态

| 状态 | 含义 | 后续动作 |
| --- | --- | --- |
| `success` | 原子需求已取得证据并通过全部验收。 | 停止该项或执行明确要求的交叉核验。 |
| `empty_verified` | 采集链路正常完成，并有明确的零结果证据。 | 记录零结果证据。 |
| `partial_success` | 取得部分证据，但该项尚未满足全部验收。 | 继续限次恢复或降级。 |
| `awaiting_human` | 登录、验证码、设备验证或 CDP 授权待用户完成。 | 暂停该项并说明一个明确动作。 |
| `blocked_user_action` | 需要其他人工操作。 | 说明所需动作和恢复条件。 |
| `blocked_dependency` | 唯一或当前选中的执行路径缺少依赖。 | 请求安装确认或补齐配置。 |
| `unassessed` | 没有取得足以判断的数据。 | 不得解释为没有内容。 |
| `failed` | 已限次恢复仍失败。 | 保存根因和恢复条件。 |

总体状态只按原子需求计算：全部通过为 `success`；部分通过为
`partial_success`；没有任何原子需求通过时必须保留真实阻塞或失败状态。未选工具
没有执行状态，也不会制造 `partial_success`。

## 文件布局

```text
<output-root>/
  raw/<YYYY-MM-DD>/<task-id>/task.json
  raw/<YYYY-MM-DD>/<task-id>/execution_plan.json
  raw/<YYYY-MM-DD>/<task-id>/work-items/<work-id>/executions/<attempt-tool>/execution_manifest.json
  processed/<YYYY-MM-DD>/<task-id>/summary.json
  reports/<YYYY-MM-DD>-<task-slug>-integrated-scraper.md
```

每个 execution manifest 至少记录 `execution_id`、`attempt_index`、
`work_item_id`、`tool`、`task_id`、`status`、`timestamp`、`target`、
`acceptance_passed` 和 `result`。未通过验收时还必须记录 `recovery_condition`。

`summary.json` 至少记录 `task_id`、`target`、`overall_status`、
`current_primary_evidence` 和逐项 `work_items`；每项关联
`accepted_execution_ids`、状态和证据存在性。校验器拒绝跨任务对象、未入选工具、
越级降级、超限重试、通过验收后重复执行或没有足够独立核验的高风险结论。

## 证据、空结果与隐私

- 每条可报告证据保留来源 URL、采集时间、采集器和原始公开文本。
- 历史数据标为历史基线，不能说成今日新增。
- 公开昵称只用于去重和人工复核；不能推断姓名、联系方式、采购权或身份。
- 主通道空载荷、连接中断、页面壳、未渲染评论、403 或权限不足都是
  `unassessed`、失败或阻塞。
- `success` 必须记录正数 `evidence_count`。
- `empty_verified` 必须保存非空 `empty_evidence`，证明页面或接口正常完成并明确为零。
- Facebook 群组列表要分批只读；0 字节不能解释为无群组。
- YouTube 评论必须保留 `comment_count` 或可见零结果证据；OpenCLI 空数组单独
  不足以证明评论为零。

## 输出表达

交付必须包含独立的分析报告MD和源数据MD。源数据不是分析精选，保留本次所有
已采内容；仅重复、安全敏感、界面噪声、删除占位可记录理由后排除。
按平台、页面组织正文和回复，保留父子关系；公共说明只写一次，技术校验信息集中
索引。完整清单、格式及最终--final-delivery验收见[续跑与内容验收](resume-and-quality.md)。

报告先写需求、机会和建议，再写证据、事实/推断边界、原子任务与实际执行器
状态、覆盖范围、限制、人工待办和本地路径。使用直接易懂的语言，不用执行日志
代替情报内容。humanizer 只作用于说明文字，不改写原始证据、URL、技术名称、
状态值和机器字段。

## 稳定版证据与恢复契约

计划由当前 `plan_run.py` 生成，包含 `task_fingerprint` 和 `contract_fingerprint`。
每份 execution manifest 和 summary 必须包含与计划相同的 `task_fingerprint`。
任务或契约改变后旧计划必须被拒绝；不得编辑旧证据来匹配新任务。历史目录保持原样。

接受的 execution manifest 的 `result` 除原字段外必须包含：

```json
{
  "evidence_count": 1,
  "evidence": [{
    "id": "W1-01-source1",
    "url": "https://example.com/source",
    "captured_at": "2026-09-10T12:00:00+08:00",
    "path": "work-items/W1/executions/01-scrapling/source.txt",
    "sha256": "实际文件的SHA256，不使用此占位值"
  }],
  "assessments": [{
    "criterion": "与该原子任务验收标准逐字一致",
    "passed": true,
    "reason": "说明原始内容如何满足标准，包括覆盖范围和遗漏情况",
    "evidence_ids": ["W1-01-source1"]
  }]
}
```

证据路径相对 raw 任务目录且不得越界，文件须非空且哈希匹配。
`empty_verified` 也必须有上述证据和 assessments，`empty_evidence` 改为指向
明确显示零结果的证据 ID；文字断言或空数组不能替代页面/接口证据。
`summary.assessments` 在总体成功时逐条对应任务级 `success_criteria`。

人工待办续跑必须使用同一工具，并在新 manifest 附：

```json
{"resume": {"previous_execution_id": "W1-01-scrapling", "condition_resolved": true,
"verified_at": "2026-09-10T12:10:00+08:00", "note": "人工完成后对同一环境复检的依据"}}
```

首次执行加两次恢复为上限；人工/缺依赖待办不算执行次数。不得跳过主工具、
越级切换或倒回已放弃的工具。高风险交叉核验尚未完成时允许如实记录暂停/失败，
不得为使校验通过把未完成项标成成功。

交叉核验完成的 summary 工作项还需 `cross_validation`，包含 `execution_ids`
（按执行顺序）、`method`、`independence_basis`、`conclusion`。不同工具抓到同一
篇文章不自动构成独立证据，必须说明核验方法、独立性与冲突处理。

注意：机器校验不是事实裁判。它检查证据文件和记录的一致性；Agent 仍须阅读内容，
判断是否为登录墙、壳页面、目标错位或覆盖不足。不得把手写的通过理由当成采集实证。
