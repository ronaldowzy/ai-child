# 子会话启动提示词 v0.1

用途：当需要你在 Codex 中新建子会话时，复制对应提示词作为第一条消息。

所有提示词都默认要求：

```text
先不要写代码。先阅读指定文档和相关文件，输出计划，等待确认后再实现。
必须先阅读 docs/session_process/SHARED_CONTEXT_V0_1.md，并运行 bash scripts/doctor_local_env.sh。
遇到环境问题时，先使用共享上下文里的标准入口命令复跑，不要只根据裸命令失败报告阻塞。
```

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
- docs/session_process/SHARED_CONTEXT_V0_1.md

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
- Android 验证优先使用 bash scripts/android_gradle.sh test assembleDebug。

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
- docs/session_process/SHARED_CONTEXT_V0_1.md
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
- Android 可编译；如失败，必须先用 bash scripts/android_gradle.sh 复跑，再给出明确手动验证步骤和阻塞原因。

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
- docs/session_process/SHARED_CONTEXT_V0_1.md
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
- Android 可编译；如失败，必须先用 bash scripts/android_gradle.sh 复跑，再给出明确手动验证步骤和阻塞原因。

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
- docs/session_process/SHARED_CONTEXT_V0_1.md
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
- 后端 pytest / ruff 通过；Android build/test 必须优先使用 bash scripts/android_gradle.sh。只有标准入口也失败时，才能明确记录环境阻塞。

Output:
先输出联调计划，列出会修改的文件、不会修改的文件、验证步骤、潜在风险。计划确认后再执行。
```

---

## S15：ChildAgentRuntime 会话

```text
你是 ai-child 项目的“ChildAgentRuntime 子会话 S15”。

目标:
把主 conversation 回复链路从 SceneOrchestrator 直接返回 hardcoded reply，升级为 SceneOrchestrator 决定策略和 fallback，ChildAgentRuntime 负责 PromptManager + ModelRegistry 生成回复、输出安全检查和 fallback。

允许文件:
- backend/app/services/child_agent_runtime.py
- backend/app/domain/agent_runtime.py（如确有必要）
- backend/app/services/conversation_service.py
- backend/app/providers/model/mock_provider.py
- backend/app/tests/** 中 runtime、conversation 回归测试
- backend/README.md

禁止文件:
- android/**
- backend/app/services/scene_orchestrator.py，除非只补充兼容字段且先说明
- 任何真实 secret、本地 .env、真实 API key
- 默认启用真实模型外发

依赖:
- S16 模型外发安全闸门已完成。
- PromptManager、ModelRegistry、SafetyEngine、SceneOrchestrator 已存在。

测试计划:
- 先运行 bash scripts/doctor_local_env.sh。
- pytest 覆盖 runtime 正常调用 PromptManager + ModelRegistry、provider 失败 fallback、空文本 fallback、输出 HIGH/CRITICAL fallback、学习场景不直接给答案、prompt_versions/metadata 可追踪。
- 运行 bash scripts/test_backend.sh -q。
- 运行 bash scripts/lint_backend.sh。

Safety note:
SceneRouteDecision.reply_text 是安全 fallback，不能删除。模型请求 metadata 必须标记 contains_child_data=true。输出必须经过 SafetyEngine.classify_output，不安全或失败时回落到 scene fallback。

共享上下文更新项:
- 是否发现 runtime 顺序、prompt_versions、model fallback 或 output safety 的共性坑。
- 是否需要更新 SHARED_CONTEXT_V0_1.md、backend/README.md 或进度板。
- 标准入口命令和结果。

Output:
先输出实现计划，列出会修改的文件、不会修改的文件、测试策略和潜在风险。计划确认后再执行。
```

---

## S16：模型外发安全闸门会话

```text
你是 ai-child 项目的“模型外发安全闸门子会话 S16”。

目标:
真实外部模型 Provider 即使 enabled，也不能在儿童数据安全条件不满足时外发 child data。策略不满足时必须在 provider 调用前 fallback mock 或抛出清晰错误。

允许文件:
- backend/app/services/model_data_policy_guard.py 或 backend/app/services/model_policy_guard.py
- backend/app/services/model_registry.py
- backend/app/domain/model_types.py（仅必要字段）
- backend/app/tests/test_model_registry.py
- backend/app/tests/test_openai_compatible_provider.py
- backend/app/tests/test_model_data_policy_guard.py（如新增）
- backend/README.md
- .env.example

禁止文件:
- backend/app/services/conversation_service.py
- backend/app/services/scene_orchestrator.py
- backend/app/services/safety_engine.py
- android/**
- 任何真实 API key、真实儿童数据、真实家庭信息

依赖:
- ModelRegistry 和 OpenAICompatibleProvider 已存在。
- 真实 provider 默认 disabled，测试不得真实联网。

测试计划:
- 先运行 bash scripts/doctor_local_env.sh。
- pytest 覆盖 Mimo child data 未授权不调用 urlopen、retention 未确认不调用 urlopen、策略完整时可进入 fake provider、image/audio gate、mock provider bypass、无 fallback 抛错。
- 运行 bash scripts/test_backend.sh -q。
- 运行 bash scripts/lint_backend.sh。

Safety note:
外部传输策略是儿童数据出境前硬闸门。不得把真实 key 写入仓库，不得把真实模型设为默认，不得让测试依赖真实网络。

共享上下文更新项:
- 是否发现模型开关、环境变量、provider fallback、外发 gate 的共性坑。
- 是否需要更新 SHARED_CONTEXT_V0_1.md 或 backend/README.md。
- 标准入口命令和结果。

Output:
先输出实现计划，列出会修改的文件、不会修改的文件、测试策略和潜在风险。计划确认后再执行。
```

---

## S17：自动记忆闭环会话

```text
你是 ai-child 项目的“自动记忆闭环子会话 S17”。

目标:
让 conversation 主流程自动产生结构化 memory，支撑父亲日报和下一轮对话上下文。v0.1 先做规则型记忆，不急着用真实 LLM 抽取。

允许文件:
- backend/app/services/conversation_memory_hooks.py
- backend/app/services/conversation_service.py
- backend/app/services/memory_service.py
- backend/app/services/parent_report_service.py
- backend/app/tests/** 中 memory、conversation、parent report 回归测试
- backend/README.md

禁止文件:
- android/**
- 真实数据库迁移或持久化方案，除非先提交计划并等待确认
- 保存 raw_chat、full_chat、真实音频、真实照片或真实身份信息
- 把 safety 记忆默认混入普通 retrieve

依赖:
- S15 ChildAgentRuntime 合并后再做。
- S18 安全场景细分合并后更稳；如果主控要求提前做，必须显式标出适配风险。

测试计划:
- 先运行 bash scripts/doctor_local_env.sh。
- pytest 覆盖学习求助记忆、直接要答案记忆、不想说话情绪观察、高风险 safety memory、父亲日报读取自动 memory、evidence 不含 raw/full transcript 禁用 source。
- 运行 bash scripts/test_backend.sh -q。
- 运行 bash scripts/lint_backend.sh。

Safety note:
记忆只能保存有限、结构化、可解释、可过期的信息。证据必须是 summary，不保存长篇逐字原文，不贴固定负面人格标签，不把内向当缺陷。

共享上下文更新项:
- 是否发现内存态重启丢失、memory/report hook 顺序、测试 fixture 的共性坑。
- 是否需要更新 SHARED_CONTEXT_V0_1.md、backend/README.md 或 MANUAL_QA_V0_1.md。
- 标准入口命令和结果。

Output:
先输出实现计划，列出会修改的文件、不会修改的文件、测试策略和潜在风险。计划确认后再执行。
```

---

## S18：安全场景细分会话

```text
你是 ai-child 项目的“安全场景细分子会话 S18”。

目标:
把当前安全路由从较粗的 safety.guardian 细化为 HIGH/CRITICAL -> safety.guardian，WATCH -> safety.gentle_checkin，LOW privacy -> privacy.boundary，LOW mental distress -> 温和情绪支持。

允许文件:
- backend/app/domain/enums.py
- backend/app/domain/scene.py
- backend/app/services/safety_engine.py
- backend/app/services/intent_classifier.py
- backend/app/services/scene_orchestrator.py
- backend/app/prompts/scenes/**
- backend/app/tests/** 中 safety、intent、scene、conversation scenario 测试

禁止文件:
- android/**
- backend/app/services/conversation_service.py，除非主控确认接口协调
- 模型 provider 真实外发配置
- 任何真实儿童安全案例、真实身份信息或真实聊天原文
- 放宽“不要求保密”“鼓励告诉可信成人”“父亲提醒”的底线

依赖:
- S15 ChildAgentRuntime 合并后更稳。
- M5/M6 安全与场景编排基础已完成。

测试计划:
- 先运行 bash scripts/doctor_local_env.sh。
- pytest 覆盖陌生人保密 -> guardian、同学骂我 -> gentle_checkin、我不想说话 -> 不进 guardian、家庭住址 -> privacy.boundary、直接要答案仍 learning.homework_help。
- 运行 bash scripts/test_backend.sh -q。
- 运行 bash scripts/lint_backend.sh。

Safety note:
不得让 AI 要求孩子保密，不得鼓励隐瞒父母/老师/可信成人。HIGH/CRITICAL 必须触发 requires_parent_attention；WATCH 不应全部粗暴升级为强 guardian。

共享上下文更新项:
- 是否发现安全测试句、风险类别、父亲提醒策略的共性坑。
- 是否需要更新 SHARED_CONTEXT_V0_1.md、MANUAL_QA_V0_1.md 或进度板。
- 标准入口命令和结果。

Output:
先输出实现计划，列出会修改的文件、不会修改的文件、测试策略和潜在风险。计划确认后再执行。
```

---

## S19：Android 父亲入口保护会话

```text
你是 ai-child 项目的“Android 父亲入口保护子会话 S19”。

目标:
在不引入账号系统的前提下，为 Android 父亲设置页和父亲日报页增加 v0.1 基础入口保护。建议采用长按父亲入口 -> 输入 dev PIN -> 进入父亲模式。

允许文件:
- android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
- android/app/src/main/java/com/childai/companion/ui/AppNavHost.kt
- android/app/src/main/java/com/childai/companion/config/DevSettings.kt
- android/app/src/main/java/com/childai/companion/ui/parent/**
- android/app/src/test/**
- android/README.md

禁止文件:
- backend/**
- 真实账号系统、云端登录、支付、广告或社交能力
- Android 端模型 API key 或真实 secret
- 展示孩子完整逐字聊天记录

依赖:
- A4 父亲设置/日报页面已完成。
- docs/session_process/SHARED_CONTEXT_V0_1.md 中 Android 标准入口。

测试计划:
- 先运行 bash scripts/doctor_local_env.sh。
- 运行 bash scripts/android_gradle.sh test assembleDebug lintDebug。
- 如能操作设备，手动 QA：点击不直接进入，长按弹 PIN，错误 PIN 温和提示，正确 PIN 进入。

Safety note:
父亲入口保护是治理边界，不是账号系统或强安全机制。不得在客户端保存模型 API key，不得把父亲日报变成逐字监控，不得用惩罚性语言或诱导孩子长时间使用。

共享上下文更新项:
- 是否发现 Android 环境、Gradle、AVD、UI 手动 QA 的共性坑。
- 是否需要更新 SHARED_CONTEXT_V0_1.md、android/README.md 或 MANUAL_QA_V0_1.md。
- 标准入口命令和结果。

Output:
先输出实现计划，列出会修改的文件、不会修改的文件、测试策略和潜在风险。计划确认后再执行。
```

---

## S20：文档同步与多会话协同会话

```text
你是 ai-child 项目的“文档同步与多会话协同子会话 S20”。如果主控指定 S20a/S20b，以主控指定的轮次目标为准。

目标:
修正文档与真实工程状态不一致的问题，维护进度板、共享上下文、工作流和子会话提示词，确保并行会话知道当前状态、文件所有权、merge gate、标准入口命令和新发现共性坑的交接方式。

允许文件:
- README.md
- docs/CODEX_PROGRESS_BOARD_V0_1.md
- docs/MANUAL_QA_V0_1.md
- docs/session_process/SHARED_CONTEXT_V0_1.md
- docs/CODEX_WORKFLOW_V0_1.md
- docs/CODEX_TASK_PROMPTS_V0_1.md
- docs/session_process/SUBSESSION_PROMPTS_V0_1.md

禁止文件:
- backend/app/**
- android/app/**
- 任何真实 secret、本地 .env、真实儿童身份信息、真实照片或真实音频
- 把 todo 写成 done，或把 mock 能力写成真实生产能力

依赖:
- AGENTS.md
- docs/session_process/README.md
- docs/session_process/SHARED_CONTEXT_V0_1.md
- docs/CODEX_PROGRESS_BOARD_V0_1.md
- README.md
- backend/README.md
- android/README.md
- docs/MANUAL_QA_V0_1.md
- 主控会话提供的当前阶段说明

测试计划:
- 先运行 bash scripts/doctor_local_env.sh。
- 文档修改后运行 git diff --check。
- 运行主控指定的过期表述扫描命令，覆盖 README.md、docs、backend/README.md、android/README.md 中的旧阶段和未初始化类表述。
- 如果扫描命中合理历史引用，必须在交接中说明。

Safety note:
文档不得削弱儿童安全底线。必须明确 Mock 优先、真实模型默认关闭、Android 不放 API key、学习不直接给答案、父亲日报不展示逐字聊天记录。

共享上下文更新项:
- 是否发现新的共性坑。
- 是否已经写入 SHARED_CONTEXT_V0_1.md，或是否需要主控确认后写入。
- 是否更新文件所有权矩阵、merge gate 或标准入口命令。

Output:
先输出文档同步计划，列出会修改的文件、不会修改的文件、验证方式和风险。计划确认或主控授权后执行。
```
