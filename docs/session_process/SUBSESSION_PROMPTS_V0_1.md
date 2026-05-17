# 子会话启动提示词 v0.1

用途：当需要你在 Codex 中新建子会话时，复制对应提示词作为第一条消息。

所有提示词都默认要求：

```text
先不要写代码。先阅读指定文档和相关文件，输出计划，等待确认后再实现。
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

