# D1 技术计划：后端小屋小客人与轻记忆

状态：approved，进入编码

更新时间：2026-05-30

---

## 1. 任务范围

实现"小屋小客人"的最小后端数据结构、状态流转和轻记忆召回规则。

### 必须做

1. 新建 `companion_objects` 数据库表和 SQLAlchemy 模型
2. 新建 `CompanionObject` 领域模型（Pydantic schema）
3. 新建 `CompanionObjectRepository`（Protocol + InMemory + SQLAlchemy 实现）
4. 新建 `CompanionObjectService`，封装业务逻辑：
   - 创建小客人（含禁记内容过滤）
   - 召回判断（含召回频率限制、同会话抑制、睡前过滤）
   - 跳过处理（跳过计数、连续跳过→暂放）
   - 状态流转（活跃→暂放→不再召回）
   - 过期自然淡出（7 天未被提起）
   - 更新小客人（召回后孩子继续时）
5. Alembic 迁移脚本
6. 单元测试覆盖全部规则

### 明确不做

- 不做儿童端文案、小白狐话术（D2 范围）
- 不做 Android 视觉呈现（D3 范围）
- 不做家长端摘要（D4 范围）
- 不做小客人列表、历史、收藏、作品库
- 不做成长档案、兴趣画像
- 不保存原始音频、照片、长篇原文
- 不新增 prompt 模板
- 不修改 opening_policy.py 或 opening_service.py

---

## 2. 文件清单

### 新建文件

| 文件 | 说明 |
|---|---|
| `backend/app/domain/companion_object.py` | 小客人领域模型 |
| `backend/app/repositories/companion_object_repository.py` | Repository Protocol + InMemory |
| `backend/app/repositories/companion_object_sql_repository.py` | SQLAlchemy 实现 |
| `backend/app/services/companion_object_service.py` | 业务逻辑层 |
| `backend/app/tests/test_companion_object_service.py` | 单元测试 |
| `backend/alembic/versions/20260530_0007_create_companion_objects.py` | 数据库迁移 |

### 修改文件

| 文件 | 说明 |
|---|---|
| `backend/app/db/models.py` | 新增 `CompanionObjectRecord` |

### 不修改

- `opening_policy.py`、`opening_service.py`、`child_agent_runtime.py` — D2 职责
- `prompt_manager.py`、`scene_orchestrator.py` — D2 职责
- `light_co_creation_service.py` — D2 对接时再考虑
- `memory_service.py`、`relationship_memory.py` — 小客人是独立实体
- `android/` — D3 范围
- `docs/` 主控文档 — 开发方不修改

---

## 3. 数据结构

### 3.1 领域枚举

```python
class CompanionObjectStatus(StrEnum):
    ACTIVE = "active"       # 活跃，可召回
    PAUSED = "paused"       # 暂放，不主动召回
    RETIRED = "retired"     # 不再召回

class CompanionObjectType(StrEnum):
    STAR = "star"
    CLOUD = "cloud"
    DRAWING_CHARACTER = "drawing_character"
    TOY_CHARACTER = "toy_character"
    BLOCK_MONSTER = "block_monster"
    PAPER_BOAT = "paper_boat"
    WINDOW_BIRD = "window_bird"
    STORY_GATE = "story_gate"
    OTHER = "other"         # 仅安全过滤通过且无法归类时使用

class CompanionObjectSource(StrEnum):
    FIRST_OPEN = "first_open"
    IMAGE_SHARE = "image_share"
    CHAT_STORY = "chat_story"
    STORY_CHAIN = "story_chain"

LIGHT_LOCATIONS = ("窗边", "地毯边", "小白狐旁边", "窗外")
```

### 3.2 领域模型

```python
class CompanionObject(BaseModel):
    id: str
    child_id: str
    name: str                           # 最长 80 字
    object_type: CompanionObjectType
    source_type: CompanionObjectSource
    safe_summary: str                   # 最长 200 字（service 校验）
    light_location: str                 # 限定 LIGHT_LOCATIONS
    status: CompanionObjectStatus
    last_recalled_at: datetime | None
    recall_count: int
    skip_count: int
    created_at: datetime
    updated_at: datetime
```

### 3.3 数据库表

```python
class CompanionObjectRecord(Base, TimestampMixin):
    __tablename__ = "companion_objects"

    id: str                     # PK, UUID
    child_id: str               # FK -> children.id
    name: str(80)
    object_type: str(40)
    source_type: str(40)
    safe_summary: str(500)      # DB 留余量，service 层限制 200
    light_location: str(40)
    status: str(40)
    last_recalled_at: datetime | None
    recall_count: int           # default 0
    skip_count: int             # default 0
```

FK 指向 `children.id`（`Child` 表主键）。加 partial unique index：`child_id` + `status` WHERE `status = 'active'`。

---

## 4. 状态流转

```
创建 → ACTIVE
  ├── 召回 → recall_count++, last_recalled_at 更新
  ├── 跳过 → skip_count++
  │     └── skip_count >= 2 → PAUSED
  ├── 召回后孩子继续 → 更新 safe_summary / light_location（保持 ACTIVE）
  └── 被新小客人替换 → RETIRED

PAUSED
  ├── 孩子主动提起且明确愿意继续 → ACTIVE
  └── 7 天未被提起 → 自然淡出（查询时过滤，不主动删除）

RETIRED → 终态
```

### 主控确认的规则

- "被提起"：孩子主动提起，或系统召回后孩子明确选择继续。不包括系统单方面召回。
- PAUSED 不主动召回；只有孩子主动提起且明确愿意继续，才可回到 ACTIVE。
- MVP 睡前统一不主动召回任何小客人；孩子主动提起时可轻接并收短。
- 创建新小客人时，旧 active / paused 自动 retired，儿童端不提示退场。
- 召回后孩子继续，默认更新现有小客人，不创建第二个 active。

---

## 5. 召回判断逻辑

```python
def can_recall(child_id, session_id, is_bedtime) -> CompanionObject | None:
    companion = repo.get_active_by_child(child_id)
    if not companion:
        return None
    if is_bedtime:                          # MVP 睡前统一不召回
        return None
    if session_tracker.has_recalled(session_id):  # 同会话抑制
        return None
    if companion.skip_count > 0:            # 被跳过过，本会话不再召回
        return None
    if companion.recall_count >= 2 and days_since(companion.last_recalled_at) < 7:
        return None                         # 7 天内最多 2 次
    if companion.last_recalled_at and is_same_day(companion.last_recalled_at, now()):
        return None                         # 每天最多 1 次
    return companion
```

同会话召回抑制：进程内存 dict `[session_id → set(child_id)]`。标注 v0.1 限制。

---

## 6. 禁记内容过滤

创建时检查 `safe_summary`，命中以下关键词则拒绝：

- 隐私：地址、学校、班级、电话、真实姓名、校服、校徽
- 负面事件：吵架、批评、打架、受伤、被骂、冲突
- 负面情绪原文：哭了、害怕了、生气了、很烦、好累
- 学习：题目、答案、作业、考试
- 保密：保密、秘密、隐瞒、不要告诉

---

## 7. 测试策略

`backend/app/tests/test_companion_object_service.py`，使用 InMemory repository：

1. 创建安全小客人 → 成功
2. 一个孩子一个活跃 → 旧的自动 retired
3. 隐私内容 → 拒绝
4. 负面事件 → 拒绝
5. 学习题目 → 拒绝
6. 第二天可召回 → 通过
7. 同会话只召回一次 → 第二次 None
8. 跳过后不再召回 → None
9. 连续跳过两次 → PAUSED
10. 睡前不召回 → None
11. 7 天内最多 2 次 → 第 3 次 None
12. 每天最多 1 次 → 同天第 2 次 None
13. PAUSED 孩子主动提起 → ACTIVE
14. 更新小客人 → 字段正确
15. 过期淡出 → 不出现在候选

---

## 8. 风险

| 风险 | 缓解 |
|---|---|
| 小客人与现有 memory 系统关系不清晰 | 独立实体，不混入 memory_items |
| 同会话抑制进程内存重启丢失 | 标注 v0.1 限制 |
| 禁记关键词不完整 | 先实现主控明确列出的项 |
| "兴奋故事线"判断标准不明确 | MVP 睡前统一不召回 |

---

## 9. 待确认问题

主控已确认全部 6 个问题，无遗留。
