# E5 交接：加一个朋友轻共创延续

状态：DONE

更新时间：2026-06-01

---

## Summary

E5 已完成。recall 后点击"加一个朋友"进入 `PendingCompanionExtension` 待定状态，返回确定性引导话术（`那我们给它找一个小伙伴\n你可以说一个名字，也可以给我看看`）+ 3 个 quick_actions（`companion_friend_name` / `companion_friend_image` / `companion_skip`）。孩子说名字后更新现有 companion 的 safe_summary（追加 `孩子给小屋小客人加了一个小伙伴：{name}`），不创建新 companion。完成后返回确定性反馈（`{name}，也来小屋里待一会儿啦`），quick_actions 为空。

---

## Files

### 修改

```text
backend/app/services/companion_object_service.py
  - 新增 PendingCompanionExtension 数据类
  - 新增 _pending_extension dict
  - 新增 begin_extension() / get_pending_extension() / clear_pending_extension()
  - 新增 update_safe_summary_append() 方法

backend/app/services/conversation_service.py
  - _check_companion_action()：companion_continue 改为建立 pending extension + 返回 co_create_guidance
  - _check_companion_action()：extension 存在时直接返回 None，让 extension handler 处理
  - 新增 _check_pending_companion_extension() 方法
  - handle_message()：新增 extension_result 检查，插入 created_companion_action 和 companion_action_result 之间
  - _check_pending_companion_seed_creation()：companion_name 时检查 extension 存在则跳过 seed 创建
  - _response_from_route_decision()：新增 co_create_guidance 和 extension_done 两种 action 处理

backend/app/tests/test_companion_object_runtime.py
  - test_quick_action_id_continue_maps_to_co_create → test_quick_action_id_continue_maps_to_co_create_guidance
```

### 新增

```text
backend/app/tests/test_add_friend_extension.py
  - 19 个测试覆盖 extension 生命周期、safe_summary 追加、确定性话术、禁用表达、skip、无名字输入
```

### 不修改

```text
backend/app/api/
backend/app/providers/
backend/app/core/
backend/app/db/models.py
backend/app/repositories/
backend/app/domain/companion_object.py
backend/app/domain/schemas/conversation.py
backend/app/services/safety_engine.py
backend/app/services/scene_orchestrator.py
backend/app/services/parent_report_service.py
backend/app/services/parent_report_language_v4.py
backend/app/services/memory_service.py
backend/app/services/prompt_manager.py
backend/app/services/opening_service.py
backend/app/services/opening_policy.py
backend/app/services/modality_manager.py
backend/app/services/quick_action_service.py
android/
```

---

## 核心变更

### 1. PendingCompanionExtension 数据类

```python
@dataclass(frozen=True)
class PendingCompanionExtension:
    child_id: str
    companion_id: str
    companion_name: str
    requested_at: datetime
```

内存态，key 为 session_id，与 PendingCompanionSeed 平级。服务重启后丢失（K05 已知限制）。

### 2. companion_continue 行为变化

之前：直接返回 `{"action": "co_create", "companion": companion}`

之后：建立 PendingCompanionExtension + 返回 `{"action": "co_create_guidance", "companion": companion}`

### 3. 确定性话术

**引导话术**（co_create_guidance）：

```text
那我们给它找一个小伙伴
你可以说一个名字，也可以给我看看
```

**完成话术**（extension_done）：

```text
{name}，也来小屋里待一会儿啦
```

### 4. quick_actions

**引导话术后**：

```text
companion_friend_name: 说个名字
companion_friend_image: 给小白狐看看
companion_skip: 先聊别的
```

**完成后**：空列表，不再显示"加一个朋友"

### 5. safe_summary 更新

追加格式：`"孩子给小屋小客人加了一个小伙伴：{name}"`

最终示例：`"这颗星星叫小棉花；孩子给小屋小客人加了一个小伙伴：小云朵"`

### 6. companion_meta

加朋友成功后继续返回：

```text
state = "active"
action = "co_create"
```

不新增 friend_count、friends、inventory 等字段。

### 7. 图片路径支持

当 PendingCompanionExtension 存在时：

- 孩子点击"给小白狐看看" → Android 触发相机
- 图片成功 → modality manager 返回 companion_name quick_action
- companion_name 时跳过 seed 创建（extension 存在）
- 孩子说名字 → extension handler 处理，更新 safe_summary
- 图片细节不保存到 companion_object

---

## Tests

```text
后端全量：889 passed, 0 failed
后端 lint：修改文件 0 errors（全量 2 errors 为修改前已有 EXCITING_TYPES/VisualKind unused import）
```

### 新增测试用例（19 个）

```text
TestPendingCompanionExtension:
  - test_begin_and_get_extension
  - test_get_extension_wrong_child
  - test_clear_extension

TestUpdateSafeSummaryAppend:
  - test_append_to_existing_summary
  - test_append_format
  - test_append_truncation
  - test_append_nonexistent_companion
  - test_append_preserves_companion_fields
  - test_append_does_not_create_second_active

TestCompanionContinueCreatesExtension:
  - test_companion_continue_returns_guidance
  - test_companion_continue_creates_pending_extension

TestExtensionNameInput:
  - test_child_says_name_updates_safe_summary
  - test_child_says_name_does_not_create_new_companion
  - test_extension_clears_pending_after_completion
  - test_extension_returns_companion_meta_active_co_create

TestExtensionDeterministicFeedback:
  - test_extension_done_returns_deterministic_template
  - test_extension_done_no_quick_actions
  - test_guidance_returns_deterministic_template
  - test_guidance_returns_quick_actions

TestExtensionNoForbiddenPhrases:
  - test_guidance_no_forbidden_phrases
  - test_completion_no_forbidden_phrases

TestExtensionSkip:
  - test_quick_action_skip_clears_extension
  - test_text_skip_signal_clears_extension
  - test_short_flat_reply_during_extension

TestExtensionNoNameReturnsNone:
  - test_long_text_not_name_returns_none
  - test_empty_text_returns_none
```

---

## Safety

```text
1. 不创建第二个 active companion — 已遵守（只调用 update_safe_summary_append，不调用 create）
2. 不新增儿童端文案 — 已遵守（使用主控确认的精确文本）
3. 不重写 prompt — 已遵守
4. 不改 Android — 已遵守
5. 不改家长端 — 已遵守
6. 不保存图片细节 — 已遵守（图片细节只用于当轮回复，不写入 companion_object）
7. 不新增奖励/任务/宠物感 — 已遵守
8. 禁用表达检查已覆盖：保存成功、已加入你的小屋、任务完成、明天一定要来看、它会等你、你获得了、解锁了、新朋友、新客人、收集成功、朋友数量、列表
```

---

## Docs

```text
docs/session_process/handoffs/20260601_E5_add_friend_cocreation_plan.md（计划）
docs/session_process/handoffs/20260601_E5_add_friend_cocreation_handoff.md（本文）
```

---

## Product boundary

```text
1. companion_continue 不再直接返回 co_create，改为 co_create_guidance + pending extension
2. 加朋友只更新 safe_summary，不创建新 companion
3. 完成后 quick_actions 为空，不进入连续加朋友循环
4. 图片路径支持但不保存图片细节
5. companion_meta 保持 state=active/action=co_create
6. Android 现有 quick_actions 渲染机制可直接复用
7. 不新增 friend_count、friends、inventory 等字段
```

---

## Known issues

```text
1. PendingCompanionExtension 内存态（K05），服务重启后丢失
2. companion_friend_image 由 Android 处理相机触发，后端不直接感知该 quick_action
3. 图片路径中 companion_name quick_action 的 label 是"起个名字"，在 extension 场景下语义略有偏差（但功能正确）
```

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是

---

## Commit

待提交
