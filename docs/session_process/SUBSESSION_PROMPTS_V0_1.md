# 子会话启动提示词 v0.1

用途：当需要你在 Codex 中新建子会话时，复制对应提示词作为第一条消息。

所有提示词都默认要求：

```text
先不要写代码。先阅读指定文档和相关文件，输出计划，等待确认后再实现。
```

注意：`docs/session_process/README.md` 和 `docs/CODEX_PROGRESS_BOARD_V0_1.md` 中，S07-S10 以后按当前执行顺序命名；如果与 `docs/DEVELOPMENT_BACKLOG_V0_1.md` 的 Milestone 编号存在不一致，子会话必须先指出差异，再以本启动提示词的 Goal / Scope / Done when 作为当前任务边界。

---

## S00：仓库初始化会话

```text
你是“仓库初始化会话 S00”。

Goal:
补齐项目基础目录和仓库工程文件，为后续后端和 Android 开发建立稳定起点。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md
- docs/DEVELOPMENT_BACKLOG_V0_1.md
- docs/CODEX_WORKFLOW_V0_1.md
- docs/session_process/README.md

Scope:
允许创建或修改：
- README.md
- .gitignore
- .env.example
- scripts/
- .github/pull_request_template.md
- docs/CODEX_PROGRESS_BOARD_V0_1.md

Constraints:
- 不写业务代码。
- 不创建 backend 实现文件。
- 不创建 Android 实现文件。
- 不引入真实 secret。
- 不改变儿童安全原则。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试或验证方式、潜在风险。计划确认后再执行。
```

---

## S01：后端骨架会话

```text
你是“后端骨架会话 S01”。

Goal:
创建 backend FastAPI 项目骨架，实现 /api/v1/health 和 /api/v1/conversation/message 的 mock 流程。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 1
- docs/CODEX_WORKFLOW_V0_1.md 的阶段 1
- docs/CODEX_TASK_PROMPTS_V0_1.md 的 M1
- docs/session_process/README.md

Environment:
使用 Conda 环境：
conda activate child-ai

Scope:
允许创建：
- backend/README.md
- backend/pyproject.toml
- backend/app/main.py
- backend/app/api/v1/health.py
- backend/app/api/v1/conversation.py
- backend/app/core/config.py
- backend/app/core/logging.py
- backend/app/domain/schemas/conversation.py
- backend/app/services/conversation_service.py
- backend/app/tests/test_health.py
- backend/app/tests/test_conversation_mock.py
- 必要的 __init__.py

Constraints:
- 不接真实大模型。
- 不接数据库。
- 不实现完整 TimeContextService。
- 不实现完整 IntentClassifier。
- 不实现完整 SceneOrchestrator。
- API route 只调用 service，不堆业务逻辑。
- mock 回复不得要求孩子保密，不得直接给学习答案。

Done when:
- GET /api/v1/health 返回 {"status":"ok"}。
- POST /api/v1/conversation/message 返回 mock reply、ui_actions、session_state。
- python -m pytest 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S02：时间与父亲策略会话

```text
你是“时间与父亲策略会话 S02”。

Goal:
实现 TimeContextService 和 ParentPolicyService，使每次 conversation/message 能注入 time_context 和 parent_policy。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Context Builder、父亲策略、动态场景编排部分
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 2
- docs/session_process/README.md
- backend 当前代码

Scope:
允许修改 backend 中与时间上下文、父亲策略、conversation context 注入相关的文件。

Constraints:
- 可先用内存存储，不上复杂数据库迁移。
- 时间段配置不能散落硬编码。
- 不接真实模型。
- 不改变 conversation API 的核心字段，必要新增 debug 字段需说明。

Done when:
- 16:30 -> after_school。
- 20:45 -> bedtime。
- /api/v1/parent/policy GET/POST 可用。
- conversation/message 能读取父亲目标。
- pytest 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S03：模型注册与 Mock Provider 会话

```text
你是“模型注册与 Mock Provider 会话 S03”。

Goal:
实现可配置模型抽象层。业务代码只能通过 ModelRegistry 调用模型，默认使用 MockModelProvider。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Model Registry 和模型 Provider 部分
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 3
- docs/session_process/README.md
- backend 当前代码

Scope:
允许创建或修改：
- backend/app/domain/model_types.py
- backend/app/providers/model/
- backend/app/services/model_registry.py
- backend/app/tests/test_model_registry.py
- backend/app/tests/test_mock_model_provider.py

Constraints:
- 不引入真实 API key。
- OpenAICompatibleProvider 只能做接口骨架，默认 disabled。
- 测试不得调用真实网络。
- 不改变 conversation API 返回结构，除非计划中说明。

Done when:
- ModelRegistry 可按 task_type 返回 MockModelProvider。
- MockModelProvider 可返回固定结构化结果。
- provider 异常时可 fallback。
- pytest 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S04：Prompt 管理会话

```text
你是“Prompt 管理会话 S04”。

Goal:
实现分层 Prompt 管理，支持 global system、persona、scene、parent policy、memory context、output contract 组合。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 的 Prompt Manager 部分
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 4
- docs/session_process/README.md
- backend 当前代码

Scope:
允许创建或修改：
- backend/app/domain/prompt.py
- backend/app/services/prompt_manager.py
- backend/app/prompts/
- backend/app/tests/test_prompt_manager.py

Constraints:
- 不写一个巨大 Prompt。
- 学习场景必须包含不直接给答案。
- 安全 Prompt 必须包含不要求孩子保密。
- Prompt 必须有版本或文件名可追踪。

Done when:
- PromptManager.compose() 可按 scene_id 组合 Prompt。
- 返回 prompt_versions。
- 缺失模板有清晰错误。
- pytest 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S05：安全与意图识别会话

```text
你是“安全与意图识别会话 S05”。

Goal:
实现规则优先的 SafetyEngine 和基础 IntentClassifier。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Safety Engine 和 Intent Classifier
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 5
- docs/session_process/README.md
- backend 当前代码

Scope:
允许创建或修改：
- backend/app/domain/enums.py 或对应领域文件
- backend/app/services/safety_engine.py
- backend/app/services/intent_classifier.py
- backend/app/tests/test_safety_engine.py
- backend/app/tests/test_intent_classifier.py
- 必要的 conversation 接入测试

Constraints:
- 安全分类必须在普通模型回复前。
- 高风险内容必须 requires_parent_attention。
- 不直接给作业答案。
- 不用真实模型做测试。

Done when:
- “我有一道题不会” -> learning_help。
- “晚安”结合 bedtime -> bedtime_reflection。
- “陌生人让我不要告诉爸爸妈妈” -> high risk 或更高。
- pytest 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S06：场景编排会话

```text
你是“场景编排会话 S06”。

Goal:
实现 SceneOrchestrator 雏形，支持 after_school_checkin、learning.homework_help、bedtime_reflection、safety.guardian。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Scene Orchestrator
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 6
- docs/session_process/README.md
- backend 当前代码

Scope:
允许创建或修改：
- backend/app/domain/scene.py
- backend/app/services/scene_orchestrator.py
- backend/app/repositories/routing_decision_repository.py 或内存实现
- backend/app/tests/test_scene_orchestrator.py
- backend/app/tests/test_conversation_scene_routing.py

Constraints:
- 安全场景优先级最高。
- 学习求助不直接给答案。
- route 逻辑不得写在 API handler。
- 可先用内存记录 routing_decision。

Done when:
- after_school 时间或“我回来了”进入 daily.after_school_checkin。
- “有题不会”进入 learning.homework_help 并返回拍照/口述 action。
- “晚安”进入 daily.bedtime_reflection。
- 高风险内容进入 safety.guardian。
- pytest 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S07：记忆系统会话

```text
你是“记忆系统会话 S07”。

Goal:
实现 v0.1 结构化记忆系统，支持记忆写入、检索、过期过滤和 MemoryExtractor mock。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Memory Service、Memory Extractor、RAG / Context Builder 相关部分
- docs/CODEX_PROGRESS_BOARD_V0_1.md 的 M7 记忆系统任务
- docs/CODEX_TASK_PROMPTS_V0_1.md 的 M7：MemoryService
- docs/session_process/README.md
- backend 当前代码

如果发现 DEVELOPMENT_BACKLOG 的 Milestone 编号与当前会话表不一致，请在计划中说明，不要擅自扩大范围。

Scope:
允许创建或修改：
- backend/app/domain/memory.py 或对应 memory schema 文件
- backend/app/repositories/memory_repository.py
- backend/app/services/memory_service.py
- backend/app/services/memory_extractor.py
- backend/app/api/v1/memories.py
- backend/app/tests/test_memory_service.py
- backend/app/tests/test_memory_extractor_mock.py
- backend/app/tests/test_memory_api.py
- 必要的 __init__.py

Constraints:
- 不保存真实长篇原始聊天为长期记忆。
- 不保存原始音频、原始照片。
- 不给孩子贴固定负面人格标签。
- 不把内向视为缺陷。
- 记忆必须包含 evidence、confidence、created_at，并支持 expires_at。
- 高风险记忆必须能标记 sensitivity / requires_parent_attention / visible_to_parent。
- v0.1 优先使用内存 repository，不做数据库迁移，除非计划中说明并获得确认。
- 不接真实模型，不调用外部网络。

Done when:
- MemoryService 支持 create / list / update / delete 或明确说明 v0.1 最小子集。
- MemoryExtractor mock 能输出结构化记忆。
- 支持 interest / learning_pattern / expression_pattern / emotion_observation / strategy 或等价类型。
- 过期记忆不会被普通检索返回。
- /api/v1/memories/{child_id} 可读，父亲可以删除错误记忆。
- pytest 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S08：父亲日报会话

```text
你是“父亲日报会话 S08”。

Goal:
实现 ParentReportService 和父亲日报 API，基于会话摘要、结构化记忆和安全提醒生成父亲可读的每日摘要。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Parent Console、Parent Report Service、Memory Service 相关部分
- docs/CODEX_PROGRESS_BOARD_V0_1.md 的 M8 父亲日报任务
- docs/CODEX_TASK_PROMPTS_V0_1.md 的 M8：ParentReportService
- docs/session_process/README.md
- backend 当前代码，尤其是 MemoryService 当前实现

如果发现 DEVELOPMENT_BACKLOG 的 Milestone 编号与当前会话表不一致，请在计划中说明，不要擅自扩大范围。

Scope:
允许创建或修改：
- backend/app/domain/parent_report.py 或对应 parent report schema 文件
- backend/app/services/parent_report_service.py
- backend/app/api/v1/parent_report.py 或 backend/app/api/v1/parent_reports.py
- backend/app/tests/test_parent_report_service.py
- backend/app/tests/test_parent_report_api.py
- 必要的 conversation / memory 接入测试

Constraints:
- 父亲日报不是逐字聊天监控，不输出完整原始聊天记录。
- 不输出“胆小”“不合群”“懒”“不聪明”等负面人格标签。
- 不把内向视为缺陷。
- 必须包含父亲可执行建议，而不是泛泛评价。
- 高风险提醒要清晰，但不要过度暴露无关儿童原始数据。
- v0.1 可以使用 mock summary，不接真实模型。
- 不引入账号系统或复杂权限系统。

Done when:
- 可按 child_id 和 date 生成或读取当天日报。
- 日报包含 summary、learning_observations、expression_observations、emotion_observations、safety_alerts、suggested_parent_actions。
- 普通日报和高风险日报都有测试。
- API 测试验证不返回完整逐字聊天记录。
- pytest 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S09：附件与 Mock OCR 会话

```text
你是“附件与 Mock OCR 会话 S09”。

Goal:
实现拍题附件流程的后端占位能力，包括 attachment API、Mock OCR provider，并接入学习求助题意确认流程。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Modality Manager、OCR、拍照题目和学习求助相关部分
- docs/CODEX_PROGRESS_BOARD_V0_1.md 的 M9 附件/OCR 任务
- docs/CODEX_TASK_PROMPTS_V0_1.md 的 M9：Attachment 和 Mock OCR
- docs/session_process/README.md
- backend 当前代码，尤其是 SceneOrchestrator、conversation schema、learning.homework_help

如果发现 DEVELOPMENT_BACKLOG 的 Milestone 编号与当前会话表不一致，请在计划中说明，不要擅自扩大范围。

Scope:
允许创建或修改：
- backend/app/domain/attachment.py 或对应 attachment schema 文件
- backend/app/api/v1/attachment.py 或 backend/app/api/v1/conversation_attachment.py
- backend/app/providers/ocr/base.py
- backend/app/providers/ocr/mock_ocr_provider.py
- backend/app/services/attachment_service.py
- backend/app/services/modality_manager.py
- backend/app/repositories/attachment_repository.py
- backend/app/tests/test_attachment_api.py
- backend/app/tests/test_mock_ocr_provider.py
- backend/app/tests/test_learning_help_with_attachment.py

Constraints:
- 不接真实 OCR。
- 不接真实相机。
- 不长期保存真实图片。
- 不在日志、fixture 或测试里写入真实儿童身份信息。
- 拍题流程不得直接给最终答案，必须先引导孩子复述题意或说明卡点。
- 低置信度 OCR 必须返回重拍或口述建议。
- 外部能力适配必须放在 providers/，业务编排放在 services/。

Done when:
- POST /api/v1/conversation/attachment 可接收 homework_photo mock attachment。
- Mock OCR 返回 recognized_content 和 confidence。
- 高置信度时进入题意确认，不直接解题。
- 低置信度时请求重拍或口述题目。
- 学习求助流程可通过 attachment_id 或等价 mock 数据继续引导。
- pytest 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S10：后端质量与演示会话

```text
你是“后端质量与演示会话 S10”。

Goal:
补齐后端核心场景测试、演示脚本和本地质量检查，让 Q1 后端 MVP 可以稳定验收。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 v0.1 用户故事和第一轮测试用例
- docs/CODEX_WORKFLOW_V0_1.md 的工程闭环和测试要求
- docs/CODEX_TASK_PROMPTS_V0_1.md 的 Q1：后端 Scenario Tests 和 CI
- docs/session_process/README.md
- backend 当前代码
- scripts/ 当前脚本

Scope:
允许创建或修改：
- backend/app/tests/test_scenarios_v0_1.py 或 backend/app/tests/scenarios/
- scripts/test_backend.sh
- scripts/lint_backend.sh
- scripts/dev_backend.sh
- scripts/demo_backend_scenarios.sh
- backend/README.md
- docs/CODEX_PROGRESS_BOARD_V0_1.md

如需新增 .github/workflows/backend-ci.yml，必须先在计划中说明；当前项目没有远端 GitHub 时，优先保证本地脚本和 README。

Constraints:
- 不新增产品功能，除非是为了补齐可测性且计划中说明。
- 不接真实模型、真实 OCR 或真实外部网络。
- demo 和测试只能使用安全的假数据，不写真实儿童身份信息。
- 不改变 conversation API 顶层 schema，除非计划中说明并获得确认。
- 不删除已有测试来让新测试通过。

Done when:
- 场景测试覆盖放学后、学习求助、直接要答案、不想说话、高风险安全、睡前复盘、父亲目标影响回复、模型 fallback。
- 本地 test_backend 和 lint_backend 脚本可运行并结果明确。
- demo_backend_scenarios 能演示核心 API 行为。
- backend README 更新本地运行和验证方式。
- pytest 和 ruff 通过。

Output:
先输出计划，列出会修改的文件、不会修改的文件、测试策略、潜在风险。计划确认后再执行。
```

---

## S11：Android 壳会话

```text
你是“Android 壳会话 S11”。

Goal:
初始化 Android Kotlin + Jetpack Compose 壳项目，先做静态聊天入口，不接真实 API。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Android Tablet App
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Android MVP
- docs/session_process/README.md

Scope:
允许创建或修改 android/。

Constraints:
- Android 端是统一智能体入口，不做功能按钮堆叠。
- 第一版不要复杂动画。
- 不做账号系统。
- 不放任何模型 API key。
- 所有 AI 决策后续由后端完成。

Done when:
- Android 项目可编译。
- 有静态聊天界面。
- 有文本输入框和消息列表占位。
- 有卡通智能体形象占位。

Output:
先输出计划，列出会修改的文件、不会修改的文件、验证方式、潜在风险。计划确认后再执行。
```

---

## S12：Android API 接入会话

```text
你是“Android API 接入会话 S12”。

Goal:
让 Android ChildChatScreen 调用后端 /api/v1/conversation/message，并渲染 reply、ui_actions 和 session_state。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Android Tablet App、Conversation Gateway、API 设计相关部分
- docs/CODEX_PROGRESS_BOARD_V0_1.md 的 A2 Android API 任务
- docs/CODEX_TASK_PROMPTS_V0_1.md 的 A2：Android 接入后端 Conversation API
- docs/session_process/README.md
- backend/README.md
- android/README.md
- 当前 Android 项目结构

Scope:
允许创建或修改 android/ 中与网络请求、DTO、Repository、ViewModel、聊天页面状态渲染相关的文件。
如发现后端 API schema 与 Android 需求不一致，先在计划中说明；不要直接大改 backend。

Constraints:
- Android 端不放任何模型 API key。
- Android 端不做 AI 决策、不做安全分类、不做场景路由，只展示后端返回结果。
- 不实现账号系统。
- 后端 base URL 通过开发配置或 README 手动说明，不写真实 secret。
- 网络失败时显示温和错误，不诱导孩子反复尝试。
- 不接真实相机和真实语音作为必需功能。

Done when:
- Android 发送 POST /api/v1/conversation/message。
- 输入“我回来了”能显示后端回复。
- 输入“我有一道题不会”能显示“拍题目 / 读题目”或等价 ui_actions。
- session_state 可被保存或用于下一轮请求。
- Android 可编译，或如本机缺少 Android SDK，给出明确手动验证步骤和阻塞原因。

Output:
先输出计划，列出会修改的文件、不会修改的文件、验证方式、潜在风险。计划确认后再执行。
```

---

## S13：Android 拍题与父亲页会话

```text
你是“Android 拍题与父亲页会话 S13”。

Goal:
实现 Android 端 mock 拍题流程、父亲设置页和父亲日报页，使 Android 能演示学习求助与父亲治理闭环。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 中 Android Tablet App、父亲端、拍照题目、多模态相关部分
- docs/CODEX_PROGRESS_BOARD_V0_1.md 的 A3 / A4 任务
- docs/CODEX_TASK_PROMPTS_V0_1.md 的 A3：Android Mock 拍题流程 和 A4：父亲设置页
- docs/session_process/README.md
- backend 的 conversation、attachment、parent policy、parent report API 文档或 schema
- 当前 Android 项目结构

Scope:
允许创建或修改 android/ 中与以下功能相关的文件：
- mock 拍题入口和状态流
- attachment API client / DTO / repository
- ParentSettingsScreen
- ParentPolicy API client / DTO / ViewModel
- ParentReport screen 或可替换的只读 stub
- README 手动验证说明

Constraints:
- 拍题优先 mock，不接真实 CameraX，除非计划中单独说明并获得确认。
- 不长期保存真实图片。
- 不直接展示最终作业答案。
- 父亲设置只配置后端策略，不在 Android 端复制 AI 决策逻辑。
- 不展示孩子完整逐字聊天记录。
- 不引入排行榜、积分或上瘾式机制。

Done when:
- 点击“拍题目”可走 mock attachment 流程，并展示后端题意引导。
- 父亲设置页可读取并更新目标、沟通偏好和作息时间。
- 父亲日报页可显示后端 summary；如果后端未完成对应 API，必须明确作为 stub 并写入 README。
- Android 可编译，或如本机缺少 Android SDK，给出明确手动验证步骤和阻塞原因。

Output:
先输出计划，列出会修改的文件、不会修改的文件、验证方式、潜在风险。计划确认后再执行。
```

---

## S14：端到端联调会话

```text
你是“端到端联调会话 S14”。

Goal:
完成 Mac mini 本机后端 + Android 平板或模拟器的 v0.1 端到端联调，验证家庭内测核心流程。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md
- docs/CODEX_WORKFLOW_V0_1.md 的端到端联调和测试要求
- docs/CODEX_PROGRESS_BOARD_V0_1.md 的 E2E 任务
- docs/CODEX_TASK_PROMPTS_V0_1.md 的 E2E：端到端联调
- docs/session_process/README.md
- backend/README.md
- android/README.md
- scripts/ 当前脚本

Scope:
允许创建或修改：
- docs/MANUAL_QA_V0_1.md 或 docs/E2E_TEST_PLAN_V0_1.md
- backend/README.md
- android/README.md
- scripts/ 中必要的本地启动或验证脚本
- backend / android 中发现的联调阻塞 bug 的最小修复

Constraints:
- 不扩大产品范围。
- 不接真实模型作为默认行为。
- 不在 Android 端放任何模型 API key。
- 不使用真实儿童数据、真实家庭信息或真实照片作为测试材料。
- 只修复联调阻塞 bug；较大的功能缺口记录为后续任务。
- 如果 Android 设备无法访问 Mac mini 后端，先记录网络和 base URL 排查结果。

Done when:
- Android 设备或模拟器可访问 /api/v1/health。
- 文字聊天可跑通放学后、学习求助、睡前复盘和高风险安全场景。
- mock 拍题流程可从 Android 触发到后端题意引导。
- 父亲策略更新能影响后续 conversation 行为或 debug。
- 手动 QA 文档记录通过项、失败项、环境信息和已知问题。
- 后端 pytest / ruff 通过；Android build/test 如环境可用则通过，否则明确记录阻塞。

Output:
先输出联调计划，列出会修改的文件、不会修改的文件、验证步骤、潜在风险。计划确认后再执行。
```
