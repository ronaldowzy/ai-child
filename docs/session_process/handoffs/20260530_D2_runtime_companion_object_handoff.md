# D2 交接：对话运行时与提示词接入

状态：done，待主控审核

更新时间：2026-05-30

---

## Summary

在对话运行时中接入 D1 的 CompanionObjectService，实现小屋小客人机制在 opening、对话和图片场景中的完整闭环。

---

## Files

### 修改

| 文件 | 说明 |
|---|---|
| `backend/app/services/opening_policy.py` | 新增 `COMPANION_RECALL` opening 模式；OpeningPolicy 新增 companion 字段 |
| `backend/app/services/opening_service.py` | 注入 CompanionObjectService；opening 阶段检查小客人召回；构建 companion metadata 和 ui_actions |
| `backend/app/services/conversation_service.py` | 注入 CompanionObjectService；对话中检测跳过/继续信号；图片成功后输出"起个名字"共创入口 |
| `backend/app/domain/schemas/conversation.py` | 新增 `CompanionObjectMeta` schema；`SessionState` 新增 `companion_object` 字段 |
| `backend/app/tests/test_conversation_opening_api.py` | 修正 `test_bedtime_opening_with_interest_seed_is_low_stimulation` 断言 |
| `backend/app/tests/test_opening_visible_quality.py` | 无修改（`test_bedtime_defer_interest_blocks_exciting_memory` 断言已正确） |

### 新建

| 文件 | 说明 |
|---|---|
| `backend/app/tests/test_companion_object_runtime.py` | D2 集成测试（11 个用例） |
| `docs/session_process/handoffs/20260530_D2_runtime_companion_object_plan.md` | D2 计划文档 |

---

## Child-visible change

1. **首次打开**：低压在场，无小客人召回（与之前一致）
2. **有活跃小客人时打开**：opening 阶段轻召回一次，气泡"{name}今天在{location}呢。要不要给它加一个朋友？"，按钮"加一个朋友"/"先聊别的"
3. **睡前打开**：统一不召回小客人（与之前一致）
4. **图片成功后**：出现"起个名字"共创入口按钮
5. **孩子跳过时**：检测"先聊别的"等信号，调用 mark_skipped()，本会话不再召回
6. **SessionState**：携带 companion_object 元数据（id、name、object_type、light_location、state、action）

---

## Tests

```
bash scripts/test_backend.sh
```

结果：814 passed, 0 failed

新增测试：`test_companion_object_runtime.py`（11 个用例）

---

## Safety

- 睡前统一不召回小客人
- 学习/安全/隐私场景不处理小客人动作
- 不保存原始音频、照片、长篇原文
- 不涉及儿童端文案新增（所有文案来自主控 master-copy）
- 不涉及家长端文案

---

## Product boundary

- 严格遵守主控文档，未自行设计产品方向
- 未新增任何儿童端文案或小白狐话术
- 未扩展为成长档案、兴趣画像、作品库或小客人列表
- companion_object 字段极简（id、name、object_type、light_location、state、action）

---

## Known issues

1. 同会话召回抑制使用进程内存（SessionRecallTracker），服务重启后丢失（K05）
2. 共创意图检测使用轻量关键词规则，可能误判（MVP 可接受）
3. 图片共创入口在 conversation runtime 层实现，不在 AttachmentService 层

---

## 主控确认事项

全部 6 个问题已按主控确认实现：
1. 首次打开小星星：opening 决策 + metadata，不创建小客人
2. 共创意图检测：显式 action + 轻量规则，不新增 prompt 结构化标记
3. 图片共创入口：conversation runtime 层输出，不在 AttachmentService
4. SessionState companion_object：极简字段
5. 召回文案：只引用主控 master-copy
6. 既有 bedtime 测试失败：已修复（断言修正 + 代码逻辑修正）

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是（`bash scripts/test_backend.sh`）
