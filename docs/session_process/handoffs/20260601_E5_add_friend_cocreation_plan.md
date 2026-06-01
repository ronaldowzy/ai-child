# E5 加一个朋友轻共创延续计划

状态：待评审

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
docs/session_process/handoffs/20260601_E4_landing_feedback_handoff.md
docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md
docs/小屋小客人共创延续机制设计_2026_05_30_V0_1.md
docs/四个核心场景话术与状态库_2026_05_30_V0_1.md
```

---

## 2. 当前 recall 后 quick_actions 链路现状

### 2.1 召回触发

`opening_service.py` 的 `_check_companion_recall()` 调用 `companion_object_service.can_recall()` 检查是否可召回。条件满足时，`create_opening()` 构建 `OpeningMode.COMPANION_RECALL` 策略。

### 2.2 召回时的 quick_actions

`opening_service.py` 行 319-366，召回模式下生成两个 quick_actions：

```python
QuickAction(id="companion_continue", label="加一个朋友")
QuickAction(id="companion_skip", label="先聊别的")
```

同时构造 `CompanionObjectMeta(state="active", action="recall")`。

### 2.3 quick_action_id 处理

`conversation_service.py` 的 `_check_companion_action()` 处理召回后的 action：

- `companion_skip` → `mark_skipped()`，skip_count+1
- `companion_continue` → 返回 `{"action": "co_create", "companion": companion}`

### 2.4 回复构造

`_response_from_route_decision()` 中，当 `companion_action.action == "co_create"` 时：

- 如果 `is_new_companion` 为 True（首次起名成功），使用确定性模板 `{name}，软软的名字\n它轻轻落到{location}啦`，quick_actions 为空
- 如果 `is_new_companion` 为 False（recall 后点击"加一个朋友"），**当前走通用模型回复路径**，没有确定性模板

### 2.5 关键发现

`companion_continue` 被点击后，当前行为是返回模型自由生成的回复 + companion_meta(state=active, action=co_create)。没有确定性模板，没有 pending 状态等待孩子输入名字，不会更新 safe_summary。

---

## 3. 点击"加一个朋友"后如何识别 quick_action_id

复用现有 `quick_action_id="companion_continue"`，不需要新增 quick_action_id。

处理位置：在 `_check_companion_action()` 中，当检测到 `quick_action_id == "companion_continue"` 且 companion 已存在（recall 场景），不再直接返回 `{"action": "co_create"}`，而是：

1. 在 session 内存中建立 `PendingCompanionExtension` 状态
2. 返回确定性引导话术：`"那我们给它找一个小伙伴\n你可以说一个名字，也可以给我看看"`
3. 返回新的 quick_actions：`[companion_add_name: 说个名字, companion_add_photo: 给小白狐看看]`

---

## 4. 是否需要 pending 状态

需要。新增 `PendingCompanionExtension` 数据类，与现有 `PendingCompanionSeed` 平级，存放在 companion_object_service 的内存 dict 中。

```python
@dataclass(frozen=True)
class PendingCompanionExtension:
    child_id: str
    companion_id: str          # 现有 companion 的 id
    companion_name: str        # 现有 companion 的名字
    requested_at: datetime
```

存储方式：`self._pending_extension: dict[str, PendingCompanionExtension]`，key 为 session_id。

生命周期：

- 点击 `companion_continue` 时创建
- 孩子说名字后消费并清除
- 孩子拍图后消费并清除
- 孩子说 skip 信号时清除
- session 结束时自然丢失（内存态，与 PendingCompanionSeed 一致）

---

## 5. 孩子说名字后如何更新现有 companion，而不是创建第二个 active

### 5.1 识别"加朋友"场景下的名字输入

在 `handle_message()` 中，检查顺序调整为：

1. 先检查 `_check_pending_companion_seed_creation`（首颗星星命名，不变）
2. 再检查是否存在 `PendingCompanionExtension`（加朋友场景）
3. 最后检查 `_check_companion_action`（召回后 skip/continue，不变）

当存在 `PendingCompanionExtension` 且孩子输入文本匹配名字模式时：

- 调用 `companion_object_service.update_safe_summary_append()` 追加朋友信息到现有 companion
- **不调用 `create()`**，不创建新 companion
- 清除 `PendingCompanionExtension`
- 返回确定性模板 + companion_meta(state=active, action=co_create)

### 5.2 不创建第二个 active 的保证

- `companion_object_service.create()` 会自动 RETIRED 旧 active companion（行 123-129），所以即使误调用也会导致旧 companion 消失——但 E5 根本不调用 `create()`
- E5 只调用 `update_safe_summary_append()` 更新现有 companion 的 safe_summary 字段
- companion 的 id、name、object_type、visual_kind、light_location 均不变
- 只有 safe_summary 和 updated_at 变化

---

## 6. 是否支持"给小白狐看看"作为加朋友来源

支持。当 `PendingCompanionExtension` 存在时，孩子拍图走以下路径：

### 6.1 图片成功

- 复用 E3 的确定性模板回复（`我看到{细节}啦 + 像{温柔想象}`）
- 但 quick_action 变为 `companion_add_name: 起个名字`（复用现有 id）
- 孩子起名后，走 5.1 的 update_safe_summary_append 路径
- 图片细节本身不保存到 companion_object，只用于当轮对话回复

### 6.2 图片失败

- 复用 E3 的失败模板
- quick_action 保持 `retake_photo` + `skip_photo`
- 不进入加朋友流程

### 6.3 如何不保存图片细节

图片细节只用于当轮小白狐回复（vision provider 输出 → 确定性模板），不写入 companion_object 的任何字段。safe_summary 只追加 `"又来了一个朋友叫{新名字}"`，不含图片内容。

---

## 7. safe_summary 如何更新

新增 `companion_object_service.update_safe_summary_append()` 方法：

```python
def update_safe_summary_append(
    self,
    companion_id: str,
    append_text: str,
) -> CompanionObject | None:
    """追加文本到现有 companion 的 safe_summary，不替换。"""
    companion = self._repo.get(companion_id)
    if companion is None:
        return None
    new_summary = f"{companion.safe_summary}；{append_text}"
    # 截断到 200 字
    if len(new_summary) > 200:
        new_summary = new_summary[:197] + "…"
    # FORBIDDEN_SUMMARY_MARKERS 检查
    ...
    return self._repo.update(companion_id, safe_summary=new_summary)
```

追加文本格式：

- 说名字来源：`"又来了一个朋友叫{新名字}"`
- 拍图来源：`"又来了一个朋友叫{新名字}"`（同样不含图片细节）

最终 safe_summary 示例：`"这颗星星叫小棉花；又来了一个朋友叫小云朵"`

---

## 8. metadata 如何返回给 Android

### 8.1 companion_meta 构建

加朋友成功后，companion_meta 保持：

```python
CompanionObjectMeta(
    id=companion.id,           # 不变
    name=companion.name,       # 不变（仍是原小客人名字）
    object_type=companion.object_type,
    light_location=companion.light_location,
    state="active",
    action="co_create",        # 复用现有 action
    visual_kind=companion.visual_kind,
)
```

### 8.2 Android 端行为

不改 Android。

现有逻辑：

- `shouldShowVisual()` 在 `state == "active" && action == "co_create"` 时返回 `true`
- `CompanionLightPoint` 入场动画（fade in 1.2s + scale 0.8→1.0）自动播放
- 视觉上保持当前小物件影子，不新增第二个影子

### 8.3 设计意图

Android 视觉最多保持当前小物件，或显示非常淡的小陪伴点。如现有 Android 不支持陪伴点，E5 不强行做。

---

## 9. 话术如何使用主控模板

### 9.1 现有 master-copy 中可用的话术

来自 `docs/四个核心场景话术与状态库_2026_05_30_V0_1.md`：

**召回入口话术**（已实现）：

```text
{name}今天在{location}呢
要不要给它加一个朋友？
```

**按钮文案**（已实现）：

```text
加一个朋友
先聊别的
```

**放下话术**（已实现）：

```text
好呀，我们聊新的
好，那它先在窗边待着
```

### 9.2 E5 需要的话术

**点击"加一个朋友"后的引导话术**（来自主控 V0.2 设计文档 §7.2）：

```text
那我们给它找一个小伙伴
你可以说一个名字，也可以给我看看
```

**起名成功后的反馈话术**（来自主控 V0.2 设计文档 §7.2）：

```text
{name}，也来小屋里待一会儿啦
```

### 9.3 需要主控确认的话术

以下话术来自主控 V0.2 设计文档和主控倾向描述，但尚未出现在 `四个核心场景话术与状态库` 的 master-copy 中：

| 话术 | 来源 | 状态 |
|---|---|---|
| 那我们给它找一个小伙伴 | 主控 V0.2 §7.2 | **需要主控补充到 master-copy** |
| 你可以说一个名字，也可以给我看看 | 主控 V0.2 §7.2 | **需要主控补充到 master-copy** |
| {name}，也来小屋里待一会儿啦 | 主控倾向描述 | **需要主控补充到 master-copy** |

E5 实现时只复制主控确认的精确文本。如果主控修正文案，E5 立即同步修改。

---

## 10. 如何避免宠物化、列表化、奖励化

### 10.1 不做列表

- 不创建新 companion，只更新现有 companion 的 safe_summary
- companion 数量始终为 1（一个 active）
- 不返回 companion 列表、不返回朋友数量

### 10.2 不做宠物化

- 不新增心情值、亲密度、饥饿值
- 不说"它会等你"、"它想你了"、"它有点难过"
- companion 的视觉表现不变（同一个物件影子）

### 10.3 不做奖励化

- 不说"新朋友已解锁"、"收集成功"、"获得成就"
- 不返回奖励闪光、收集提示
- quick_actions 不新增"查看收藏"、"小客人列表"

### 10.4 不做历史展示

- 不展示历史小客人
- 不展示朋友数量
- safe_summary 是后端内部字段，不直接展示给儿童端

---

## 11. 会修改的文件

### 11.1 后端

| 文件 | 修改内容 |
|---|---|
| `backend/app/services/companion_object_service.py` | 新增 `PendingCompanionExtension` 数据类；新增 `_pending_extension` dict；新增 `begin_extension()` / `get_pending_extension()` / `clear_pending_extension()` 方法；新增 `update_safe_summary_append()` 方法 |
| `backend/app/services/conversation_service.py` | `_check_companion_action()` 中处理 recall 后 `companion_continue`：建立 pending extension + 返回确定性引导话术；`handle_message()` 中新增检查 `PendingCompanionExtension` 的分支；`_response_from_route_decision()` 中处理 extension 创建成功后的确定性反馈模板 |
| `backend/app/services/modality_manager.py` | 当 `PendingCompanionExtension` 存在时，图片成功后的 quick_action 从 `companion_name` 保持不变（复用），但后续消费时走 extension 路径而非 seed 路径 |
| `backend/app/tests/test_add_friend_extension.py` | 新增：覆盖 extension 创建、名字输入更新 safe_summary、skip 清除、图片路径、禁用表达检查 |

### 11.2 Android

不修改。

### 11.3 文档

| 文件 | 修改内容 |
|---|---|
| `docs/session_process/handoffs/20260601_E5_add_friend_cocreation_plan.md` | 本文（计划） |
| `docs/session_process/handoffs/20260601_E5_add_friend_cocreation_handoff.md` | 交接文档（实现后） |

---

## 12. 不会修改的文件

```text
backend/app/api/                          — 不改 API 路由
backend/app/providers/                    — 不改外部 provider
backend/app/core/                         — 不改核心配置
backend/app/db/models.py                  — 不改数据库 schema
backend/app/repositories/                 — 不改数据访问层
backend/app/domain/companion_object.py    — 不改领域模型枚举/字段
backend/app/domain/schemas/conversation.py — 不改 API schema（复用现有 QuickAction）
backend/app/services/safety_engine.py     — 不改安全引擎
backend/app/services/scene_orchestrator.py — 不改场景编排
backend/app/services/parent_report_service.py — 不改家长日报
backend/app/services/parent_report_language_v4.py — 不改日报语言
backend/app/services/memory_service.py    — 不改记忆服务
backend/app/services/prompt_manager.py    — 不改提示词管理
backend/app/services/opening_service.py   — 不改开场服务
backend/app/services/opening_policy.py    — 不改开场策略
backend/app/services/quick_action_service.py — 不改通用 quick_action
android/                                  — 不改 Android
```

---

## 13. 测试策略

### 13.1 新增测试文件

`backend/app/tests/test_add_friend_extension.py`

### 13.2 测试用例

```text
1. test_companion_continue_creates_pending_extension
   点击 companion_continue 后，PendingCompanionExtension 被创建

2. test_companion_continue_returns_deterministic_guidance
   点击 companion_continue 后，返回确定性引导话术

3. test_companion_continue_returns_add_friend_quick_actions
   点击 companion_continue 后，返回 [companion_add_name, companion_add_photo]

4. test_child_says_name_updates_safe_summary
   孩子说名字后，现有 companion 的 safe_summary 被追加

5. test_child_says_name_does_not_create_new_companion
   孩子说名字后，不创建新 companion，active companion 数量仍为 1

6. test_child_says_name_returns_deterministic_feedback
   孩子说名字后，返回 "{name}，也来小屋里待一会儿啦"

7. test_child_says_name_returns_companion_meta_active_co_create
   companion_meta 保持 state=active, action=co_create

8. test_child_says_skip_clears_extension
   孩子说"先聊别的"后，PendingCompanionExtension 被清除

9. test_extension_name_input_uses_existing_companion_id
   更新的是现有 companion 的 safe_summary，不是新 companion

10. test_safe_summary_append_format
    safe_summary 追加格式正确："原摘要；又来了一个朋友叫{name}"

11. test_safe_summary_append_truncation
    safe_summary 超过 200 字时正确截断

12. test_safe_summary_append_forbidden_markers
    safe_summary 追加内容不含禁用标记

13. test_image_success_during_extension_returns_name_action
    extension 存在时，图片成功后返回 companion_add_name quick_action

14. test_image_success_during_extension_no_image_detail_saved
    图片细节不写入 companion_object

15. test_extension_no_forbidden_phrases
    确定性话术不含禁用表达：新朋友已解锁、收集成功、它会等你、明天一定要来看
```

### 13.3 现有测试保护

运行现有 companion 相关测试确保不回归：

```bash
bash scripts/test_backend.sh
```

预期：851+ passed, 0 failed（现有测试不受影响）。

---

## 14. 风险点

### 14.1 PendingCompanionExtension 内存态

与 PendingCompanionSeed 一致，extension 状态存在进程内存中。服务重启后丢失。

影响：孩子点击"加一个朋友"后如果服务重启，需要重新点击。首版可接受（K05 已知限制）。

### 14.2 companion_continue 的双重语义

当前 `companion_continue` 在 `_check_companion_action()` 中直接返回 `{"action": "co_create"}`。E5 需要改变这个行为：当 companion 已存在时，不再直接返回 co_create，而是建立 pending extension。

需要确保：

- 首颗星星起名流程不受影响（走 `_check_pending_companion_seed_creation`，不走 `_check_companion_action`）
- recall 后的 companion_skip 不受影响
- 只有 recall 后的 companion_continue 行为变化

### 14.3 safe_summary 追加与现有 FORBIDDEN_SUMMARY_MARKERS

追加的文本 `"又来了一个朋友叫{name}"` 需要通过现有的禁用标记检查。如果孩子起的名字恰好包含禁用词（如真实姓名），会被拦截。

处理方式：名字本身经过 `_safe_child_name()` 清洗（复用 E3 逻辑），截断到 10 字，过滤隐私敏感词。

### 14.4 话术不在 master-copy 中

当前 `四个核心场景话术与状态库` 中没有 E5 需要的 3 句话术。主控 V0.2 设计文档中有，但需要确认是否已批准为 master-copy。

阻塞条件：主控确认话术前，E5 编码中的话术部分按占位处理，测试中用占位文本，主控确认后精确替换。

### 14.5 图片路径与 E3 的交互

当 PendingCompanionExtension 存在时，孩子拍图走 E3 的图片处理逻辑（vision provider、确定性模板），但 quick_action 的消费逻辑需要区分是"首颗星星命名"还是"加朋友"。

区分方式：在 `_check_pending_companion_seed_creation` 中，如果 pending extension 存在，quick_action_id == "companion_name" 走 extension 路径而非 seed 路径。

---

## 15. 需要主控确认的问题

### 问题 1：话术确认

以下 3 句话术是否已批准为 master-copy 精确文本？如有修正，请给出最终版本：

```text
A. 点击"加一个朋友"后的引导话术：
   那我们给它找一个小伙伴
   你可以说一个名字，也可以给我看看

B. 起名成功后的反馈话术：
   {name}，也来小屋里待一会儿啦

C. 引导话术后的按钮文案：
   说个名字
   给小白狐看看
```

### 问题 2：图片路径的起名反馈话术

当孩子通过"给小白狐看看"路径加朋友时，起名成功后反馈话术是否与说名字路径一致？

```text
{name}，也来小屋里待一会儿啦
```

还是需要不同话术？

### 问题 3：safe_summary 追加格式

追加文本格式 `"又来了一个朋友叫{新名字}"` 是否合适？还是用其他表述？

### 问题 4：quick_action_id 命名

引导话术后的两个按钮：

```text
id="companion_add_name", label="说个名字"
id="companion_add_photo", label="给小白狐看看"
```

是否复用现有 `companion_name` 和 `给小白狐看看` 按钮 id，还是新增？

### 问题 5：recall 后 companion_continue 行为变化的兼容性

当前 recall 后点击 `companion_continue` 直接返回 co_create + companion_meta。E5 改为先建立 pending extension + 引导话术。Android 端当前如何处理 recall 后的 `companion_continue` 点击？是否需要 Android 配合修改？

### 问题 6：连续加朋友

如果孩子第一次加朋友成功后，本轮会话内是否还能再次点击"加一个朋友"？

主控倾向是"一次轻共创延续"，建议：加朋友成功后，本会话不再出现"加一个朋友"按钮。需要主控确认。
