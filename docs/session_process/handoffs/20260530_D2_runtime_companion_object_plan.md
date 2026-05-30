# D2 计划：对话运行时与提示词接入

状态：计划评审中

更新时间：2026-05-30

---

## 1. 已阅读的文档

```text
README.md
AGENTS.md
docs/提示词与文案归属规则_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
docs/session_process/轻量交接协议_2026_05_30_V0_1.md
docs/session_process/handoffs/20260530_D1_companion_object_handoff.md
docs/小白狐关系与轻连续体验总设计_2026_05_30_V0_1.md
docs/小屋小客人共创延续机制设计_2026_05_30_V0_1.md
docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md
docs/小白狐首次与每日打开体验设计_2026_05_30_V0_1.md
docs/四个核心场景话术与状态库_2026_05_30_V0_1.md
docs/连续三天真实家庭测试脚本_2026_05_30_V0_1.md
docs/小白狐关系与轻连续体验开发任务清单_2026_05_30_V0_1.md
```

还阅读了以下代码文件：

```text
backend/app/services/child_agent_runtime.py        (~1050 行，主对话运行时)
backend/app/services/conversation_service.py       (~31KB，对话总控)
backend/app/services/opening_service.py            (~31KB，opening 生成)
backend/app/services/opening_policy.py             (~16KB，opening 模式决策)
backend/app/services/prompt_manager.py             (~728 行，prompt 组装)
backend/app/services/scene_orchestrator.py         (~500 行，场景路由)
backend/app/services/light_co_creation_service.py  (轻共创状态管理)
backend/app/services/companion_object_service.py   (D1 陪伴物服务)
backend/app/domain/companion_object.py             (D1 领域模型)
backend/app/domain/schemas/conversation.py         (对话 API schema)
backend/app/domain/attachment.py                   (附件响应 schema)
backend/app/api/v1/conversation_opening.py         (opening API 路由)
backend/app/tests/test_conversation_opening_api.py (opening 测试)
```

---

## 2. D2 任务范围理解

D2 的目标是：让小白狐在合适时机生成"小屋小客人"相关 opening、召回、共创和放下行为。

D2 在对话运行时层面接入 D1 已实现的 `CompanionObjectService`，使小屋小客人机制在以下时机生效：

```text
1. 打开 App（opening）时：检查是否有活跃小客人可召回
2. 对话过程中：检测共创意图、创建/更新/跳过小客人
3. 图片上传后：在成功场景中提供一个共创入口
4. 睡前：统一不主动召回小客人
5. 学习/安全/隐私场景：不生成小客人
```

D2 的本质工作是在现有对话运行时的关键节点插入 `CompanionObjectService` 调用，并通过 prompt 注入将小客人上下文传递给模型。

---

## 3. 会修改的文件

| 文件 | 修改内容 |
|---|---|
| `backend/app/services/opening_service.py` | 注入 `CompanionObjectService`；opening 阶段检查小客人召回 |
| `backend/app/services/opening_policy.py` | 新增 `COMPANION_RECALL` opening 模式 |
| `backend/app/services/conversation_service.py` | 注入 `CompanionObjectService`；对话中检测共创意图并创建/更新/跳过小客人 |
| `backend/app/services/prompt_manager.py` | `render_companion_context()` 方法，将小客人上下文注入 prompt |
| `backend/app/prompts/scenes/conversation_open_v0_1.txt` | 追加小客人召回指令段（只复制主控 master-copy 文案） |
| `backend/app/domain/schemas/conversation.py` | 扩展 `SessionState` 增加 `companion_object` 字段；新增 `CompanionObjectMeta` schema |
| `backend/app/tests/test_companion_object_runtime.py` | 新增 D2 运行时集成测试 |

---

## 4. 明确不会修改的文件

```text
backend/app/services/companion_object_service.py  — D1 已完成，不改
backend/app/domain/companion_object.py             — D1 已完成，不改
backend/app/repositories/companion_object_*        — D1 已完成，不改
backend/app/db/models.py                           — D1 已完成，不改
backend/alembic/versions/*                         — D1 已完成，不改
backend/app/services/child_agent_runtime.py        — 不改主运行时流程
backend/app/services/scene_orchestrator.py         — 不改场景路由优先级
backend/app/services/safety_engine.py              — 不改安全引擎
backend/app/api/v1/conversation_opening.py         — 不改 API 路由
backend/app/api/v1/conversation.py                 — 不改 API 路由
backend/app/api/v1/conversation_attachment.py      — 不改 API 路由
backend/app/services/light_co_creation_service.py  — 不改既有轻共创
android/                                           — D2 不涉及 Android
```

---

## 5. 是否涉及儿童端文案、prompt、家长端文案

**涉及 prompt 注入**：需要在 opening scene prompt 中追加小客人召回指令段。此段内容只复制主控 master-copy 中的精确文案，不自行编写。

**涉及儿童端可见文案**：D2 不新增任何儿童端文案。所有孩子可见的气泡文本（召回话术、放下话术、共创入口等）均通过 prompt 指令让模型从主控 master-copy 中选取，或由现有确定性 fallback 覆盖。

**不涉及家长端文案**：D2 不修改家长日报或家长端展示。

---

## 6. 文案来源说明

D2 使用的儿童端可见文案只来自以下主控 master-copy 文档：

```text
docs/小白狐首次与每日打开体验设计_2026_05_30_V0_1.md  — opening 相关话术
docs/四个核心场景话术与状态库_2026_05_30_V0_1.md       — 场景话术、按钮文案
docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md     — 召回/放下话术
```

prompt 中注入的小客人召回指令将直接引用上述文档中的精确短句，例如：

```text
召回话术："{name}今天在{location}呢" + "要不要给它加一个朋友？"
放下话术："好呀，我们聊新的"
按钮："加一个朋友" / "先聊别的"
```

不得自行替换为意思相近的句子。

---

## 7. 现有代码复用点

### 7.1 Opening 阶段

- `OpeningService.create_opening()` 是 opening 入口，已有完整的模式决策、fallback 文本、模型调用和清理流程
- `OpeningPolicyBuilder.build()` 已有多种模式（DEFAULT_LIGHT、INTEREST_CALLBACK、BEDTIME_CLOSURE 等），可在此基础上新增 `COMPANION_RECALL` 模式
- `_build_opening_text()` 已有按模式选择 fallback 模板的逻辑
- `_opening_prompt()` 已有构建模型 system prompt 的框架
- `FORBIDDEN_OPENING_PHRASES` 已有禁止话术列表

### 7.2 对话阶段

- `ConversationService.handle_message()` 是对话主流程，已有安全分类、意图分类、场景路由、记忆检索、运行时调用的完整链路
- `LightCoCreationService` 已有共创状态管理（session 级别的 INVITED/RESPONDED/COMPLETED 状态机），可参考其模式
- `SceneOrchestrator.route()` 已有场景优先级链，D2 不修改此链，但会利用其输出的 `scene_id` 判断是否为学习/安全/隐私场景

### 7.3 Prompt 组装

- `PromptManager.compose()` 已有 11 层 prompt 组装框架
- `render_memory_context()` 已有记忆上下文注入模式，可参考其模式新增 `render_companion_context()`

### 7.4 图片处理

- `_image_context_repair_reply()` 已有按 `recognized_type` 分支的确定性回复替换逻辑
- `AttachmentCreateResponse` 已有 `ui_actions` 字段，可用于传递共创按钮

---

## 8. CompanionObjectService 接入建议

### 8.1 依赖注入

`OpeningService` 和 `ConversationService` 的 `__init__` 新增可选参数 `companion_object_service`，通过 `get_companion_object_service()` 获取实例。

### 8.2 Opening 阶段接入

在 `OpeningService.create_opening()` 中，在 `OpeningPolicyBuilder.build()` 之后、`_build_opening_text()` 之前，插入小客人召回检查：

```python
# 伪代码
companion_svc = self._companion_object_service
if companion_svc and not opening_policy.is_bedtime:
    companion = companion_svc.can_recall(child_id, session_id, is_bedtime=False)
    if companion:
        opening_policy.mode = OpeningMode.COMPANION_RECALL
        opening_policy.companion_object = companion
```

### 8.3 对话阶段接入

在 `ConversationService.handle_message()` 中，在场景路由之后、运行时调用之前，插入小客人状态检查：

```python
# 伪代码
companion = None
if scene_id not in (SAFETY, PRIVACY, LEARNING, BEDTIME):
    companion = companion_svc.can_recall(child_id, session_id, is_bedtime=False)
    # 将 companion 信息注入 memory_context 或 turn_guidance
```

在运行时返回后，检测回复中的共创意图：

```python
# 如果孩子说了类似命名的内容（由模型输出 metadata 标记）
if model_output indicates naming and companion is None:
    companion_svc.create(CompanionObjectCreateRequest(...))
elif model_output indicates skip:
    companion_svc.mark_skipped(companion.id, session_id)
elif model_output indicates continue and companion:
    companion_svc.update(companion.id, ...)
```

### 8.4 图片上传后接入

在 `AttachmentCreateResponse` 构建时，如果图片成功识别且 `recognized_type` 为安全类型（child_drawing、toy、object、handmade），在 `ui_actions` 中追加一个共创按钮（"起个名字"或"编个小故事"）。

---

## 9. 场景识别建议

| 场景 | 识别方式 | 已有代码支撑 |
|---|---|---|
| 首次打开 | `OpeningPolicyBuilder` 中检查 child 是否有任何 companion_object 历史记录（通过 `get_active_by_child()` 返回 None 且无历史） | 需新增 `has_any_history()` 方法 |
| 每日打开 | `OpeningPolicyBuilder` 中 `can_recall()` 返回有效 `CompanionObject` | D1 已有 `can_recall()` |
| 睡前打开 | `time_period == BEDTIME`（已有判断） | `OpeningPolicyBuilder` 已判断 bedtime |
| 图片成功 | `AttachmentService` 返回 `recognized_type` 为安全类型 | `_image_context_repair_reply()` 已按类型分支 |
| 图片失败 | `AttachmentService` 返回失败或 `recognized_type` 为 `unclear`/`low_confidence` | 已有处理 |
| 孩子继续 | 模型回复中检测到共创继续信号（由 prompt 指令让模型输出 metadata） | 需新增 metadata 解析 |
| 孩子跳过 | 模型回复中检测到放下信号，或检测到短答/换题 | 需新增意图检测 |
| 学习场景 | `scene_id == learning.homework_help` | `SceneOrchestrator` 已判断 |
| 高风险/隐私场景 | `scene_id in (safety.guardian, safety.gentle_checkin, privacy.boundary)` | `SceneOrchestrator` 已判断 |

---

## 10. 返回给 Android 的 metadata / action / reply 字段

### 10.1 Opening 响应扩展

在 `SessionState` 中新增可选字段：

```python
class CompanionObjectMeta(BaseModel):
    """小客人元数据，供 Android 渲染轻视觉点。"""
    name: str                              # 小客人名字
    light_location: str                    # 轻位置：窗边/地毯边/小白狐旁边/窗外
    object_type: str                       # 类型：star/cloud/drawing_character 等
    status: str                            # active/paused
    is_recall: bool                        # 本次是否为召回

class SessionState(BaseModel):
    base_scene: str
    active_scene: str
    needs_input: str | None = None
    requires_parent_attention: bool | None = None
    companion_object: CompanionObjectMeta | None = None  # 新增
```

### 10.2 召回时的 ui_actions

```python
ui_actions=[
    UiAction(
        type="show_quick_actions",
        actions=[
            QuickAction(id="companion_continue", label="加一个朋友"),
            QuickAction(id="companion_skip", label="先聊别的"),
        ]
    )
]
```

### 10.3 图片成功后的 ui_actions

```python
# 只出现一个共创入口
ui_actions=[
    UiAction(
        type="show_quick_actions",
        actions=[
            QuickAction(id="companion_name", label="起个名字"),
        ]
    )
]
```

### 10.4 对话响应扩展

`ConversationMessageResponse` 的 `SessionState` 同样携带 `companion_object` 字段，使 Android 在整个会话期间都能获取小客人状态。

---

## 11. 测试策略

### 11.1 新增测试文件

`backend/app/tests/test_companion_object_runtime.py`

### 11.2 必须覆盖的测试用例

```text
1. test_opening_first_time_no_companion        — 首次打开无小客人，低压在场
2. test_opening_with_active_companion_recall    — 有活跃小客人时 opening 召回
3. test_opening_bedtime_no_recall               — 睡前 opening 不召回小客人
4. test_opening_paused_companion_no_recall      — 暂放小客人不主动召回
5. test_conversation_skip_marks_skipped         — 孩子跳过时调用 mark_skipped
6. test_conversation_continue_updates_companion — 孩子继续时更新小客人
7. test_learning_scene_no_companion_creation    — 学习场景不生成小客人
8. test_safety_scene_no_companion               — 高风险场景不生成/召回小客人
9. test_privacy_scene_no_companion              — 隐私场景不生成/召回小客人
10. test_image_success_shows_co_creation_entry  — 图片成功后出现共创入口
11. test_image_failure_no_co_creation_entry     — 图片失败后不出现共创入口
12. test_companion_meta_in_session_state        — SessionState 包含小客人元数据
13. test_recall_only_once_per_session           — 同会话只召回一次
14. test_forbidden_phrases_not_in_output        — 禁止话术不出现
```

### 11.3 既有测试复核

运行完整回归：

```bash
bash scripts/test_backend.sh -v
```

确认 D2 改动不引入新失败。

---

## 12. 可能风险

### 12.1 模型不遵循 prompt 指令

风险：模型可能不按 prompt 中的小客人召回指令输出，导致召回话术不可控。

控制：
- opening 阶段召回使用确定性 fallback 文本（模板化），不依赖模型输出
- 对话阶段的共创意图通过 prompt 指令让模型输出结构化 metadata，失败时忽略

### 12.2 检测共创意图误判

风险：孩子说"不要"可能被误判为跳过，孩子说"好"可能被误判为继续。

控制：
- 跳过检测使用多信号综合：短答 + 换题 + 明确拒绝
- 继续检测需要更明确的信号（如包含名字或类型关键词）
- 误判的代价低：跳过只是不召回，继续只是更新 safe_summary

### 12.3 Opening 时间延迟

风险：新增 `can_recall()` 数据库查询可能增加 opening 延迟。

控制：
- `can_recall()` 是轻量查询（单表按 child_id 查）
- 可在 `OpeningService` 中缓存结果（同一 session 只查一次）

### 12.4 Session state 膨胀

风险：`CompanionObjectMeta` 增加响应体积。

控制：
- 字段极简（name、location、type、status、is_recall）
- 只有存在小客人时才填充

---

## 13. 主控文档、D1 接口与现有代码冲突分析

### 13.1 无冲突

D1 接口设计与现有对话运行时架构兼容：

- `CompanionObjectService` 是独立服务层，不侵入现有运行时
- `can_recall()` 返回 `CompanionObject | None`，与现有"可选注入"模式一致
- `mark_skipped()` / `update()` 是独立操作，不影响现有对话流

### 13.2 需注意的边界

- `LightCoCreationService` 已有 session 级别的共创状态管理，D2 的小客人共创应与之协调，避免双重触发。建议：D2 只负责小客人数据层（create/update/skip），prompt 中的共创邀请仍由 `LightCoCreationService` 管理状态
- `OpeningPolicyBuilder.build()` 的模式决策有优先级链，新增 `COMPANION_RECALL` 需要确定插入位置。建议：在 `INTEREST_CALLBACK` 之后、`DEFAULT_LIGHT` 之前

### 13.3 既有失败测试分析

**测试**：`test_conversation_opening_api.py::test_bedtime_opening_with_interest_seed_is_low_stimulation`

**失败原因**：测试期望睡前 opening 包含"跑步比赛"和"明天白天再慢慢说"，但实际返回通用睡前模板"小白狐在这里。现在有点晚，我们可以慢慢说一小会儿，也可以明天再说。"

**根因**：`opening_service.py` 第 440-446 行，`BEDTIME_DEFER_INTEREST` 模式下先调用 `_bedtime_memory_opening()`，该方法返回了通用文本，覆盖了后续的 topic-specific 逻辑（第 449-450 行）。

**与 D2 的关系**：
1. 此失败不是 D1 引入，是 opening_service 的既有逻辑问题
2. 主控已确认：D2 必须一并修复此测试，不得借机重写 opening 系统
3. 修复方向：调整 `_bedtime_memory_opening()` 的返回逻辑，使 `BEDTIME_DEFER_INTEREST` 模式下 topic 优先于通用记忆 opening

---

## 14. 主控确认结论（2026-05-30）

### Q1：首次打开小星星起名

**确认**：D2 实现后端 opening 决策和 metadata，不做 Android UI。孩子未命名前不能创建小客人。

### Q2：共创意图检测

**确认**：MVP 采用"显式 action + 轻量规则"，不新增 prompt 结构化标记，不重写全局 prompt。

实现方式：Android 端通过 `ui_actions` 按钮（如"起个名字"）发送显式 action；后端通过 `ConversationInput` 中的 action 字段或轻量关键词规则识别共创意图。

### Q3：图片成功后共创入口

**确认**：不放在 AttachmentService 做产品决策。AttachmentService 只提供图片成功/失败事实；conversation runtime / image context 编排层负责只输出一个共创入口；D3 只负责渲染。

### Q4：SessionState companion_object 字段

**确认**：需要，但极简。只给 id、name、object_type、light_location、state、action。不要给 safe_summary、完整故事、召回次数、跳过次数或历史列表。

### Q5：小客人召回文案

**确认**：已有 master-copy，只能引用以下文档中的精确文本：
- `docs/小白狐首次与每日打开体验设计_2026_05_30_V0_1.md`
- `docs/四个核心场景话术与状态库_2026_05_30_V0_1.md`
- `docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md`

如果需要模板，只能做 `{name}` 和 `{light_location}` 变量替换。

### Q6：既有 bedtime opening 测试失败

**确认**：必须纳入 D2。复现并窄修 bedtime opening 优先级/低刺激规则，完整回归不能继续保留此失败。不得借机重写 opening 系统，不得新增儿童端文案。

---

## 15. 实现步骤概览（修正版）

```text
步骤 0：修复 bedtime opening 既有失败（窄修 _bedtime_memory_opening 优先级）
步骤 1：在 opening_policy.py 新增 COMPANION_RECALL 模式
步骤 2：在 opening_service.py 注入 CompanionObjectService，opening 阶段检查召回
步骤 3：首次打开小星星种子：opening 决策 + metadata，不创建小客人
步骤 4：在 schemas/conversation.py 扩展 SessionState（极简 companion_object）
步骤 5：在 conversation_service.py 注入 CompanionObjectService
步骤 6：图片成功后由 conversation runtime 输出一个共创入口
步骤 7：对话中通过显式 action + 轻量规则检测共创意图
步骤 8：编写集成测试
步骤 9：运行完整回归，确认 0 失败
```

每步完成后运行对应测试，不一次性写完再测。
