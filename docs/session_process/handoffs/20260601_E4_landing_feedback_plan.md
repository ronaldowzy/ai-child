# E4 计划：起名后"落到小屋里"的反馈强化

状态：待主控确认

更新时间：2026-06-01

---

## 1. 已阅读文档列表

```text
README.md
AGENTS.md
docs/提示词与文案归属规则_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
docs/session_process/轻量交接协议_2026_05_30_V0_1.md
docs/给小白狐看看2_0与小屋可见共创增强设计_2026_06_01_V0_1.md
docs/session_process/handoffs/20260601_E1_visual_kind_mapping_handoff.md
docs/session_process/handoffs/20260601_E2_android_visible_object_shadow_handoff.md
docs/session_process/handoffs/20260601_E3_image_detail_cocreation_handoff.md
docs/四个核心场景话术与状态库_2026_05_30_V0_1.md
```

---

## 2. 当前起名成功后的后端 response 现状

### 2.1 起名流程回顾

```text
1. 孩子拍图成功 → modality_manager 返回确定性模板："我看到{细节}啦\n像{想象}\n要不要给它起个名字？"
2. quick_actions 返回 [companion_name: 起个名字]
3. 孩子点击"起个名字" → conversation_service._check_pending_companion_seed_creation()
   → begin_seed_naming() 设置 pending，不创建 companion_object
   → 返回 None（不改变回复）
4. 孩子输入名字（如"小棉花"）→ _check_pending_companion_seed_creation()
   → 检测到 pending + 提取到名字 → companion_object_service.create()
   → 返回 {"action": "co_create", "companion": companion}
```

### 2.2 当前问题

起名成功后，回复文本来自 `runtime_result.reply_text`，是**模型自由生成**的，不是确定性模板。

这意味着：
```text
1. 模型可能生成不符合主控要求的话术（如"太棒了！小棉花已经加入你的小屋了！"）
2. 模型可能不包含"落到小屋"的感知
3. 模型可能生成过长或过短的回复
4. 不同次起名的回复不一致
```

### 2.3 companion_meta 构建

起名成功后，`_response_from_route_decision()` 会构建 companion_meta：

```python
companion_meta = CompanionObjectMeta(
    id=str(companion.id),
    name=companion.name,
    object_type=companion.object_type,
    light_location=companion.light_location,
    state=companion.status,  # "active"
    action="co_create",      # 因为 action 在 ("recall", "co_create") 中
    visual_kind=resolve_visual_kind(companion.object_type),
)
```

这个 companion_meta 会通过 `session_state.companion_object` 传给 Android。

---

## 3. 当前 active/co_create metadata 是否足够驱动 Android 入场动画

### 3.1 Android 端判断逻辑

```kotlin
// XiaobaohuCompanionStage.kt:424-428
internal fun CompanionObjectMeta.shouldShowVisual(): Boolean {
    if (state == "paused") return false
    if (state == "seed" && action == "name_seed") return true
    if (state == "active" && action in setOf("recall", "co_create")) return true
    return false
}
```

起名成功后：`state="active"`, `action="co_create"` → `shouldShowVisual()` 返回 `true`。

### 3.2 入场动画触发条件

```kotlin
// XiaobaohuCompanionStage.kt:613-624
var entranceDone by remember { mutableStateOf(false) }
val entranceProgress = remember { Animatable(0f) }
LaunchedEffect(Unit) {
    if (!entranceDone) {
        entranceProgress.animateTo(
            targetValue = 1f,
            animationSpec = tween(durationMillis = 1200, easing = EaseOut),
        )
        entranceDone = true
    }
}
```

关键点：
```text
1. LaunchedEffect(Unit) 在 Composable 进入组合时执行
2. 如果 companionObject 从 null 变为非 null，Composable 会重组
3. 重组时 entranceDone 会被重置为 false（因为是新的 remember）
4. 入场动画会重新播放
```

### 3.3 结论

**当前 metadata 足够驱动 Android 入场动画。**

起名成功后：
- companionObject 从 null 变为 {state: "active", action: "co_create", visual_kind: "xxx"}
- Android 端 shouldShowVisual() 返回 true
- CompanionLightPoint Composable 进入组合
- 入场动画 1.2s fade in + scale 播放

---

## 4. 是否需要新增 action

### 4.1 分析

```text
当前 action 值：recall / co_create / none / name_seed

如果新增 landed / co_create_landed：
- 需要修改后端 companion_meta 构建
- 需要修改 Android shouldShowVisual()
- 需要修改 Android 入场动画判断
- 增加复杂度
```

### 4.2 结论

**不需要新增 action。**

理由：
1. 复用 `state=active/action=co_create` 已足够
2. Android 端入场动画已能在 co_create 时触发
3. 主控倾向：不要新增复杂状态
4. 区分"首次落到小屋"和普通 active 显示的需求，可以通过 companionObject 从 null 变为非 null 来判断

---

## 5. 是否需要新增一次性 UI event

### 5.1 分析

如果需要 Android 在起名成功时播放特殊动画（如从对话区飞到小屋区），需要新增 UI event。

但当前需求是：
```text
1. 小物件影子从很淡到可见（已有 fade in 1.2s）
2. 停在窗边/地毯边/小白狐旁边（已有位置逻辑）
3. 不出现奖励爆光（已遵守）
```

### 5.2 结论

**不需要新增一次性 UI event。**

理由：
1. 现有入场动画（fade in 1.2s + scale 0.8→1.0）已满足"从很淡到可见"
2. companionObject 从 null 变为非 null 时，入场动画会自动播放
3. 不需要特殊飞行动画或其他复杂效果

---

## 6. 起名成功后的精确话术如何处理

### 6.1 当前问题

起名成功后，回复文本来自模型自由生成，不符合主控要求。

### 6.2 解决方案

在 `_response_from_route_decision()` 中，当 companion_action 为 co_create 且是新建时，**替换回复文本为确定性模板**。

### 6.3 话术模板来源

来自 `docs/四个核心场景话术与状态库_2026_05_30_V0_1.md` 第 3.6 节：

```text
小棉花，软软的名字
那它今天就在窗边待一会儿

小尾巴，听起来会跑来跑去
那它今天就在地毯边待一会儿
```

以及主控确认的话术方向：

```text
模板 A：
{name}，软软的名字
它轻轻落到{light_location}啦

模板 B：
{name}，听起来会跑来跑去
它先在{light_location}待一会儿
```

### 6.4 实现方式

在 `conversation_service.py` 的 `_response_from_route_decision()` 中：

```python
# 如果是新建 companion（co_create），替换回复为确定性模板
if (companion_action is not None
    and companion_action.get("action") == "co_create"
    and companion is not None):
    # 使用确定性模板，不依赖模型生成
    name = companion.name
    location = companion.light_location or "窗边"
    reply_text = f"{name}，软软的名字\n它轻轻落到{location}啦"
```

### 6.5 quick_actions 处理

起名成功后，不返回任何 quick_actions（避免任务感）。

当前 quick_actions 来自 `quick_action_service.actions_for()`，需要在 companion_action 为 co_create 时返回空列表。

---

## 7. Android 是否需要区分"首次落到小屋"和普通 active 显示

### 7.1 场景分析

```text
首次落到小屋：
- companionObject 从 null 变为 {state: "active", action: "co_create"}
- 入场动画播放（fade in 1.2s）

普通 active 显示（如 recall）：
- companionObject 从 null 变为 {state: "active", action: "recall"}
- 入场动画播放（fade in 1.2s）
```

### 7.2 结论

**不需要区分。**

理由：
1. 两种情况都播放相同的入场动画，体验一致
2. 区分的话需要新增字段或 action，增加复杂度
3. 主控不要求区分的视觉效果

---

## 8. 如何避免奖励感、任务感、宠物感

### 8.1 话术层面

```text
1. 使用"轻轻落到"而不是"加入/解锁/获得"
2. 使用"待一会儿"而不是"等待你/会等你"
3. 不使用"保存成功/任务完成/恭喜"
4. 不催促"明天一定要来看它"
```

### 8.2 视觉层面

```text
1. 入场动画 1.2s，不抢眼
2. 半透明、低饱和、绘本感
3. 不出现奖励爆光/金币特效
4. 不出现收集提示/图鉴格子
```

### 8.3 交互层面

```text
1. 起名成功后不返回 quick_actions（避免"下一步任务"感）
2. 孩子可以继续聊别的，也可以放下
3. 不提示"还有更多小客人等你收集"
```

---

## 9. 会修改哪些文件

### 后端

```text
backend/app/services/conversation_service.py
  - _response_from_route_decision()：当 companion_action 为 co_create 时，替换回复文本为确定性模板
  - quick_actions：当 companion_action 为 co_create 时，返回空列表
```

### Android

```text
不修改
```

---

## 10. 不会修改哪些文件

```text
backend/app/providers/
backend/app/core/
backend/app/api/
backend/app/db/
backend/app/repositories/
backend/app/services/safety_engine.py
backend/app/services/scene_orchestrator.py
backend/app/services/parent_report_service.py
backend/app/services/parent_report_language_v4.py
backend/app/services/memory_service.py
backend/app/services/prompt_manager.py
backend/app/services/modality_manager.py
backend/app/services/companion_object_service.py
backend/app/services/opening_service.py
backend/app/domain/
backend/app/tests/（新增测试，不修改现有）
android/
```

---

## 11. 测试策略

### 11.1 后端测试

```text
1. 新增测试：起名成功后回复文本是否为确定性模板
2. 新增测试：起名成功后 quick_actions 是否为空
3. 新增测试：companion_meta 是否正确构建（state=active, action=co_create, visual_kind 正确）
4. 运行现有测试确保不破坏：bash scripts/test_backend.sh
```

### 11.2 测试用例

```python
def test_naming_success_returns_deterministic_template():
    """起名成功后，回复文本应为确定性模板，不是模型生成。"""
    # 模拟：拍图成功 → 点击"起个名字" → 输入"小棉花"
    # 断言：reply_text == "小棉花，软软的名字\n它轻轻落到窗边啦"

def test_naming_success_no_quick_actions():
    """起名成功后，不应返回 quick_actions。"""
    # 断言：ui_actions 为空列表

def test_naming_success_companion_meta():
    """起名成功后，companion_meta 应正确构建。"""
    # 断言：state="active", action="co_create", visual_kind 正确
```

### 11.3 Android 测试

```text
不新增测试（不改 Android 代码）
现有测试：bash scripts/android_gradle.sh test
```

---

## 12. 风险点

### 12.1 确定性模板可能不够自然

```text
风险：固定模板可能在某些场景下显得生硬
缓解：使用两个模板轮换，或根据 light_location 微调
```

### 12.2 模型回复被完全丢弃

```text
风险：模型可能生成更有创意的回复
缓解：E4 目标是"明确感到落到小屋"，确定性模板更可靠
```

### 12.3 quick_actions 为空可能导致孩子不知道下一步

```text
风险：起名成功后没有任何按钮，孩子可能困惑
缓解：话术本身已足够完整，孩子可以自然继续聊或放下
```

### 12.4 light_location 可能为空

```text
风险：companion.light_location 为空时，模板会出现"它轻轻落到 啦"
缓解：使用默认值"窗边"
```

---

## 13. 需要主控确认的问题

### Q1：话术模板选择

主控确认的话术方向有两个版本：

```text
模板 A：
{name}，软软的名字
它轻轻落到{light_location}啦

模板 B：
{name}，听起来会跑来跑去
它先在{light_location}待一会儿
```

**问题：使用哪个模板？还是两个轮换？**

### Q2：quick_actions 是否真的为空

起名成功后，是否完全不返回任何按钮？

```text
选项 A：完全不返回按钮（孩子自然继续聊或放下）
选项 B：返回"先聊别的"按钮（给孩子一个明确出口）
```

### Q3：话术是否需要根据 visual_kind 微调

不同 visual_kind 是否需要不同的话术？

```text
例如：
- 小星星：它轻轻落到窗边啦
- 小纸船：它轻轻漂到窗边啦
- 小恐龙：它轻轻走到地毯边啦
```

还是统一使用"轻轻落到"？

### Q4：回复是否需要包含小白狐状态气泡

起名成功后，小白狐的状态气泡应该显示什么？

```text
选项 A：不显示状态气泡（只有对话区的回复）
选项 B：显示"我来说啦"（因为小白狐在说话）
选项 C：显示"我们接一句"（共创状态）
```

---

## 附录：代码变更预览

### conversation_service.py 变更

```python
def _response_from_route_decision(
    self,
    decision: SceneRouteDecision,
    runtime_result: AgentRuntimeResult,
    *,
    child_text: str,
    parent_policy: object | None,
    companion_action: dict | None = None,
    image_context: object | None = None,
) -> ConversationMessageResponse:
    # Build companion metadata if companion is active
    companion_meta = None
    is_new_companion = False  # 新增标记
    if companion_action is not None:
        companion = companion_action.get("companion")
        action = companion_action.get("action", "none")
        if companion is not None:
            from app.domain.companion_object import resolve_visual_kind
            from app.domain.schemas.conversation import CompanionObjectMeta
            companion_meta = CompanionObjectMeta(
                id=str(companion.id),
                name=companion.name,
                object_type=companion.object_type,
                light_location=companion.light_location,
                state=companion.status,
                action=action if action in ("recall", "co_create") else "none",
                visual_kind=getattr(companion, "visual_kind", None)
                    or resolve_visual_kind(companion.object_type),
            )
            if action == "co_create":
                is_new_companion = True  # 标记为新建

    # 如果是新建 companion，替换回复为确定性模板
    if is_new_companion and companion_meta is not None:
        name = companion_meta.name
        location = companion_meta.light_location or "窗边"
        reply_text = f"{name}，软软的名字\n它轻轻落到{location}啦"
        reply_emotion = "warm"
        quick_actions = []  # 不返回按钮
    else:
        reply_text = runtime_result.reply_text
        reply_emotion = decision.reply_emotion
        quick_actions = self._quick_action_service.actions_for(
            decision=decision,
            child_text=child_text,
            reply_text=runtime_result.reply_text,
            parent_policy=parent_policy,
            conversation_control=runtime_result.model_metadata.get(
                "final_conversation_control"
            ),
        )

    return ConversationMessageResponse(
        reply=Reply(
            text=reply_text,
            emotion=reply_emotion,
            agent_motion=self._agent_motion_for(decision),
        ),
        ui_actions=[
            UiAction(
                actions=[
                    QuickAction(id=action.id, label=action.label)
                    for action in quick_actions
                ]
            )
        ]
        if quick_actions
        else [],
        session_state=SessionState(
            base_scene=decision.base_scene.value,
            active_scene=decision.active_scene.value,
            needs_input=decision.needs_input,
            requires_parent_attention=(
                True if decision.requires_parent_attention else None
            ),
            companion_object=companion_meta,
        ),
    )
```
