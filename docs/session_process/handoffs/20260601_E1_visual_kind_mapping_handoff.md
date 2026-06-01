# E1 交接：visual_kind 数据映射实现

状态：DONE

远程提交：`059379f`

更新时间：2026-06-01

---

## Summary

E1 已完成。新增 `visual_kind` 字段贯穿后端领域模型、数据库、API schema、Android DTO 四层。后端 `resolve_visual_kind()` 从 `object_type` 确定性映射到 6 种 visual_kind，Android 优先从 `visual_kind` 渲染，保留 `objectType` 模糊匹配作为 legacy fallback。

---

## Files

### 新增

```text
backend/alembic/versions/20260601_0008_add_visual_kind_to_companion.py
```

### 修改

```text
backend/app/domain/companion_object.py          新增 VisualKind 枚举、visual_kind 字段、resolve_visual_kind()
backend/app/db/models.py                        CompanionObjectRecord 新增 visual_kind 列
backend/app/domain/schemas/conversation.py      CompanionObjectMeta 新增 visual_kind 字段
backend/app/services/companion_object_service.py create() 调用 resolve_visual_kind()
backend/app/services/opening_policy.py          OpeningPolicy 新增 companion_visual_kind
backend/app/services/opening_service.py         两处 CompanionObjectMeta 构建传入 visual_kind
backend/app/services/conversation_service.py    CompanionObjectMeta 构建传入 visual_kind
backend/app/repositories/companion_object_sql_repository.py  _apply/_to_domain 处理 visual_kind
backend/app/tests/test_conversation_opening_api.py  更新 seed 断言包含 visual_kind
android/.../data/conversation/ConversationDtos.kt   CompanionObjectMeta 新增 visualKind
android/.../ui/chat/XiaobaohuCompanionStage.kt      toCompanionVisualType() 改为从 visual_kind 映射
```

### 不修改

```text
backend/app/providers/
backend/app/core/
backend/app/api/
backend/app/services/safety_engine.py
backend/app/services/scene_orchestrator.py
backend/app/services/parent_report_service.py
backend/app/services/parent_report_language_v4.py
backend/app/services/memory_service.py
```

---

## visual_kind 映射表

| object_type | visual_kind | 说明 |
|---|---|---|
| star | star | 小星星 |
| cloud | cloud | 小云朵 |
| paper_boat | paper_boat | 小纸船 |
| story_gate | tiny_door | 故事里的小门 |
| drawing_character | dino_shadow | 画里的小角色 |
| block_monster | block_light | 积木小怪兽 |
| window_bird | cloud | 窗边小鸟，归入轻柔类 |
| toy_character | block_light | 玩具小客人，归入实体物件类 |
| other | star | 兜底 |

---

## Tests

```text
后端全量：851 passed, 0 failed
后端 companion 专项：82 passed
后端 lint：40 errors（均为 D1 前已有）
Android 单测：BUILD SUCCESSFUL
Android assembleDebug：BUILD SUCCESSFUL
```

---

## Safety

```text
1. 不保存原始图片 — 已遵守
2. 不保存详细图片描述 — 已遵守
3. 不改家长端边界 — 已遵守
4. 不新增儿童端文案 — 已遵守
5. 不重写 prompt — 已遵守
6. visual_kind 只是枚举字符串，不含敏感信息
```

---

## Docs

```text
docs/session_process/handoffs/20260601_E1_visual_kind_mapping_plan.md（计划）
docs/session_process/handoffs/20260601_E1_visual_kind_mapping_handoff.md（本文）
```

---

## Product boundary

```text
1. visual_kind 由后端 resolve_visual_kind() 自动推导，生产路径不允许前端显式传入
2. 旧数据 server_default="star"，SQL repository 读取时兜底
3. Android 优先从 visual_kind 映射，objectType 模糊匹配标注为 legacy fallback
4. 图片共创到 companion_object 的创建链路不在 E1 范围（留给 E3）
5. Android 小物件影子渲染增强不在 E1 范围（留给 E2）
```

---

## Known issues

```text
1. 图片共创（IMAGE_SHARE）到 companion_object 的创建链路未打通，E3 实现。
2. 6 种 visual_kind 在 Android 端当前只有 4 种 CompanionVisualType 对应（StarPoint/CloudShadow/LightSpot/SoftOutline），E2 阶段会增强区分度。
3. audioReadyUsesQueueWhenNotuted 已知失败仍存在，与 E1 无关。
```

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是
