# Codex 任务 Prompt 清单 v0.1

版本：v0.1 Draft  
用途：给 Codex 直接复制粘贴使用的任务指令库  
关联文档：

```text
AGENTS.md
docs/SYSTEM_DESIGN_V0_1.md
docs/DEVELOPMENT_BACKLOG_V0_1.md
docs/CODEX_WORKFLOW_V0_1.md
```

---

## 0. 使用规则

每个任务开始前，让 Codex 先阅读：

```text
AGENTS.md
docs/SYSTEM_DESIGN_V0_1.md
docs/DEVELOPMENT_BACKLOG_V0_1.md
docs/CODEX_WORKFLOW_V0_1.md
```

除非任务非常小，否则都要加：

```text
先不要写代码。请先输出实现计划，列出你会修改的文件、不会修改的文件、测试策略和潜在风险。计划确认后再编码。
```

每个任务结束后，要求 Codex 输出：

```text
1. 修改了哪些文件。
2. 实现了哪些行为。
3. 运行了哪些命令和测试结果。
4. 是否有未完成事项。
5. 是否有风险或需要人工确认的点。
```

---

## 1. 项目启动 Prompt

```text
请阅读以下文件：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md
- docs/DEVELOPMENT_BACKLOG_V0_1.md
- docs/CODEX_WORKFLOW_V0_1.md

先不要写代码。请输出你对本项目 v0.1 的理解，重点说明：
1. 产品目标。
2. 儿童安全底线。
3. 后端核心架构。
4. Android 第一版范围。
5. 为什么第一版先用 MockModelProvider。
6. Milestone 1 应该创建哪些文件。
7. 你会如何验证 Milestone 1。

然后等待我确认。
```

---

## 2. C0：仓库初始化

```text
Goal:
初始化 child-ai-agent 仓库结构，为后续 Codex 开发建立长期规则和基础目录。

Context:
请阅读 AGENTS.md 模板和 docs/ 下所有 v0.1 文档。

Implementation details:
创建或确认以下结构：
- README.md
- AGENTS.md
- docs/
- backend/
- android/
- scripts/
- .github/pull_request_template.md
- .env.example
- .gitignore

Constraints:
- 不写业务代码。
- 不引入真实大模型 API key。
- 不创建复杂 CI。
- README 只写项目定位、文档入口、后续启动方式。

Done when:
- 仓库有清晰目录结构。
- README 指向 docs/SYSTEM_DESIGN_V0_1.md。
- AGENTS.md 存在且包含儿童安全和工程规则。
- .env.example 不包含真实 secret。

Verification:
- 输出文件树。
- 确认没有真实密钥。
```

---

## 3. M1：后端 FastAPI 骨架

```text
Goal:
创建 backend FastAPI 项目骨架，实现 /api/v1/health 和 /api/v1/conversation/message 的 mock 流程。

Context:
请阅读：
- AGENTS.md
- docs/SYSTEM_DESIGN_V0_1.md 的后端架构部分
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 1
- docs/CODEX_WORKFLOW_V0_1.md 的阶段 1

Implementation details:
在 backend/ 下创建：
- pyproject.toml
- README.md
- app/main.py
- app/api/v1/health.py
- app/api/v1/conversation.py
- app/core/config.py
- app/core/logging.py
- app/domain/schemas/conversation.py
- app/services/conversation_service.py
- app/tests/test_health.py
- app/tests/test_conversation_mock.py

Conversation mock 要求：
- 接收 child_id、session_id、input.text、client_context.device_time、client_context.timezone。
- 返回 reply.text、ui_actions、session_state。
- 暂时固定返回温和的小狐狸回复。

Constraints:
- 不接真实大模型。
- 不接数据库。
- 不实现完整场景编排。
- 不把业务逻辑堆在 route function 中。
- 使用 Pydantic schema。

Done when:
- GET /api/v1/health 返回 {"status":"ok"}。
- POST /api/v1/conversation/message 返回 mock reply。
- pytest 通过。
- backend README 能说明如何启动和测试。

Verification:
运行：
- pytest
- uvicorn app.main:app --reload 后手动 curl health 和 conversation

请先输出实现计划，确认后再写代码。
```

---

## 4. M2：时间上下文和父亲策略

```text
Goal:
实现 TimeContextService 和 ParentPolicyService，使每次 conversation/message 都能注入 time_context 和 parent_policy。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md 中时间感知、父亲策略、动态场景编排部分。
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 2。

Implementation details:
新增或修改：
- app/domain/enums.py 或 app/domain/time.py
- app/services/time_context_service.py
- app/services/parent_policy_service.py
- app/api/v1/parent_policy.py
- app/domain/schemas/parent_policy.py
- app/tests/test_time_context_service.py
- app/tests/test_parent_policy_api.py
- app/tests/test_conversation_with_context.py

TimePeriod 初始值：
- morning_before_school
- after_school
- homework_time
- bedtime
- other

默认作息：
- 06:30-07:50 morning_before_school
- 15:30-18:00 after_school
- 18:00-20:20 homework_time
- 20:20-21:30 bedtime

ParentPolicy 初始字段：
- goals: list[str]
- communication_preferences: dict
- safety_rules: dict
- schedule: dict

Constraints:
- 先使用内存存储或简单 JSON，不上复杂数据库迁移。
- 时间段必须可配置，不要散落硬编码。
- conversation/message 的 dev debug 中返回 time_context。

Done when:
- 16:30 -> after_school。
- 20:45 -> bedtime。
- /api/v1/parent/policy GET/POST 可用。
- conversation/message 能读取父亲目标。
- pytest 通过。

请先输出实现计划，确认后再编码。
```

---

## 5. M3：Model Registry 和 MockModelProvider

```text
Goal:
实现可配置模型抽象层。业务代码只能通过 ModelRegistry 调用模型，不能直接绑定具体供应商。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md 中模型可配置、Model Provider Adapter、能力矩阵部分。
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 3。

Implementation details:
新增：
- app/domain/model_types.py
- app/providers/model/base.py
- app/providers/model/mock_provider.py
- app/providers/model/openai_compatible_provider.py
- app/services/model_registry.py
- app/tests/test_model_registry.py
- app/tests/test_mock_model_provider.py

定义 ModelTaskType：
- child_chat
- intent_classification
- safety_classification
- memory_extraction
- parent_report
- vision
- ocr

定义 ModelRequest / ModelResponse：
- task_type
- messages
- input_text
- context
- response_text
- structured_output
- provider_name
- model_name
- metadata

MockModelProvider 要能根据 task_type 返回固定结果。

OpenAICompatibleProvider 只做接口骨架：
- 从环境变量读取 base_url/api_key/model_name。
- 默认 disabled。
- 不在测试中调用真实网络。

Constraints:
- 不引入真实 API key。
- 不在业务服务中直接 import OpenAI provider。
- 不改变 conversation API 返回结构。
- 必须支持 fallback provider。

Done when:
- ModelRegistry.select(task_type) 可返回 MockModelProvider。
- 配置中可切换 child_chat_primary。
- provider 异常时可 fallback。
- pytest 通过。

请先输出实现计划，确认后再编码。
```

---

## 6. M4：Prompt Manager

```text
Goal:
实现分层 Prompt 管理，支持全局安全、人设、父亲策略、时间上下文、场景 Prompt 和记忆上下文组合。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md 的 Prompt 体系。
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 4。

Implementation details:
新增：
- app/domain/prompt.py
- app/services/prompt_manager.py
- app/prompts/global_system.md
- app/prompts/persona_fox.md
- app/prompts/scenes/after_school_checkin.md
- app/prompts/scenes/learning_homework_help.md
- app/prompts/scenes/bedtime_reflection.md
- app/prompts/memory_extraction.md
- app/tests/test_prompt_manager.py

PromptManager.compose() 输入：
- scene_id
- time_context
- parent_policy
- child_profile
- retrieved_memories
- session_state

输出：
- composed_prompt 或 messages list
- prompt_versions

Constraints:
- 不要写一个超级 Prompt。
- Prompt 模板要能单独更新。
- 儿童安全规则必须在 global_system 中。
- 学习场景必须包含“不直接给答案，先问题目在问什么”。

Done when:
- 可组合 after_school、learning_help、bedtime 三类 prompt。
- 测试覆盖模板缺失和版本信息。
- pytest 通过。

请先输出实现计划，确认后再编码。
```

---

## 7. M5：SafetyEngine 和 IntentClassifier

```text
Goal:
实现规则优先的安全分类和意图识别，为 SceneOrchestrator 提供稳定输入。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md 的安全系统、意图识别、场景切换部分。
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 5。

Implementation details:
新增：
- app/domain/classification.py
- app/services/safety_engine.py
- app/services/intent_classifier.py
- app/tests/test_safety_engine.py
- app/tests/test_intent_classifier.py

RiskCategory：
- none
- privacy
- bullying
- self_harm
- adult_secret
- stranger
- sexual_content
- violence
- medical
- unknown_risk

RiskLevel：
- none
- low
- medium
- high
- critical

Intent：
- after_school_checkin
- learning_help
- bedtime_reflection
- emotion_support
- social_issue
- interest_chat
- safety_guardian
- unknown

规则要求：
- 包含“题”“不会”“作业” -> learning_help。
- 包含“晚安”“睡觉”且 time_period=bedtime -> bedtime_reflection。
- 包含“我回来了”或 time_period=after_school 且会话刚开始 -> after_school_checkin。
- 包含“陌生人”“不要告诉爸爸妈妈”“保密” -> risk high，intent safety_guardian。

Constraints:
- 高风险分类必须优先于普通意图。
- 不用真实模型做分类。
- 不要过度追问敏感细节。

Done when:
- 所有规则测试通过。
- conversation/message 可以在 debug 中返回 intent 和 risk。
- pytest 通过。

请先输出实现计划，确认后再编码。
```

---

## 8. M6：SceneOrchestrator

```text
Goal:
实现动态场景编排器，基于 time_context、intent、risk、parent_policy 和 session_state 返回合适回复策略与 ui_actions。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md 的动态场景编排器和场景栈。
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 6。
- 当前 SafetyEngine 和 IntentClassifier 实现。

Implementation details:
新增或修改：
- app/domain/scene.py
- app/services/scene_orchestrator.py
- app/services/conversation_service.py
- app/tests/test_scene_orchestrator.py
- app/tests/test_conversation_scenarios.py

SceneId：
- daily.after_school_checkin
- learning.homework_help
- daily.bedtime_reflection
- safety.guardian
- casual.interest_chat

场景行为：
1. after_school_checkin：返回低压力选择题。
2. learning.homework_help：如果没有题目内容，返回 take_photo / speak_problem actions。
3. learning.homework_help：如果已有题目内容，先问“这道题在问什么”。
4. bedtime_reflection：返回三问复盘。
5. safety.guardian：鼓励告诉爸爸妈妈，并标记 requires_parent_attention=true。

Constraints:
- 不接真实模型。
- 不直接给作业答案。
- 不改变 conversation/message 顶层 schema，除非必要且同步测试。
- 场景逻辑不要写进 API handler。

Done when:
- 五类场景都有测试。
- routing_decision 可被记录或返回 debug。
- pytest 通过。

请先输出实现计划，确认后再编码。
```

---

## 9. M7：MemoryService

```text
Goal:
实现 v0.1 结构化记忆系统，支持写入、检索、过期过滤和父亲可见性字段。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md 的记忆系统、RAG、记忆数据结构。
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 7：基础记忆系统。

Implementation details:
新增：
- app/domain/memory.py
- app/repositories/memory_repository.py
- app/services/memory_service.py
- app/services/memory_extractor.py
- app/tests/test_memory_service.py
- app/tests/test_memory_extractor_mock.py

MemoryItem 字段：
- id
- child_id
- memory_type
- content
- tags
- evidence
- confidence
- importance
- sensitivity
- visible_to_parent
- requires_parent_attention
- expires_at
- created_at
- updated_at

MemoryType：
- interest
- learning_pattern
- expression_pattern
- emotion_observation
- event
- safety
- parent_rule

Constraints:
- 不保存真实长篇原始聊天为长期记忆。
- 不贴人格标签。
- v0.1 可使用内存 repository 或 SQLite，优先简单可测。
- 高风险记忆 sensitivity=critical，requires_parent_attention=true。

Done when:
- 可写入和检索记忆。
- 过期记忆不会被 retrieve 返回。
- 高风险记忆有父亲提醒字段。
- pytest 通过。

请先输出实现计划，确认后再编码。
```

---

## 10. M8：ParentReportService

```text
Goal:
实现父亲日报服务，汇总今日会话、记忆、学习观察、表达观察、风险提醒和建议父亲行动。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md 的父亲端和父亲日报。
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 8：父亲日报。
- MemoryService 当前实现。

Implementation details:
新增：
- app/domain/parent_report.py
- app/services/parent_report_service.py
- app/api/v1/parent_report.py
- app/tests/test_parent_report_service.py
- app/tests/test_parent_report_api.py

ParentReport 字段：
- child_id
- date
- summary
- learning_observations
- expression_observations
- emotion_observations
- safety_alerts
- suggested_parent_actions
- created_at

Constraints:
- 父亲日报不要逐字展示孩子所有原话。
- 不输出“胆小”“不合群”等负面人格标签。
- 高风险提醒要清晰。
- v0.1 可以用 mock summary，不接真实模型。

Done when:
- /api/v1/parent/report/today 可用。
- 有普通日报和高风险日报测试。
- pytest 通过。

请先输出实现计划，确认后再编码。
```

---

## 11. M9：Attachment 和 Mock OCR

```text
Goal:
实现拍照题目流程的后端占位能力：上传附件、Mock OCR、将题目内容用于学习引导。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md 的多模态、拍照题目、Modality Manager 部分。
- docs/DEVELOPMENT_BACKLOG_V0_1.md 的 Milestone 9：多模态占位和附件流程。

Implementation details:
新增：
- app/domain/attachment.py
- app/api/v1/attachment.py 或 app/api/v1/conversation_attachment.py
- app/providers/ocr/base.py
- app/providers/ocr/mock_ocr_provider.py
- app/services/attachment_service.py
- app/tests/test_attachment_api.py
- app/tests/test_learning_help_with_attachment.py

行为：
- POST /api/v1/conversation/attachment 接收 child_id、session_id、attachment_type、mock_ocr_text 或 file metadata。
- v0.1 不必真实保存图片。
- 返回 recognized_content。
- conversation/message 接收 attachment_ids 后可进入题目引导。

Constraints:
- 不接真实 OCR。
- 不长期保存真实图片。
- 不直接给题目答案。
- 图片相关日志不得记录真实文件路径之外的敏感数据。

Done when:
- 学习求助 -> 返回 take_photo action。
- 上传 mock homework_photo -> 返回题目文本。
- 再次 conversation/message -> 先问题目在问什么。
- pytest 通过。

请先输出实现计划，确认后再编码。
```

---

## 12. Q1：后端 Scenario Tests 和 CI

```text
Goal:
补齐后端核心场景测试、demo 脚本和 GitHub Actions CI。

Context:
请阅读：
- docs/CODEX_WORKFLOW_V0_1.md 的阶段 7。
- 当前 backend 测试结构。

Implementation details:
新增或修改：
- backend/app/tests/test_scenarios_v0_1.py
- scripts/test_backend.sh
- scripts/dev_backend.sh
- scripts/demo_backend_scenarios.sh
- .github/workflows/backend-ci.yml
- backend/README.md

Scenario tests 覆盖：
1. 放学后打开。
2. 学习求助。
3. 拍照题目。
4. 睡前复盘。
5. 高风险安全。
6. 父亲目标影响回复。
7. 模型 fallback。

Constraints:
- CI 只跑后端 pytest 和 ruff。
- 不要求 Android CI。
- 不引入真实外部网络调用。

Done when:
- 本地 scripts/test_backend.sh 通过。
- GitHub Actions 配置文件存在。
- backend README 更新。

请先输出实现计划，确认后再编码。
```

---

## 13. A1：Android 项目初始化

```text
Goal:
初始化 Android 平板端项目，创建基础 Compose 应用和子端聊天页面静态骨架。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md 的 Android 端设计。
- docs/CODEX_WORKFLOW_V0_1.md 的阶段 8。

Implementation details:
在 android/ 下创建标准 Android 项目：
- Kotlin
- Jetpack Compose
- Material 3

创建：
- MainActivity
- AppNavHost
- ChildChatScreen
- CartoonAgentView
- MessageList
- InputBar
- Android README

静态 UI 要求：
- 顶部显示小狐狸名称。
- 中间显示消息列表。
- 底部输入框和发送按钮。
- 不做复杂动画。

Constraints:
- 不接后端。
- 不接真实相机。
- 不接真实语音。
- 不做账号系统。

Done when:
- Android 项目可以编译。
- ChildChatScreen 可显示静态消息。
- README 说明如何运行。

请先输出实现计划，确认后再编码。
```

---

## 14. A2：Android 接入后端 Conversation API

```text
Goal:
让 Android ChildChatScreen 调用后端 /api/v1/conversation/message，并渲染 reply 和 ui_actions。

Context:
请阅读：
- 后端 OpenAPI 或 conversation schema。
- docs/SYSTEM_DESIGN_V0_1.md 的 API 设计。
- 当前 Android 项目结构。

Implementation details:
新增：
- ConversationApiClient
- ConversationRepository
- ChatViewModel
- UiAction model
- DevSettings for backend base URL

行为：
- 用户输入文字后发送到后端。
- 显示用户消息和 AI 回复。
- 如果后端返回 ui_actions，渲染按钮。
- 默认 child_id=child_demo_001。

Constraints:
- 不实现登录。
- 不把任何模型 API key 放到 Android。
- 网络失败时显示温和错误。
- 不做复杂本地数据库。

Done when:
- 输入“我回来了”显示后端回复。
- 输入“我有一道题不会”显示“拍题目/读题目”按钮。
- Android 可编译。

请先输出实现计划，确认后再编码。
```

---

## 15. A3：Android Mock 拍题流程

```text
Goal:
实现 Android 端“拍题目”按钮的 mock 流程，不接真实相机，先向后端发送 mock OCR 文本。

Context:
请阅读：
- 后端 /api/v1/conversation/attachment 接口。
- 当前 Android ChatViewModel。

Implementation details:
行为：
- 点击“拍题目”按钮。
- 弹出或直接使用 mock 题目文本。
- 调用 attachment API。
- 将 recognized_content 或 attachment_id 继续传给 conversation/message。
- 显示 AI 的题目引导。

Constraints:
- 不接真实 CameraX。
- 不接真实 OCR。
- 不直接显示最终答案。

Done when:
- 学习求助流程可从 Android 端完整跑通。
- Android 可编译。
- README 更新手动测试步骤。

请先输出实现计划，确认后再编码。
```

---

## 16. A4：父亲设置页

```text
Goal:
实现 Android 父亲设置页，可以配置目标、沟通偏好和作息时间，并提交到后端。

Context:
请阅读：
- 后端 /api/v1/parent/policy。
- docs/SYSTEM_DESIGN_V0_1.md 的父亲端设计。

Implementation details:
创建：
- ParentSettingsScreen
- ParentPolicyApiClient
- ParentPolicyViewModel

字段：
- 本周目标
- 沟通偏好：选择题引导、不要强迫表达、学习先问思路
- after_school start/end
- bedtime start/end

Constraints:
- 不做复杂权限系统。
- 入口可以暂时是隐藏按钮或开发菜单。
- 不展示孩子逐字聊天记录。

Done when:
- 能读取当前 policy。
- 能修改并保存 policy。
- 保存后会影响下一次 conversation/message。
- Android 可编译。

请先输出实现计划，确认后再编码。
```

---

## 17. E2E：端到端联调

```text
Goal:
完成后端 + Android 的 v0.1 端到端联调，验证核心家庭内测流程。

Context:
请阅读：
- docs/CODEX_WORKFLOW_V0_1.md 阶段 9。
- backend README。
- android README。

Tasks:
1. 启动后端。
2. 启动 Android 应用。
3. 验证放学后场景。
4. 验证学习求助和 mock 拍题。
5. 验证睡前复盘。
6. 验证高风险安全。
7. 验证父亲设置影响回复。
8. 记录手动 QA 结果。

Constraints:
- 不接真实儿童数据。
- 不接真实模型。
- 如果发现后端 API 与 Android 不一致，优先修正 schema 和文档。

Done when:
- docs/MANUAL_QA_V0_1.md 存在。
- 所有核心场景都有通过/失败记录。
- 失败项转成 issue。

请先输出联调计划，确认后再执行修改。
```

---

## 18. Bug 修复通用 Prompt

```text
Bug:
[描述问题]

Repro:
1. [步骤 1]
2. [步骤 2]
3. [步骤 3]

Expected:
[期望行为]

Actual:
[实际行为]

Context:
请优先查看以下文件：
- [文件 1]
- [文件 2]

Constraints:
- 先复现或写出可失败的测试。
- 最小化修改。
- 不删除现有测试。
- 不重构无关模块。
- 修复后运行相关测试。

Done when:
- 回归测试通过。
- 相关测试通过。
- 最后说明根因、修改文件和验证结果。

请先给排查计划，不要直接大改。
```

---

## 19. Refactor 通用 Prompt

```text
Goal:
对 [模块] 做小范围重构，提升可读性和可测试性，不改变外部行为。

Context:
- [相关文件]
- [相关测试]

Constraints:
- 不改变 API schema。
- 不改变用户可见行为。
- 不引入新依赖。
- 每一步保持测试通过。
- 如果重构超过 800 行 diff，先拆分计划。

Done when:
- 原有测试通过。
- 新增必要测试。
- 代码职责更清晰。
- 最后说明重构前后模块边界变化。

请先输出重构计划和风险点，确认后再编码。
```

---

## 20. Review 通用 Prompt

```text
请审查当前 diff。重点检查：
1. 是否符合 AGENTS.md。
2. 是否符合 docs/SYSTEM_DESIGN_V0_1.md。
3. 是否违反儿童安全原则。
4. 是否可能直接给作业答案。
5. 是否过度保存儿童数据。
6. 是否绕过 ModelRegistry / PromptManager / SafetyEngine / SceneOrchestrator。
7. 是否缺少测试。
8. 是否有 API 兼容性问题。
9. 是否有过度工程化。

输出格式：
- P0：必须立即修复，否则不能合并。
- P1：应该在本 PR 修复。
- P2：可以后续处理。
- Positive notes：做得好的地方。
- Suggested minimal patch：最小修复建议。
```

---

## 21. 文档更新 Prompt

```text
Goal:
根据当前实现更新文档，保证 docs 与代码一致。

Context:
请阅读：
- docs/SYSTEM_DESIGN_V0_1.md
- docs/DEVELOPMENT_BACKLOG_V0_1.md
- docs/CODEX_WORKFLOW_V0_1.md
- 当前实现相关文件

Constraints:
- 不夸大未实现功能。
- 明确区分已实现、mock、待实现。
- 不写无法验证的承诺。
- 保持 Markdown 结构清晰。

Done when:
- 文档准确反映当前代码。
- README 本地运行命令可用。
- 变更摘要清楚。

请先列出需要更新的文档位置，确认后再修改。
```
