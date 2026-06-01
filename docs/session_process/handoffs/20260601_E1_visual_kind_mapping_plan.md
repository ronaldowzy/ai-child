# E1 计划：visual_kind 数据映射方案

项目：`ai-child`

任务：给小白狐看看 2.0 与小屋可见共创增强 —— 视觉类型与数据映射

状态：计划待主控确认

更新时间：2026-06-01

---

## 1. 已阅读文档列表

```text
1. README.md
2. AGENTS.md
3. docs/提示词与文案归属规则_V0_1.md
4. docs/CODEX_PROGRESS_BOARD_V0_1.md
5. docs/session_process/README.md
6. docs/session_process/SHARED_CONTEXT_V0_1.md
7. docs/session_process/轻量交接协议_2026_05_30_V0_1.md
8. docs/给小白狐看看2_0与小屋可见共创增强设计_2026_06_01_V0_1.md
9. docs/小白狐关系与轻连续体验总设计_2026_05_30_V0_1.md
10. docs/小屋小客人共创延续机制设计_2026_05_30_V0_1.md
11. docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md
12. docs/四个核心场景话术与状态库_2026_05_30_V0_1.md
13. docs/session_process/handoffs/20260530_D5_full_qa_handoff.md
14. docs/session_process/handoffs/20260530_D5_true_device_gap_review_checklist.md
15. backend/app/domain/companion_object.py
16. backend/app/db/models.py
17. backend/app/domain/schemas/conversation.py
18. backend/app/services/companion_object_service.py
19. backend/app/repositories/companion_object_repository.py
20. backend/app/repositories/companion_object_sql_repository.py
21. backend/app/services/opening_service.py
22. backend/app/services/conversation_service.py
23. backend/app/services/parent_report_service.py
24. backend/alembic/versions/20260530_0007_create_companion_objects.py
25. android/app/src/main/java/com/childai/companion/data/conversation/ConversationDtos.kt
26. android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt
```

---

## 2. 当前 companion_object 数据结构现状

### 2.1 领域模型字段

backend/app/domain/companion_object.py 中 `CompanionObject`：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | str | UUID |
| child_id | str | 孩子 ID |
| name | str | 小客人名字，最长 80 |
| object_type | CompanionObjectType | 物件类型枚举 |
| source_type | CompanionObjectSource | 来源枚举 |
| safe_summary | str | 安全短摘要，最长 200 |
| light_location | str | 轻位置，必须是 LIGHT_LOCATIONS 之一 |
| status | CompanionObjectStatus | 生命周期状态 |
| last_recalled_at | datetime/None | 最近召回时间 |
| recall_count | int | 召回次数 |
| skip_count | int | 跳过次数 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 2.2 CompanionObjectType 枚举（当前 9 种）

```text
STAR = "star"
CLOUD = "cloud"
DRAWING_CHARACTER = "drawing_character"
TOY_CHARACTER = "toy_character"
BLOCK_MONSTER = "block_monster"
PAPER_BOAT = "paper_boat"
WINDOW_BIRD = "window_bird"
STORY_GATE = "story_gate"
OTHER = "other"
```

### 2.3 CompanionObjectSource 枚举（当前 4 种）

```text
FIRST_OPEN = "first_open"
IMAGE_SHARE = "image_share"
CHAT_STORY = "chat_story"
STORY_CHAIN = "story_chain"
```

### 2.4 当前生产路径

只有 first_open + star 的种子起名链路真实走通。IMAGE_SHARE / CHAT_STORY / STORY_CHAIN 枚举值已存在，但没有真实调用 CompanionObjectService.create() 的代码路径。

### 2.5 当前 Android 视觉映射

Android 端 `XiaobaohuCompanionStage.kt` 中 `String.toCompanionVisualType()` 通过字符串模糊匹配把 object_type 映射到 4 种视觉类型：

```text
包含"星"或等于"star" -> StarPoint
包含"云"或等于"cloud" -> CloudShadow
包含"光"或"影" -> LightSpot
其他 -> SoftOutline
```

### 2.6 当前 API 输出

`CompanionObjectMeta`（Pydantic schema）只输出：

```text
id, name, object_type, light_location, state, action
```

不包含 visual_kind。Android 直接用 object_type 字符串做模糊匹配。

---

## 3. 是否需要新增 visual_kind 字段

**需要。**

理由：

```text
1. 当前 object_type 有 9 种值，但设计文档定义的首版小物件影子只有 6 种。
   9 -> 6 的映射不是一对一，需要明确规则。

2. 当前 Android 的模糊字符串匹配不可靠：
   - drawing_character / toy_character / window_bird / other 都会 fallback 到 SoftOutline。
   - 没有 paper_boat、tiny_door、dino_shadow、block_light 的视觉区分。

3. 如果不加 visual_kind，Android 需要自己维护一套 object_type -> 视觉类型的映射逻辑，
   且无法区分"同一 object_type 不同来源可能对应不同视觉"的情况。

4. visual_kind 是后端确定性输出，Android 只负责渲染，符合架构原则。
```

---

## 4. visual_kind 放在各层的位置

### 4.1 领域模型

在 `CompanionObject` 中新增字段：

```python
visual_kind: str  # star / cloud / paper_boat / tiny_door / dino_shadow / block_light
```

新增 `VisualKind` 枚举：

```python
class VisualKind(StrEnum):
    STAR = "star"
    CLOUD = "cloud"
    PAPER_BOAT = "paper_boat"
    TINY_DOOR = "tiny_door"
    DINO_SHADOW = "dino_shadow"
    BLOCK_LIGHT = "block_light"
```

### 4.2 数据库

`companion_objects` 表新增列：

```python
visual_kind = Column(String(40), nullable=True, server_default="star")
```

新增 Alembic 迁移文件，revision 依赖 `20260530_0007`。

列设为 nullable=True + server_default="star"，兼容旧数据。

### 4.3 API metadata

`CompanionObjectMeta`（Pydantic schema）新增字段：

```python
visual_kind: str = "star"
```

带默认值，旧数据或未设置时返回 "star"。

### 4.4 Android DTO

`CompanionObjectMeta`（Kotlin data class）新增字段：

```kotlin
val visualKind: String = "star"
```

`fromJson()` 中读取 `json.optString("visual_kind", "star")`。

`toCompanionVisualType()` 改为从 visualKind 映射，不再从 objectType 模糊匹配。

### 4.5 CompanionObjectCreateRequest

新增可选字段：

```python
visual_kind: str | None = None
```

如果不传，由 service 层根据 object_type 自动推导。

---

## 5. 如何兼容旧数据

```text
1. 数据库列设为 nullable=True，server_default="star"。
   旧记录自动获得 visual_kind="star"，不会破坏现有数据。

2. API schema 中 visual_kind: str = "star"，即使旧数据没有该字段也返回默认值。

3. Android DTO 中 visualKind 默认 "star"，fromJson 兼容缺失字段。

4. 迁移脚本不需要 backfill，因为 server_default 在 ALTER TABLE 时会自动填充已有行。
```

---

## 6. object_type / source_type / 图片共创结果如何映射 visual_kind

### 6.1 核心映射规则

后端提供确定性映射函数 `resolve_visual_kind(object_type, source_type) -> VisualKind`：

| object_type | visual_kind | 说明 |
|---|---|---|
| star | star | 小星星，直接对应 |
| cloud | cloud | 小云朵，直接对应 |
| paper_boat | paper_boat | 小纸船，直接对应 |
| story_gate | tiny_door | 故事里的小门 -> 小门 |
| drawing_character | dino_shadow | 画里的小角色 -> 小恐龙影子（最典型） |
| block_monster | block_light | 积木小怪兽 -> 小积木光点 |
| window_bird | cloud | 窗边小鸟 -> 归入小云朵类（轻柔自然） |
| toy_character | block_light | 玩具小客人 -> 归入小积木光点类（实体小物件） |
| other | star | 兜底 -> 小星星 |

### 6.2 source_type 的作用

source_type 不直接决定 visual_kind，但影响 object_type 的选择：

```text
FIRST_OPEN -> object_type=star -> visual_kind=star（种子起名，固定小星星）
IMAGE_SHARE -> object_type 由图片内容决定 -> visual_kind 由 object_type 推导
CHAT_STORY -> object_type 由对话内容决定 -> visual_kind 由 object_type 推导
STORY_CHAIN -> object_type 由故事内容决定 -> visual_kind 由 object_type 推导
```

### 6.3 图片共创的映射路径

当图片共创链路打通后（E3 阶段），流程：

```text
孩子拍图 -> 模型识别内容 -> 决定 object_type -> resolve_visual_kind -> 存储 visual_kind
```

示例：

```text
图片是恐龙画 -> object_type=drawing_character -> visual_kind=dino_shadow
图片是积木 -> object_type=block_monster -> visual_kind=block_light
图片是云朵 -> object_type=cloud -> visual_kind=cloud
图片是纸船 -> object_type=paper_boat -> visual_kind=paper_boat
图片无法识别具体类型 -> object_type=other -> visual_kind=star
```

### 6.4 映射函数实现位置

在 `backend/app/domain/companion_object.py` 中新增：

```python
def resolve_visual_kind(object_type: str, source_type: str | None = None) -> str:
    """从 object_type 推导 visual_kind。"""
    _OBJECT_TYPE_TO_VISUAL_KIND = {
        CompanionObjectType.STAR: VisualKind.STAR,
        CompanionObjectType.CLOUD: VisualKind.CLOUD,
        CompanionObjectType.PAPER_BOAT: VisualKind.PAPER_BOAT,
        CompanionObjectType.STORY_GATE: VisualKind.TINY_DOOR,
        CompanionObjectType.DRAWING_CHARACTER: VisualKind.DINO_SHADOW,
        CompanionObjectType.BLOCK_MONSTER: VisualKind.BLOCK_LIGHT,
        CompanionObjectType.WINDOW_BIRD: VisualKind.CLOUD,
        CompanionObjectType.TOY_CHARACTER: VisualKind.BLOCK_LIGHT,
        CompanionObjectType.OTHER: VisualKind.STAR,
    }
    try:
        ot = CompanionObjectType(object_type)
    except ValueError:
        return VisualKind.STAR
    return _OBJECT_TYPE_TO_VISUAL_KIND.get(ot, VisualKind.STAR)
```

---

## 7. 不保存原始图片和详细图片描述的方案

E1 阶段不涉及图片处理链路变更。当前约束不变：

```text
1. 不保存原始图片到数据库或长期存储。
2. 不保存详细图片描述。
3. 只保存 safe_summary（最长 200 字，经过 FORBIDDEN_SUMMARY_MARKERS 过滤）。
4. visual_kind 只是一个枚举字符串，不含图片内容信息。
5. 图片共创链路的真实对接在 E3 阶段，E1 只建好 visual_kind 的数据通道。
```

---

## 8. 不改家长端边界的方案

```text
1. visual_kind 不出现在家长日报摘要中。
2. 家长端展示逻辑不因 visual_kind 变化。
3. parent_report_service.py 不需要修改。
4. parent_report_language_v4.py 不需要修改。
5. 家长端仍只知道"今天有一次轻共创"，不知道具体是什么视觉类型。
```

---

## 9. 会修改的文件

### 9.1 后端

| 文件 | 修改内容 |
|---|---|
| backend/app/domain/companion_object.py | 新增 VisualKind 枚举；CompanionObject 新增 visual_kind 字段；新增 resolve_visual_kind() 函数；CompanionObjectCreateRequest 新增可选 visual_kind |
| backend/app/db/models.py | CompanionObjectRecord 新增 visual_kind 列 |
| backend/alembic/versions/20260601_0008_add_visual_kind_to_companion.py | 新增迁移文件 |
| backend/app/domain/schemas/conversation.py | CompanionObjectMeta 新增 visual_kind 字段 |
| backend/app/services/companion_object_service.py | create() 中调用 resolve_visual_kind() 推导并存储 visual_kind |
| backend/app/services/opening_service.py | 构建 CompanionObjectMeta 时传入 visual_kind |
| backend/app/services/conversation_stream_service.py | _route_payload() 中 companion_object 包含 visual_kind |
| backend/app/services/conversation_service.py | 构建 companion_object metadata 时传入 visual_kind |

### 9.2 Android

| 文件 | 修改内容 |
|---|---|
| android/.../data/conversation/ConversationDtos.kt | CompanionObjectMeta 新增 visualKind 字段；fromJson 读取 visual_kind |
| android/.../ui/chat/XiaobaohuCompanionStage.kt | toCompanionVisualType() 改为从 visualKind 映射，不再从 objectType 模糊匹配 |

### 9.3 测试

| 文件 | 修改内容 |
|---|---|
| backend/app/tests/test_companion_object_service.py | 新增 visual_kind 相关测试 |
| backend/app/tests/test_companion_object_runtime.py | 更新 companion_object metadata 断言 |
| android/.../ui/chat/CompanionObjectVisualTest.kt | 更新视觉类型映射测试 |
| android/.../data/ConversationDtosTest.kt | 新增 visualKind 解析测试 |

---

## 10. 不会修改的文件

```text
backend/app/providers/                   不改
backend/app/core/                        不改
backend/app/api/                         不改（接口契约由 schema 层处理）
backend/app/services/safety_engine.py    不改
backend/app/services/scene_orchestrator.py 不改
backend/app/services/parent_report_service.py 不改
backend/app/services/parent_report_language_v4.py 不改
backend/app/services/memory_service.py   不改
backend/app/repositories/companion_object_sql_repository.py  不改（字段由 ORM 自动映射）
android/app/src/main/java/.../ui/chat/XiaobaohuVisualStateResolver.kt  不改
android/app/src/main/java/.../ui/chat/XiaobaohuVisualStateRuntime.kt   不改
android/app/src/main/java/.../ui/chat/ChatViewModel.kt                 不改
docs/                                    不改（本文档除外）
```

---

## 11. 测试策略

### 11.1 后端单元测试

```text
1. resolve_visual_kind() 测试：
   - 每种 object_type 映射到正确的 visual_kind。
   - 未知 object_type fallback 到 star。
   - 大小写和空格容错。

2. CompanionObjectService.create() 测试：
   - 传入 object_type="star" 时，创建后 visual_kind="star"。
   - 传入 object_type="drawing_character" 时，visual_kind="dino_shadow"。
   - 不传 visual_kind 时自动推导。
   - 传入 visual_kind 时使用传入值。

3. CompanionObjectMeta schema 测试：
   - 序列化包含 visual_kind。
   - visual_kind 默认值为 "star"。

4. opening/recall 路径测试：
   - opening seed 返回 visual_kind="star"。
   - recall 返回 active companion 的 visual_kind。
   - stream route payload 包含 visual_kind。

5. 现有测试不破坏：
   - test_companion_object_service.py 全部通过。
   - test_companion_object_runtime.py 全部通过。
   - test_parent_report_companion.py 全部通过。
```

### 11.2 Android 单元测试

```text
1. CompanionObjectMeta.fromJson() 解析 visual_kind。
2. visualKind 缺失时默认 "star"。
3. toCompanionVisualType() 从 visualKind 正确映射到 CompanionVisualType。
4. 6 种 visual_kind 各自映射到正确的视觉渲染类型。
```

### 11.3 集成验证

```text
1. 后端单测全量通过：bash scripts/test_backend.sh
2. 后端 lint 通过：bash scripts/lint_backend.sh
3. Android 单测通过：bash scripts/android_gradle.sh testDebugUnitTest
4. Android 构建通过：bash scripts/android_gradle.sh assembleDebug
```

---

## 12. 风险点

### 12.1 数据库迁移

```text
风险：新增列可能影响已有 companion_objects 记录。
缓解：nullable=True + server_default="star"，旧记录自动获得默认值。
验证：迁移后查询旧记录确认 visual_kind="star"。
```

### 12.2 object_type -> visual_kind 映射合理性

```text
风险：window_bird -> cloud、toy_character -> block_light 的归并可能不够精确。
缓解：首版先用确定性映射，后续可根据真实使用数据调整。
备注：当前生产路径只有 star，其他 object_type 尚未真实使用，映射可迭代。
```

### 12.3 Android 向后兼容

```text
风险：新版 Android 读取旧后端（没有 visual_kind 字段的响应）。
缓解：Android fromJson 使用 optString("visual_kind", "star")，缺失时默认 star。
验证：模拟旧后端响应确认 Android 不崩溃。
```

### 12.4 不破坏现有 star 种子链路

```text
风险：修改 create() 逻辑可能影响已通过的 D5 链路。
缓解：resolve_visual_kind 对 star 返回 star，行为不变。
验证：test_companion_object_runtime 专项测试全部通过。
```

---

## 13. 需要主控确认的问题

### Q1：object_type -> visual_kind 映射表是否确认？

当前映射：

```text
star -> star
cloud -> cloud
paper_boat -> paper_boat
story_gate -> tiny_door
drawing_character -> dino_shadow
block_monster -> block_light
window_bird -> cloud
toy_character -> block_light
other -> star
```

window_bird 归入 cloud、toy_character 归入 block_light 是否合适？还是需要新增 visual_kind？

### Q2：visual_kind 是否允许创建时由调用方显式传入，还是必须由后端自动推导？

当前方案：可选传入，不传则由 resolve_visual_kind() 自动推导。

### Q3：旧数据 server_default 用 "star" 是否合适？

当前数据库中只有 first_open + star 的记录，server_default="star" 与实际一致。是否有异议？

### Q4：E1 是否需要同时打通图片共创到 companion_object 的创建链路？

当前方案：E1 只建好 visual_kind 数据通道和映射函数，不打通图片共创创建链路（那是 E3 范围）。是否确认？

### Q5：Android toCompanionVisualType() 是否改为纯从 visual_kind 映射，完全废弃 objectType 模糊匹配？

当前方案：改为从 visualKind 映射，objectType 模糊匹配作为 fallback 保留。是否确认？

---

## 附录：修改文件汇总

```text
新增：
  backend/alembic/versions/20260601_0008_add_visual_kind_to_companion.py

修改：
  backend/app/domain/companion_object.py
  backend/app/db/models.py
  backend/app/domain/schemas/conversation.py
  backend/app/services/companion_object_service.py
  backend/app/services/opening_service.py
  backend/app/services/conversation_stream_service.py
  backend/app/services/conversation_service.py
  backend/app/tests/test_companion_object_service.py
  backend/app/tests/test_companion_object_runtime.py
  android/.../data/conversation/ConversationDtos.kt
  android/.../ui/chat/XiaobaohuCompanionStage.kt
  android/.../ui/chat/CompanionObjectVisualTest.kt
  android/.../data/ConversationDtosTest.kt

不修改：
  其余所有文件
```
