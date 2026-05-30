# D4 计划：家长端摘要边界

状态：已确认，实现完成

更新时间：2026-05-30

---

## 1. 已阅读文档

```text
README.md
AGENTS.md
docs/提示词与文案归属规则_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
docs/session_process/轻量交接协议_2026_05_30_V0_1.md
docs/session_process/handoffs/20260530_D1_companion_object_handoff.md
docs/session_process/handoffs/20260530_D2_runtime_companion_object_handoff.md
docs/session_process/handoffs/20260530_D3_android_companion_object_handoff.md
docs/小白狐关系与轻连续体验总设计_2026_05_30_V0_1.md
docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md
docs/四个核心场景话术与状态库_2026_05_30_V0_1.md
docs/连续三天真实家庭测试脚本_2026_05_30_V0_1.md
docs/小白狐关系与轻连续体验开发任务清单_2026_05_30_V0_1.md
```

额外阅读的代码文件：

```text
backend/app/services/parent_report_service.py          — 家长日报核心 service（1649 行）
backend/app/services/parent_report_language_v4.py       — prompt 与确定性文案
backend/app/domain/parent_report.py                     — Pydantic domain 模型
backend/app/api/v1/parent_report.py                     — FastAPI 端点
backend/app/repositories/parent_report_repository.py    — DB 持久化
backend/app/db/models.py                                — ParentReportRecord ORM
android/.../data/parent/ParentReportDtos.kt             — Android DTO
android/.../data/parent/ParentReportApiClient.kt        — Android HTTP 客户端
android/.../ui/parent/ParentReportScreen.kt             — Android 家长端 UI
android/.../ui/parent/ParentReportViewModel.kt          — Android ViewModel
```

---

## 2. 任务范围理解

D4 的目标：让家长端日报能高层表达"小白狐关系与轻连续体验"的价值，但不得展示逐字聊天、图片细节、小客人历史、情绪评分、亲密度或监控感内容。

核心约束：
- 家长端只展示高层摘要，不展示逐字对话
- 不展示小客人历史列表、召回/跳过行为细节
- 不展示情绪评分、亲密度、兴趣画像
- 不展示图片详细内容
- 所有家长端敏感文案必须来自 master-copy
- 不改 D1/D2/D3 逻辑
- 不做家长监控页、小客人管理页、成长档案

---

## 3. 当前家长日报/摘要生成链路

### 3.1 数据来源

```text
ParentReportService.get_daily_report(child_id, report_date)
  ├── MemoryService.list_memories()                    → 当天 visible_to_parent=True 的记忆
  └── ConversationPersistenceRepository.list_report_messages()  → 当天对话消息
```

### 3.2 生成策略

```text
model-first + deterministic fallback：
1. 先计算 deterministic fallback report（确定性文案拼接）
2. 调用 LLM（ModelRegistry, task_type=PARENT_REPORT）生成更自然版本
3. LLM 失败（blocked/failed/empty）→ 回退到 deterministic report
```

### 3.3 当前字段

```text
ParentReport:
  child_id, date, summary（500 字以内）
  topic_overview: list[ParentReportTopicOverview]（topic/child_intent/summary/emotion_tone/parent_bridge）
  conversation_summary, learning_observations, expression_observations
  emotion_observations, safety_alerts, suggested_parent_actions
  tonight_parent_bridge, avoid_followup
  generation_status, generated_by, generation_error_code, material_fingerprint, created_at
```

### 3.4 关键发现

**当前日报链路中没有 companion_object 相关内容。**

- ParentReport domain 无 companion_object 字段
- parent_report_service.py 不读取 companion_objects 表
- parent_report_language_v4.py 的 prompt 和确定性文案无小客人相关内容
- Android ParentReportDtos.kt 无 companion_object 字段
- Android ParentReportScreen.kt 无小客人相关 UI

D1 已建立 `companion_objects` 表和 `CompanionObjectService`，但日报链路尚未接入。

---

## 4. 会修改的文件

### 后端

| 文件 | 修改内容 |
|---|---|
| `backend/app/domain/parent_report.py` | 新增 `companion_summary: str | None` 字段 |
| `backend/app/services/parent_report_service.py` | 注入 CompanionObjectService；日报生成时读取当日 companion_object 状态，构建 companion 信号传入 model/deterministic 逻辑 |
| `backend/app/services/parent_report_language_v4.py` | prompt 中新增 companion 相关写作指引；deterministic_narrative_v4 新增 companion 分支；新增 companion 相关确定性文案（来自 master-copy） |
| `backend/app/tests/test_parent_report_service.py` | 新增 companion_summary 相关测试 |

### Android

| 文件 | 修改内容 |
|---|---|
| `android/.../data/parent/ParentReportDtos.kt` | 新增 `companionSummary: String?` 字段和 JSON 解析 |
| `android/.../ui/parent/ParentReportScreen.kt` | 新增"轻共创"展示区块（仅当 companionSummary 非空时显示） |

---

## 5. 不会修改的文件

```text
backend/app/domain/companion_object.py              — D1 已完成，不改
backend/app/repositories/companion_object_repository.py  — D1 已完成，不改
backend/app/services/companion_object_service.py     — D1 已完成，不改
backend/app/services/opening_service.py              — D2 已完成，不改
backend/app/services/conversation_service.py         — D2 已完成，不改
backend/app/services/child_agent_runtime.py          — 不改
backend/app/api/v1/parent_report.py                  — API 端点不变，只是返回数据多一个可选字段
backend/app/repositories/parent_report_repository.py — 持久化层兼容处理，companion_summary 作为可选字段透传
backend/app/db/models.py                             — ParentReportRecord 不改（companion_summary 不单独建列，通过 JSON 或实时查询）
android/.../ui/chat/                                 — D3 已完成，不改
docs/                                                — 不改主控文档
```

---

## 6. 如何表达"轻共创 / 作品分享 / 小屋小客人"

### 6.1 数据信号来源

日报生成时，从 `CompanionObjectService` 读取当日 child_id 的 companion_object 状态：

```text
信号类型                    来源
─────────────────────────────────────────────────
有活跃小客人且今日有共创     companion_object.created_at 或 updated_at 在当日
小客人类型                  companion_object.object_type（小星星/小云朵/画里的小角色等）
小客人来源                  companion_object.source_type（首次打开/拍图/普通聊天/接一句故事）
小客人状态                  companion_object.status（ACTIVE/PAUSED/FADED_OUT）
```

### 6.2 家长端允许的表达（来自 master-copy）

以下文案来自 `docs/四个核心场景话术与状态库_2026_05_30_V0_1.md` 第 8 节和 `docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md` 第 8 节：

```text
今天孩子和小白狐有一次轻松共创。
孩子主动分享了一张作品。
孩子遇到学习卡点时，小白狐陪他一步一步看。
没有发现需要特别留意的风险内容。
今晚可以轻轻问一句：你今天给小白狐看了什么呀？
```

### 6.3 companion_summary 生成逻辑

**deterministic 路径**（LLM 不可用时）：

```python
# 伪代码
if companion_object and companion_object.status == ACTIVE:
    if companion_object.source_type == "拍图":
        companion_summary = "孩子今天和小白狐有一次轻松共创，主动分享了一张作品。"
    elif companion_object.source_type == "首次打开":
        companion_summary = "孩子今天和小白狐有一次轻松共创。"
    elif companion_object.source_type == "接一句故事":
        companion_summary = "孩子今天和小白狐有一次轻松共创。"
    else:
        companion_summary = "孩子今天和小白狐有一次轻松共创。"
else:
    companion_summary = None  # 不展示
```

**model 路径**（LLM 可用时）：

在 system prompt 中新增指引，让 LLM 在 summary 或 mentioned_items 中自然融入 companion 信号，不单独暴露小客人机制细节。

### 6.4 Android 展示

```text
当 companion_summary 非空时，在"今天一句话"下方新增一个区块：
标题："轻共创"
内容：companion_summary 文本

当 companion_summary 为空时，不显示该区块。
```

---

## 7. 如何避免逐字聊天和监控感

### 7.1 已有防线（不需改动）

当前 `parent_report_language_v4.py` 已有以下防线：

```text
MONITORING_STYLE_FORBIDDEN = (
    "给小白狐看的东西",
    "孩子主要聊了",
    "消息数量",
    "条孩子消息",
    "条小白狐回复",
    "逐字聊天记录",
    "孩子今天共有",
    "表达能力较好",
    "孩子表现不错",
)
```

System prompt 已要求：
- 不引用孩子原话
- 不暴露图片内容
- 不写消息数量
- 不贴标签
- 不写话术建议

### 7.2 D4 新增防线

在 system prompt 中新增禁止表达（来自 master-copy）：

```text
禁止出现：
- 系统记录到孩子创建了小客人。
- 孩子与 AI 建立了持续关系。
- 孩子今天完成了小屋互动任务。
- 孩子拒绝继续昨日内容。
- 孩子连续两次跳过小白狐召回。
```

在 deterministic 路径中：
- companion_summary 只使用 master-copy 中的固定表达
- 不暴露小客人名字、类型、位置等细节
- 不暴露召回/跳过次数
- 不暴露小客人生命周期状态变化

### 7.3 不新增的内容

```text
不新增：情绪评分字段
不新增：亲密度字段
不新增：兴趣画像字段
不新增：小客人历史列表字段
不新增：召回/跳过行为详情字段
不新增：逐字聊天字段
不新增：图片细节字段
```

---

## 8. 是否需要读取 companion_objects

**是。** 需要在 `ParentReportService` 中读取 companion_objects 数据。

具体方式：
- `ParentReportService.__init__` 新增可选参数 `companion_object_service: CompanionObjectService | None = None`
- `_generate_daily_report_from_materials` 方法中调用 `companion_object_service.get_active_by_child(child_id)` 获取当日活跃小客人
- 将 companion 信号（是否有活跃小客人、来源类型、状态）传入 deterministic 和 model 路径

不直接查 DB，通过已有的 `CompanionObjectService` 接口访问，保持 D1 的封装。

---

## 9. 测试策略

### 9.1 后端单元测试

新增到 `backend/app/tests/test_parent_report_service.py`（或新建 `test_parent_report_companion.py`）：

```text
1. 有活跃小客人（source_type=首次打开）→ companion_summary 非空
2. 有活跃小客人（source_type=拍图）→ companion_summary 含"分享了一张作品"
3. 无活跃小客人 → companion_summary 为 None
4. 小客人状态为 PAUSED → companion_summary 为 None
5. companion_summary 不包含小客人名字
6. companion_summary 不包含小客人类型细节
7. companion_summary 不包含召回/跳过次数
8. companion_summary 不包含小客人位置
9. deterministic 路径 companion 文案正确
10. model 路径 prompt 中包含 companion 信号
```

### 9.2 测试命令

```bash
bash scripts/test_backend.sh -k "parent_report" -v
```

### 9.3 Android 测试

```bash
bash scripts/android_gradle.sh test
```

验证：
- ParentReportDtos 新增 companionSummary 字段解析正确
- companionSummary 为空时不显示"轻共创"区块
- companionSummary 非空时显示"轻共创"区块

---

## 10. 风险点

### 10.1 CompanionObjectService 依赖注入

`ParentReportService` 当前不依赖 `CompanionObjectService`。新增依赖需确保：
- 构造函数中为可选参数，默认 None
- None 时 companion_summary 为 None（不破坏现有行为）
- 通过 `get_companion_object_service()` 获取默认实例

### 10.2 companion 数据时效性

companion_object 的 `created_at`/`updated_at` 使用 UTC。日报的 `report_date` 使用本地日期。需确保时区对齐。

### 10.3 Staleness 机制

当前 staleness 通过 `material_fingerprint`（SHA256 of memories + conversation_messages）判断。companion_object 变化也应纳入 fingerprint，否则小客人状态变化后日报不会刷新。

### 10.4 LLM prompt 长度

新增 companion 信号到 prompt 中会增加 token 数。当前 prompt 已较长，需确认不超过模型上下文限制。

### 10.5 Android 向后兼容

新增 `companionSummary` 为可选字段（nullable），旧版后端不返回该字段时 Android 应正常处理（`optNullableString` 已有此模式）。

---

## 11. 发现的文档与代码冲突

无明显冲突。D1/D2/D3 交接文档中描述的 companion_object 接口与实际代码一致。

---

## 12. 需要主控确认的问题

1. **companion_summary 是独立字段还是融入 summary？** 建议作为独立可选字段，Android 端可选择性展示。主控是否有不同意见？

2. **companion_summary 的确定性文案是否需要更多变体？** 当前只有"孩子今天和小白狐有一次轻松共创"和"孩子主动分享了一张作品"两句。是否需要根据 source_type 区分更多表达？

3. **"今晚可以轻轻问一句：你今天给小白狐看了什么呀？"是否应出现在 companion_summary 中？** 还是放在 tonight_parent_bridge 中？

4. **小客人状态为 PAUSED 时，家长端是否应看到任何信息？** 当前计划是不展示（companion_summary=None）。主控是否有不同判断？

5. **是否需要在 companion_summary 中区分"首次创建"和"继续共创"？** 例如"孩子今天和小白狐开始了一个新共创"vs"孩子今天继续了之前的小共创"。

6. **model prompt 中 companion 信号的权重？** 是作为独立 evidence packet 条目，还是作为 context 注入？
