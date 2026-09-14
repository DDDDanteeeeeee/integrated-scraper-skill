# 续跑与内容验收

这些检查来自真实任务中的重复问题，不限定平台、品牌或本次研究主题。
沿用原任务计划与固定入口，不新增账号管理系统或平台适配器。

## 复用标签页

先通过已选浏览器工具读取本项目标签页库存。不要读取Cookie、个人Profile或其他项目浏览器。

1. 在原任务检查点记录无凭据目标URL、已观察到的target ID及待办动作。
   target ID只在本机本次会话有效，不能作为跨电脑配置。
2. 调用脚本的tabs模式，输入包含tabs、expected_url、previous_target_id。
   tabs只含当前任务相关标签的targetId和url。URL需要匹配路径与查询条件，不能
   只匹配域名或标题。需要签名的页面不持久化签名URL，改用浏览器内已知目标ID，
   并人工核对页面实际对象；不得为了自动匹配擅自删除查询条件。
3. reuse表示可以选择该标签，不表示已登录。切换后截图、核对实际目标和正文，
   再记录content_ready、login_required、challenge或unrendered。
4. inspect_candidates表示存在多个副本：逐一核对实际内容，再选择；不取数组第一项。
   target_missing表示原目标不在库存，先调查是否关闭或发生重定向，不自动新开并丢掉人工进度。
5. 首页、搜索页、详情页可能各自触发验证。只对实际目标验证通过的页面记录已恢复。
   用户本轮暂缓的平台保留未完成，不重复请求登录。

在PowerShell中运行UTF-8脚本，避免中文变成乱码：

```powershell
& ./.agents/skills/integrated-scraper/scripts/invoke_browser_harness.ps1 -ScriptPath <本次任务脚本路径>
```

该入口仍检查9222归属并持有浏览器锁，旧命令行模式保留。

## 格式、评论和时间

所有离线检查通过项目Python入口执行，不安装新的解析依赖。

```powershell
& ./.agents/skills/integrated-scraper/scripts/invoke_project_python.ps1 -PythonArguments @('.agents/skills/integrated-scraper/scripts/collection_quality.py','decode','--input','<原始JSON>','--scalar-list','--output','<新解析JSON>')
```

decode优先读取JSON。仅在实际输出已确认是单行键值列表时使用scalar-list；这不是
通用YAML解析器。多行、嵌套、标签和重复字段明确报错，不能用猜测填补。
保留原命令exit_code；即使解出正文，非零退出码也不因此变成业务成功。

DOM提取前先观察本页选择器，再使用collection_quality.comment_expression生成
只读表达式。每条正文必须满足其最近的评论容器就是当前容器，不能把子回复
正文归到已删除父评论。没有稳定评论ID时不能宣称完整去重。

评论数量检查输入格式如下。以下是合成示例，不是已采证据：

```json
{
  "page_state": "content_ready",
  "displayed_count": 1,
  "count_unit": "all_comment_nodes",
  "records": [{
    "id": "example-comment-1",
    "source_url": "https://example.org/discussion",
    "text_original": "Example source text",
    "removed": false
  }]
}
```

- displayed_count来自实际页面，不能拿脚本读到的条数反填。
- all_comment_nodes只在页面总数确实包含主评论、回复及占位时使用；口径不明则
  使用unknown，检查会保留count_not_comparable。主评论数不能与含回复总数直接对比。
- removed仅在页面明确显示删除占位时设置；正文须空，禁止恢复删除内容。
- 同一来源+ID重复、非占位空正文、数量差额或页面未就绪都会阻止完整度通过。
- 相同文字不同ID先保留，交由内容复核判断复制、转述或不同发言，不擅自合并。
- date_window只接受带时区的完整时间；月日、相对日期、无时区日期返回date_unconfirmed。
  内容复核可保留相对时间原文，不编造具体年份，也不把旧评论计为新增需求。

将数量检查输入另存为原始证据文件，附URL、采集时间和SHA256。新评论执行manifest
的result加入collection_check，值为对象，evidence_id指向该文件在evidence数组中的ID。
validate_run会重新计算检查结果，不相信手写的ok。数量相等仍需原文、日期、相关性和
归属验收。旧manifest兼容原证据契约，不补造新检查。

## 原文文档交付

分析报告和源数据MD是每次必交付的两份独立文档，执行记录另存。用户要求不在MD呈现采集失败时，
在对话直接反馈，JSON/TXT保留记录；MD保留必要样本范围，不谎称全量。

原文渲染输入为本次全部已采内容的records数组，不是分析精选。每条提供kind（comment/post/danmaku/article）、
platform、source_url、source_file（相对raw任务目录）、source_sha256、captured_at、
text_original；可选author_public、title、published_raw、context。context只写身份/日期等
内容边界，不放工具报错。include默认true；仅重复、安全敏感、非内容噪声或删除占位
可用include=false并填写exclusion_reason为duplicate/sensitive/non_content/removed，
排除详情保留在JSON。不能因“无价值”、超期或无日期而不归档已经取得的内容。

同一帖子/视频用page_url归组、page_title作标题；评论保留id，有实际父子关系时
提供parent_id。原始关系未知不得编造。每条只显示类型、作者、发表时间和原文，
回复标注回复对象；公共说明不逐条重复。采集时间及哈希按源文件集中在文末。
页面导航、按钮、推荐栏等不混入内容正文；清理仅针对界面噪声，原始文件不改。
同文不同作者/ID不能因为看起来重复而删除；不同采集快照重复记录须保留排除依据。

源内容清单须逐个核对本次原始文件，记录全部内容（含安全排除项）。渲染器能验证
清单到文档的一致性，但不能证明上游清单未漏读文件；这一步由Agent复核并记录。

```powershell
& ./.agents/skills/integrated-scraper/scripts/invoke_project_python.ps1 -PythonArguments @('.agents/skills/integrated-scraper/scripts/collection_quality.py','render','--input','<已复核原文清单JSON>','--run-dir','<raw任务目录>','--output','<新原文MD>')
```

渲染前检查凭据、签名链接、二维码和无关账号内容。不要把完整运行目录盲目交付。
脚本检查源文件哈希、路径范围及原文非空，拒绝错误日志、删除占位和覆盖已有文件。
最终必须以validate_run.py的--final-delivery模式验收，并传入--analysis-report、
--source-document和--source-records；缺文档、文档相同、源文档与清单不一致均失败。
旧运行的结构检查仍可不传此开关，但不能将其作为新交付的验收。
结构检查结果明确返回validation_scope=structure_only、delivery_passed=false；
只有最终交付模式且全部校验通过才返回delivery_passed=true。
无内容时同样生成源数据MD，写明无可展示内容，不把采集失败解释为平台零数据。
原文放入不会执行HTML的代码围栏；本地源链接使用相对路径。归档时一起保留raw与reports
相对布局；这是文档可移植，不表示其他电脑无需安装依赖。

## 回归与新电脑边界

先跑离线回归，再做本机目标能力实测。每台新电脑仍需按初始化文档生成本机配置，
不能复制collection.local.json或浏览器Profile，也不能从一次本机通过推断全平台通过。

```powershell
& ./.agents/skills/integrated-scraper/scripts/invoke_project_python.ps1 -PythonArguments @('-m','unittest','discover','-s','tests','-v')
```

验收分别记录：离线合成数据、本机已有证据回放、真实浏览器、实际登录续跑、
新电脑完整安装。未执行的项目明确写未验证，不更改历史状态来制造通过。
