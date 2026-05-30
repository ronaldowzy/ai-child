# D1 交接：后端小屋小客人与轻记忆

状态：done（返修完成），待主控审核

更新时间：2026-05-30（返修更新）

---

## Summary

实现"小屋小客人"最小后端数据结构、状态流转和轻记忆召回规则。

---

## Files

### 新建

| 文件 | 说明 |
|---|---|
| `backend/app/domain/companion_object.py` | 领域模型：枚举、schema、常量 |
| `backend/app/repositories/companion_object_repository.py` | Repository Protocol + InMemory 实现 |
| `backend/app/repositories/companion_object_sql_repository.py` | SQLAlchemy 实现 |
| `backend/app/services/companion_object_service.py` | 业务逻辑层 |
| `backend/app/tests/test_companion_object_service.py` | 39 个单元测试 |
| `backend/alembic/versions/20260530_0007_create_companion_objects.py` | 数据库迁移 |
| `docs/session_process/handoffs/20260530_D1_companion_object_plan.md` | 技术计划 |

### 修改

| 文件 | 说明 |
|---|---|
| `backend/app/db/models.py` | 新增 `CompanionObjectRecord` ORM 模型 + partial unique index |

---

## Child-visible change

D1 是纯后端数据层，无直接儿童端可见变化。为 D2（对话运行时）提供以下接口：

- `CompanionObjectService.create()` — 创建小客人
- `CompanionObjectService.can_recall()` — 判断是否可召回
- `CompanionObjectService.mark_recalled()` — 标记已召回
- `CompanionObjectService.mark_skipped()` — 标记跳过
- `CompanionObjectService.update()` — 更新小客人（召回后继续）
- `CompanionObjectService.unpause()` — 暂放→活跃（孩子主动提起）
- `CompanionObjectService.get_active_by_child()` — 查询当前活跃小客人
- `CompanionObjectService.is_faded_out()` — 检查是否已淡出

---

## Tests

```
bash scripts/test_backend.sh -k "test_companion_object" -v
```

结果：41 passed, 0 failed

完整回归：802 passed, 1 failed（已有的 `test_bedtime_opening_with_interest_seed_is_low_stimulation`，非 D1 引入）

---

## Safety

- 不保存原始音频、照片、长篇原文
- 创建时执行禁记内容过滤（隐私、负面事件、学习题目、保密）
- safe_summary 领域层限制 200 字，DB 字段 500 字留余量
- 不召回负面事件、隐私、真实人物或学习内容
- 睡前统一不主动召回
- 一个 child_id 最多一个 active 小客人（service + partial unique index 双重保证）
- 不涉及儿童端文案、prompt 或家长端文案

---

## Product boundary

- 严格遵守主控文档，未自行设计产品方向
- 未新增任何儿童端文案或小白狐话术
- 未扩展为成长档案、兴趣画像、作品库或小客人列表
- OTHER 类型仅在安全过滤通过且无法归类时使用

---

## Known issues

1. 同会话召回抑制使用进程内存（`SessionRecallTracker`），服务重启后丢失。v0.1 可接受（K05），后续需持久化。
2. "兴奋故事线"判断通过 `EXCITING_TYPES` 集合硬编码。MVP 睡前统一不召回，此集合暂未在召回逻辑中使用，预留供 D2 扩展。
3. `test_conversation_opening_api.py::test_bedtime_opening_with_interest_seed_is_low_stimulation` 已有失败，非 D1 引入。

## 返修记录（2026-05-30）

**返修 1：修正 skip_count 阻断召回逻辑**
- 移除 `can_recall()` 中 `skip_count > 0` 的永久阻断
- `mark_skipped()` 新增 `session_id` 参数，跳过后标记到 `SessionRecallTracker`，同会话不再召回
- skip_count = 1 时状态仍为 ACTIVE，未来新会话/新日期可召回
- skip_count >= 2 时变为 PAUSED，不主动召回
- 新增测试：`test_recall_skip_once_allows_future_session`、`test_recall_skip_once_allows_different_session_same_day`

**返修 2：SQL 仓储不自动创建 Child**
- 移除 `_ensure_child()` 自动创建 Child 的逻辑
- child_id 不存在时抛出 `CompanionObjectRepositoryUnavailable` 错误
- 调用方需确保 child_id 已存在于 children 表

---

## Next session needs

D2（对话运行时与提示词接入）需要知道：

1. `CompanionObjectService` 已就绪，可通过 `get_companion_object_service()` 获取实例
2. `can_recall()` 接收 `child_id`、`session_id`、`is_bedtime` 参数，返回 `CompanionObject | None`
3. 创建小客人需要 `CompanionObjectCreateRequest`，包含 name、object_type、source_type、safe_summary、light_location
4. light_location 限定：窗边、地毯边、小白狐旁边、窗外
5. 召回后孩子继续，调用 `update()` 更新现有小客人
6. 跳过调用 `mark_skipped()`，连续 2 次自动 PAUSED
7. PAUSED 状态下孩子主动提起且愿意继续，调用 `unpause()` 回到 ACTIVE
8. 所有儿童端可见文案必须从主控 master-copy 复制

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是（`bash scripts/test_backend.sh`）

---

## 主控确认事项

全部 6 个问题已由主控确认，无遗留。
