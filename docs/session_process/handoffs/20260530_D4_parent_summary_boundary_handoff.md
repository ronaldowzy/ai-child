# D4 交接：家长端摘要边界

状态：done，待主控审核

更新时间：2026-05-30

---

## Summary

让家长端日报能高层表达"小白狐关系与轻连续体验"的价值：当孩子当天有轻共创/作品分享/故事接龙时，家长日报展示一句独立的 companion_summary，但不展示逐字聊天、图片细节、小客人名字、位置、召回/跳过行为。

---

## Files

### 修改

| 文件 | 说明 |
|---|---|
| `backend/app/domain/parent_report.py` | 新增 `companion_summary: str | None` 字段 |
| `backend/app/services/parent_report_service.py` | 注入 CompanionObjectService；新增 `_get_companion_signal()` 方法；deterministic/model/failed 三条路径均支持 companion_summary 和 tonight_parent_bridge；material_fingerprint 包含 companion 信号 |
| `backend/app/services/parent_report_language_v4.py` | 新增 `COMPANION_FORBIDDEN` 禁止表达列表；新增 `companion_deterministic_summary()` 函数（3 类确定性文案）；system prompt 新增 companion 写作指引 |
| `backend/app/repositories/parent_report_repository.py` | `_to_domain()` 新增 `companion_summary=None`（实时计算，不持久化） |
| `android/.../data/parent/ParentReportDtos.kt` | 新增 `companionSummary: String?` 字段和 JSON 解析 |
| `android/.../ui/parent/ParentReportScreen.kt` | 新增"轻共创"区块（companionSummary 非空时显示） |

### 新建

| 文件 | 说明 |
|---|---|
| `backend/app/tests/test_parent_report_companion.py` | 19 个单元测试覆盖 companion_summary 全路径 |

---

## Child-visible change

D4 是家长端变更，无直接儿童端可见变化。

家长端变化：
1. **有轻共创时**：日报新增"轻共创"区块，显示"今天孩子和小白狐有一次轻松共创。"或"孩子主动分享了一张作品。"或"今天孩子和小白狐接了一点小故事。"
2. **有轻共创时**：tonight_parent_bridge 显示"今晚可以轻轻问一句：你今天给小白狐看了什么呀？"
3. **无轻共创时**：不显示"轻共创"区块，行为与 D4 前完全一致
4. **PAUSED 状态小客人**：不展示（避免家长追问）

---

## Tests

```
bash scripts/test_backend.sh -k "test_parent_report_companion" -v
```

结果：19 passed, 0 failed

完整回归：

```
bash scripts/test_backend.sh
```

结果：840 passed, 0 failed

Android：

```
bash scripts/android_gradle.sh test
```

结果：241 tests completed, 1 failed（`ChatViewModelStreamTest > audioReadyUsesQueueWhenNotMuted`，非 D4 引入，D3 已记录）

```
bash scripts/android_gradle.sh assembleDebug
```

结果：BUILD SUCCESSFUL

---

## Safety

- companion_summary 只使用 master-copy 固定表达，不暴露小客人名字、类型、位置、召回/跳过次数
- PAUSED 状态小客人不展示，避免家长追问孩子行为
- companion_signal 只传布尔/枚举级别给 model prompt（had_light_cocreation + cocreation_kind），不传 name/location/counts
- 不新增情绪评分、亲密度、兴趣画像字段
- 不展示逐字聊天、图片细节、小客人历史
- system prompt 新增 companion 禁止表达列表

---

## 文案来源

所有 companion_summary 文案来自主控 master-copy：
- `docs/四个核心场景话术与状态库_2026_05_30_V0_1.md` 第 8 节
- `docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md` 第 8 节
- 主控确认的 3 类确定性表达

---

## Product boundary

- 严格遵守主控文档和主控确认的 6 点修正
- 未自行设计产品方向或文案
- 未新增任何未经主控批准的家长端表达
- 未扩展为监控页、小客人管理页或成长档案
- 未改 D1/D2/D3 逻辑

---

## 主控确认事项执行记录

| 确认点 | 执行方式 |
|---|---|
| 1. companion_summary 独立字段 | ParentReport 新增 companion_summary 字段，不融入 summary |
| 2. 只保留 3 类确定性表达 | companion_deterministic_summary() 只返回 3 种文案 |
| 3. "今晚轻轻问一句"放 tonight_parent_bridge | companion_signal 有 companion 时设置 tonight_parent_bridge |
| 4. PAUSED 不展示 | _get_companion_signal 检查 status==ACTIVE |
| 5. 不区分首次/继续 | 统一表达为"轻松共创" |
| 6. model prompt 不注入详细信号 | payload 只传 had_light_cocreation + cocreation_kind |

---

## Known issues

1. companion_summary 不持久化到 DB，每次实时计算。旧版 persisted report 返回时 companion_summary=None，但 staleness 机制（material_fingerprint 包含 companion 信号）会触发重新生成。
2. `ChatViewModelStreamTest > audioReadyUsesQueueWhenNotMuted` 已有失败，非 D4 引入。

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是（`bash scripts/test_backend.sh`、`bash scripts/android_gradle.sh test`、`bash scripts/android_gradle.sh assembleDebug`）
