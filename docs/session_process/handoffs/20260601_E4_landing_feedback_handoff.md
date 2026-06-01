# E4 交接：起名后"落到小屋里"的反馈强化

状态：DONE

更新时间：2026-06-01

---

## Summary

E4 已完成。起名成功后，后端不再依赖模型自由生成回复，改为使用确定性模板：`{name}，软软的名字\n它轻轻落到{location}啦`。起名成功后不返回任何 quick_actions，避免任务感。companion_meta 保持 `state=active/action=co_create`，Android 端现有入场动画（fade in 1.2s）可正常触发。

---

## Files

### 修改

```text
backend/app/services/conversation_service.py
  - _response_from_route_decision()：新增 is_new_companion 标记
  - 当 companion_action 为 co_create 时，替换回复文本为确定性模板
  - quick_actions 返回空列表
```

### 新增

```text
backend/app/tests/test_companion_landing_feedback.py
  - 10 个测试覆盖：确定性模板内容、禁用表达检查、不同名字/位置、co_create/recall/无 companion 场景
```

### 不修改

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
android/
```

---

## 核心变更

### 1. 确定性模板

起名成功后，回复文本固定为：

```text
{name}，软软的名字
它轻轻落到{light_location}啦
```

- `name`：孩子起的名字
- `light_location`：companion 的位置，为空时兜底"窗边"

### 2. quick_actions 处理

起名成功后，`ui_actions` 返回空列表 `[]`。

不返回任何按钮，包括：
- 不返回"先聊别的"
- 不返回"继续"
- 不返回"完成"

### 3. companion_meta 构建

起名成功后，companion_meta 保持：

```text
state = "active"
action = "co_create"
visual_kind = 由 resolve_visual_kind() 推导
```

不新增 action（如 landed / co_create_landed）。

### 4. Android 端行为

不改 Android。

现有逻辑：
- `shouldShowVisual()` 在 `state == "active" && action == "co_create"` 时返回 `true`
- `CompanionLightPoint` 入场动画（fade in 1.2s + scale 0.8→1.0）自动播放

---

## Tests

```text
后端全量：863 passed, 0 failed
后端 lint：修改文件 0 errors（全量 43 errors 为修改前已有）
Android assembleDebug：BUILD SUCCESSFUL
```

### 新增测试用例

```text
1. test_naming_success_returns_deterministic_template：起名成功后返回确定性模板
2. test_naming_success_companion_meta_fields：companion_meta 字段正确
3. test_deterministic_template_content：模板包含名字和位置
4. test_deterministic_template_no_forbidden_phrases：模板不含禁用表达
5. test_deterministic_template_with_different_locations：不同位置模板正确
6. test_deterministic_template_with_different_names：不同名字模板正确
7. test_response_from_route_decision_with_co_create：co_create 返回确定性模板
8. test_response_from_route_decision_co_create_no_quick_actions：co_create 无 quick_actions
9. test_response_from_route_decision_co_create_companion_meta：co_create companion_meta 正确
10. test_response_from_route_decision_recall_uses_model_reply：recall 使用模型回复
11. test_response_from_route_decision_no_companion_uses_model_reply：无 companion 使用模型回复
12. test_default_location_when_empty：空位置兜底"窗边"
```

---

## Safety

```text
1. 不新增儿童端文案 — 已遵守（只使用主控确认的模板）
2. 不改 prompt — 已遵守
3. 不改 Android — 已遵守
4. 不改家长端 — 已遵守
5. 不新增奖励/任务/宠物感 — 已遵守
6. 禁用表达检查已覆盖：保存成功、已加入你的小屋、任务完成、明天一定要来看、它会等你、你获得了、解锁了、新朋友、新客人
```

---

## Docs

```text
docs/session_process/handoffs/20260601_E4_landing_feedback_plan.md（计划）
docs/session_process/handoffs/20260601_E4_landing_feedback_handoff.md（本文）
```

---

## Product boundary

```text
1. 确定性模板统一使用"轻轻落到"，不按 visual_kind 区分动词
2. quick_actions 为空，不返回"先聊别的"
3. 不新增状态气泡
4. 不新增 action（复用 state=active/action=co_create）
5. 不改 Android 入场动画
6. light_location 为空时兜底"窗边"
```

---

## Known issues

```text
1. 确定性模板固定，可能在某些场景下显得不够自然（首版可接受）
2. 模型生成的回复被完全丢弃（E4 目标是"明确感到落到小屋"，确定性模板更可靠）
3. PendingCompanionSeed 仍在内存中（K05 已知限制），服务重启后丢失
```

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是

---

## Commit

待提交
