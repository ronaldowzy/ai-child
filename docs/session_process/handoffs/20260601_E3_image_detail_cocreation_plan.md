# E3 计划：拍图后细节承接与图片共创创建链路

项目：`ai-child`

状态：待主控确认

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
docs/session_process/handoffs/20260530_D5_full_qa_handoff.md
docs/session_process/handoffs/20260530_D5_true_device_gap_review_checklist.md
docs/四个核心场景话术与状态库_2026_05_30_V0_1.md
```

代码文件：

```text
backend/app/services/modality_manager.py
backend/app/services/child_agent_runtime.py
backend/app/services/conversation_service.py
backend/app/services/companion_object_service.py
backend/app/services/attachment_service.py
backend/app/domain/companion_object.py
backend/app/domain/attachment.py
```

---

## 2. 当前图片上传 / image_context / attachment / conversation runtime 链路现状

### 2.1 图片上传

两条路径，均在 `backend/app/api/v1/conversation_attachment.py`：

- **JSON 路径**：`POST /conversation/attachment`，接收 base64 `image_data_uri`，调用 `AttachmentService.create_attachment()`
- **Multipart 路径**：`POST /attachments/images`，接收文件，调用 `AttachmentService.create_real_image_upload()`

两条路径最终都经过：

```text
MIME/size 校验
  -> _recognize_with_model_vision()  调用 ModelRegistry VISION task
  -> 解析 JSON 输出 -> RecognizedContent (type, text, confidence, ...)
  -> ModalityManager.decide_image_attachment()  质量门控
  -> 保存 AttachmentRecord
  -> 返回 AttachmentCreateResponse (reply, quick_actions, session_state)
```

### 2.2 image_context 在对话中的流转

```text
ConversationService.handle_message()
  -> attachment_service.get_image_context(attachments)
  -> 返回 ImageAttachmentContext (attachment_id, image_purpose, recognized_type, recognized_text, child_caption)
  -> image_context.to_prompt_context() 转为 dict
  -> 传入 AgentRuntimeRequest.conversation_metadata["image_context"]
```

### 2.3 ChildAgentRuntime 处理

```text
ChildAgentRuntime.run()
  -> Fast path 阻断 (有图片不走 fast path)
  -> PromptManager.compose(image_context=...) 注入 prompt layer
  -> ModelRegistry.generate(CHILD_CHAT)
  -> _image_context_repair_reply() 修复模型拒绝看图的回复
```

### 2.4 当前问题（E3 需要解决）

| 问题 | 当前表现 | E3 目标 |
|---|---|---|
| quick_actions 过多 | 图片成功后返回 `[起名字, 讲故事, 说说看]` 三个按钮 | 只返回一个：`起个名字` |
| 回复不符合模板 | `"我看到像是{detail}。你可以给它起个名字，或者告诉我发生了什么。"` | `"我看到{细节}啦\n像{温柔想象}\n要不要给它起个名字？"` |
| 图片失败仍可能有共创入口 | confidence < 0.65 时返回 `[我来说说, 再拍一张]` | 失败时不出现任何共创入口 |
| quick_action id 不一致 | ModalityManager 返回 `id="give_name"`，ConversationService 监听 `id="companion_name"` | 统一为 `companion_name` |
| object_type 硬编码 | `begin_seed_naming()` 固定传 `object_type=STAR` | 根据 `recognized_type` 映射 |
| 修复回复模板不符 | `_image_context_repair_reply()` 使用自由生成文本 | 使用确定性模板 |

---

## 3. 图片成功后如何生成"一个具体细节"的安全短句

### 3.1 数据来源

Vision provider（当前为 mimo）返回 JSON：

```json
{
  "child_summary": "圆圆的小角",
  "context_summary": "...",
  "recognized_type": "toy",
  "confidence": 0.85
}
```

`child_summary` 已经是面向儿童的短描述，直接用作"具体细节"。

### 3.2 "温柔想象"的生成方式

不使用模型自由生成。使用基于 `recognized_type` 的确定性映射表：

```text
recognized_type    -> 温柔想象短语
child_drawing      -> 像一个小世界
art_feedback       -> 像一个小世界
toy                -> 像一个小伙伴
object             -> 像一个小秘密
handmade           -> 像一个小故事
daily_life         -> 像一幅小画
cloud              -> 像一朵小云
default/空         -> 软软的
```

### 3.3 组装模板

```text
我看到{child_summary}啦
像{温柔想象短语}
要不要给它起个名字？
```

当 `child_summary` 为空时，使用兜底：

```text
我看到一个小东西啦
软软的
要不要给它起个名字？
```

### 3.4 安全约束

- `child_summary` 来自 vision provider，已经过 `_strip_image_detail_labels()` 和 `_looks_private_for_child_detail()` 过滤
- 温柔想象短语为固定枚举，不包含任何隐私信息
- 最终回复不保存到 companion_object 的 safe_summary 中
- safe_summary 只保存：`"{name}来自图片分享"`（如 `"小棉花来自图片分享"`）

---

## 4. 图片失败后如何保证不进入共创

### 4.1 失败判定条件

以下任一条件视为图片失败：

```text
1. recognized_content.type == "privacy_sensitive"
2. recognized_content.type in ("unclear", "low_confidence", "unsafe_unknown")
3. recognized_content.confidence < IMAGE_OBSERVATION_CONFIDENCE_THRESHOLD (0.65)
4. recognized_content.text 为空
```

### 4.2 失败时的行为

```text
quick_actions: []  （空列表，不返回任何按钮）
reply_text: 使用 master-copy 失败文案
```

master-copy 失败文案（来自四个核心场景话术与状态库 3.8）：

```text
这张图还没看到
可以再试一次，也可以先不看
```

### 4.3 代码保障

`ModalityManager.decide_image_attachment()` 中：

- privacy_sensitive 分支：quick_actions 只有 `[知道了, 问家长]`，无共创入口（已正确）
- confidence < 0.65 分支：当前返回 `[我来说说, 再拍一张]`，**需改为空列表**
- 成功分支：只返回 `[companion_name: 起个名字]`

`_image_context_repair_reply()` 中：

- `unclear` / `low_confidence` 分支：不返回共创入口（当前已正确）
- 所有修复回复不包含"起个名字"或"编个小故事"

---

## 5. 图片成功后如何只返回一个 quick action：起个名字

### 5.1 当前代码

`ModalityManager.decide_image_attachment()` 成功分支（line 75-92）：

```python
quick_actions=[
    QuickAction(id="give_name", label="起个名字"),
    QuickAction(id="tell_story", label="讲个故事"),
    QuickAction(id="say_what_happened", label="说说看"),
]
```

### 5.2 改为

```python
quick_actions=[
    QuickAction(id="companion_name", label="起个名字"),
]
```

变更点：
1. `id` 从 `"give_name"` 改为 `"companion_name"`，与 `ConversationService._check_pending_companion_seed_creation()` 监听的 id 一致
2. 删除 `tell_story` 和 `say_what_happened`
3. 只保留一个按钮

---

## 6. 点击"起个名字"后如何建立 image naming pending 状态

### 6.1 当前链路（已有，E3 复用）

```text
Android 点击"起个名字"
  -> 发送消息，quick_action_id="companion_name"
  -> ConversationService.handle_message()
  -> _check_pending_companion_seed_creation(quick_action_id="companion_name")
  -> CompanionObjectService.begin_seed_naming(session_id, child_id, object_type, ...)
  -> 注册 PendingCompanionSeed 到内存 dict
```

### 6.2 E3 改动

`begin_seed_naming()` 当前硬编码 `object_type=STAR`。E3 需要：

1. 在 `PendingCompanionSeed` 中新增 `recognized_image_type: str | None` 字段
2. `begin_seed_naming()` 接收 `recognized_image_type` 参数
3. `_check_pending_companion_seed_creation()` 从 `image_context` 获取 `recognized_type` 并传入

这样下一轮孩子说名字时，可以根据 `recognized_image_type` 推导正确的 `object_type`。

---

## 7. 孩子说"叫xxx / 名字是xxx"后如何调用 CompanionObjectService.create()

### 7.1 当前链路（已有，E3 复用 + 修正）

```text
孩子说"叫小棉花"
  -> ConversationService.handle_message()
  -> _check_pending_companion_seed_creation()
  -> pending = svc.get_pending_seed_naming(session_id, child_id)
  -> companion_name = _extract_pending_companion_name("叫小棉花")  # 正则提取 "小棉花"
  -> svc.create(CompanionObjectCreateRequest(...))
```

### 7.2 E3 改动

在 `svc.create()` 调用处，`object_type` 不再固定为 `pending.object_type`（STAR），而是根据 `pending.recognized_image_type` 推导：

```python
object_type = _resolve_object_type_from_image(pending.recognized_image_type)
```

映射表（定义在 `conversation_service.py` 或 `companion_object.py`）：

```text
recognized_type       -> object_type
child_drawing         -> DRAWING_CHARACTER
art_feedback          -> DRAWING_CHARACTER
toy                   -> TOY_CHARACTER
handmade              -> TOY_CHARACTER
object                -> OTHER
daily_life            -> CLOUD
cloud                 -> CLOUD
default/空/None       -> STAR
```

`safe_summary` 改为：

```python
safe_summary=f"{companion_name}来自图片分享"
```

不再使用 `"这颗星星叫{companion_name}"`（那是 opening seed 的模板）。

---

## 8. source_type=image_share 时如何确定 object_type / visual_kind

### 8.1 object_type 确定

由第 7 节的映射表确定。图片分享场景下 `source_type=IMAGE_SHARE`。

### 8.2 visual_kind 确定

复用 E1 已有的 `resolve_visual_kind(object_type, source_type)` 函数。该函数在 `CompanionObjectService.create()` 内部调用，自动从 `object_type` 映射到 `visual_kind`。

映射表（E1 已实现，E3 不改）：

```text
object_type         -> visual_kind
STAR                -> star
CLOUD               -> cloud
DRAWING_CHARACTER   -> dino_shadow
TOY_CHARACTER       -> block_light
BLOCK_MONSTER       -> block_light
PAPER_BOAT          -> paper_boat
STORY_GATE          -> tiny_door
WINDOW_BIRD         -> cloud
OTHER               -> star
```

### 8.3 图片分享场景的典型流转

```text
孩子拍了一幅画
  -> recognized_type = "child_drawing"
  -> object_type = DRAWING_CHARACTER
  -> visual_kind = dino_shadow
  -> Android 渲染恐龙轮廓影子

孩子拍了一个玩具
  -> recognized_type = "toy"
  -> object_type = TOY_CHARACTER
  -> visual_kind = block_light
  -> Android 渲染积木块影子
```

---

## 9. safe_summary 如何控制在 200 字以内

### 9.1 当前约束

`CompanionObjectCreateRequest.safe_summary` 已有 `max_length=200` 校验。`CompanionObjectService.create()` 中有 `strip()[:SAFE_SUMMARY_MAX_LENGTH]` 截断。

### 9.2 E3 的 safe_summary 内容

图片分享场景：

```python
safe_summary = f"{companion_name}来自图片分享"
```

示例：
- `"小棉花来自图片分享"` （9 个字）
- `"小恐龙来自图片分享"` （9 个字）

远低于 200 字限制。

### 9.3 安全校验

`_validate_safe_summary()` 会检查 `FORBIDDEN_SUMMARY_MARKERS`（地址、学校、电话、真实姓名、吵架、题目、答案、保密等）。`"{name}来自图片分享"` 不包含任何 forbidden marker。

如果孩子起的名字包含 forbidden marker（如"叫学校"），`_validate_safe_summary()` 会抛出 `ForbiddenContentError`，需要捕获并返回温和提示让孩子重新起名。

---

## 10. 如何不保存原始图片和详细图片描述

### 10.1 当前状态

- `AttachmentService.create_real_image_upload()` 会存储图片到 `backend/storage/attachments/images/{attachment_id}.{ext}` —— **这是已有行为，E3 不改**
- `RecognizedContent.text` 存储在 `AttachmentRecord` 中 —— **这是已有行为，E3 不改**

### 10.2 E3 的安全措施

1. **companion_object 不保存图片路径或详细描述**：`safe_summary` 只包含 `"{name}来自图片分享"`，不含任何图片内容
2. **回复文本不持久化到 companion_object**：小白狐的回复（"我看到圆圆的小角啦"）只存在于对话历史中，不写入 companion_object
3. **温柔想象短语为固定枚举**：不保存模型生成的任何图片分析内容

### 10.3 关于 AttachmentRecord

AttachmentRecord 中的 `recognized_content.text` 是已有机制，不在 E3 范围内修改。如果需要清理，应作为独立的隐私合规任务处理。

---

## 11. 如何避免模型自由生成未批准儿童端文案

### 11.1 核心策略

E3 中图片成功后的回复**不依赖模型自由生成**，而是使用确定性模板：

```text
我看到{child_summary}啦
像{温柔想象短语}
要不要给它起个名字？
```

- `child_summary`：来自 vision provider 的结构化输出（`RecognizedContent.text`），经过安全过滤
- 温柔想象短语：来自固定的 type->phrase 映射表

### 11.2 _image_context_repair_reply() 改造

当前该函数对不同 `recognized_type` 生成不同格式的自由文本。E3 将其改造为统一使用上述模板。

### 11.3 模型回复的处理

如果模型自身回复了符合模板的内容且不包含拒绝性文字，`_image_context_repair_reply()` 不会触发（line 976: `if reply_text and not self._looks_like_image_refusal(reply_text): return None`）。

只有当模型拒绝看图或没有 image_context 时，才用确定性模板覆盖。

### 11.4 文案来源确认

所有文案均来自：
- 模板结构：`docs/给小白狐看看2_0与小屋可见共创增强设计_2026_06_01_V0_1.md` 第 3.2 节
- 失败文案：`docs/四个核心场景话术与状态库_2026_05_30_V0_1.md` 第 3.8 节
- 按钮文案：`docs/四个核心场景话术与状态库_2026_05_30_V0_1.md` 第 7.5 节

E3 不新增任何儿童端文案。

---

## 12. 会修改哪些文件

### 后端

| 文件 | 改动内容 |
|---|---|
| `backend/app/services/modality_manager.py` | ① 图片成功回复改为确定性模板 ② quick_actions 改为只含 `companion_name` ③ confidence < 0.65 时 quick_actions 改为空 ④ 新增 `_build_image_success_reply()` 和 `_imagination_phrase()` 辅助函数 |
| `backend/app/services/child_agent_runtime.py` | ① `_image_context_repair_reply()` 统一使用确定性模板 ② 删除各 recognized_type 分支的自由生成文本 |
| `backend/app/services/conversation_service.py` | ① `_check_pending_companion_seed_creation()` 接收 image_context 参数 ② `begin_seed_naming()` 传入 `recognized_image_type` ③ create() 时根据 recognized_image_type 推导 object_type ④ safe_summary 改为图片分享模板 ⑤ 捕获 ForbiddenContentError 返回温和提示 |
| `backend/app/domain/companion_object.py` | ① `PendingCompanionSeed` 新增 `recognized_image_type` 字段 ② 新增 `resolve_object_type_from_image()` 映射函数 |

### 不修改

| 文件 | 原因 |
|---|---|
| `backend/app/api/v1/conversation_attachment.py` | 图片上传 API 不变 |
| `backend/app/services/attachment_service.py` | 附件识别逻辑不变 |
| `backend/app/services/companion_object_service.py` | create() 接口不变，调用方改传参 |
| `backend/app/services/prompt_manager.py` | prompt 注入逻辑不变 |
| `backend/app/services/quick_action_service.py` | 非附件场景的 quick action 不变 |
| `backend/app/services/parent_report_service.py` | 家长端不变 |
| `backend/app/services/parent_report_language_v4.py` | 家长端不变 |
| `backend/app/services/memory_service.py` | 记忆不变 |
| `backend/app/services/safety_engine.py` | 安全引擎不变 |
| `backend/app/services/scene_orchestrator.py` | 场景编排不变 |
| `backend/app/providers/` | provider 不变 |
| `backend/app/core/` | 核心配置不变 |
| `backend/app/db/models.py` | 数据库模型不变（E1 已加 visual_kind） |
| `backend/app/repositories/` | 仓储不变 |
| `android/` | Android 不变（E2 已完成渲染） |
| `docs/` 主控文档 | 开发方不改主控文档 |

---

## 13. 不会修改哪些文件

见第 12 节"不修改"表格。

补充说明：

```text
1. 不重写全局 prompt —— PromptManager 不动
2. 不改 Android 渲染 —— E2 已完成
3. 不改家长端边界 —— parent_report 不动
4. 不新增儿童端文案 —— 全部使用 master-copy 或主控批准的模板
5. 不改数据库 schema —— E1 已加 visual_kind
6. 不新增 API endpoint —— 复用已有附件和对话接口
```

---

## 14. 测试策略

### 14.1 后端单测

| 测试文件 | 覆盖场景 |
|---|---|
| `test_modality_manager.py`（新增或扩写） | ① 图片成功只返回 `companion_name` 一个 quick action ② confidence < 0.65 时 quick_actions 为空 ③ privacy_sensitive 时无共创入口 ④ 回复符合确定性模板结构 ⑤ 各 recognized_type 的温柔想象短语映射 |
| `test_child_agent_runtime.py`（扩写） | ① `_image_context_repair_reply()` 对各类型返回模板化回复 ② 模型正常回复时不触发修复 ③ 模型拒绝看图时触发修复 |
| `test_conversation_service.py`（扩写） | ① 图片分享 + companion_name -> begin_seed_naming 传入 recognized_type ② 孩子说名字 -> create() 使用正确的 object_type ③ create() 成功返回 co_create metadata ④ ForbiddenContentError 时返回温和提示 ⑤ 图片失败时不建立 pending |
| `test_companion_object.py`（扩写） | ① `resolve_object_type_from_image()` 映射正确 ② IMAGE_SHARE source_type 时 visual_kind 正确 |

### 14.2 运行命令

```bash
# 后端全量
bash scripts/test_backend.sh

# 后端 lint
bash scripts/lint_backend.sh

# companion 专项
bash scripts/test_backend.sh -k "companion" -q

# modality 专项
bash scripts/test_backend.sh -k "modality" -q

# Android 构建验证（确保不破坏）
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh testDebugUnitTest
```

### 14.3 禁止话术扫描

测试中需验证以下禁止表达不出现：

```text
上传成功
识别成功
图片分析结果
检测到多个物体
你画得真好
你真棒
```

---

## 15. 风险点

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| vision provider 返回的 `child_summary` 过长或包含隐私 | 回复超出预期长度或泄露隐私 | 复用已有 `_strip_image_detail_labels()` 和 `_looks_private_for_child_detail()` 过滤；截断到 20 字 |
| vision provider 返回的 `child_summary` 为空 | 回复缺少具体细节 | 使用兜底文本"一个小东西" |
| `recognized_type` 不在映射表中 | object_type 无法确定 | 兜底到 STAR |
| `_extract_pending_companion_name()` 提取失败 | 孩子说了名字但没被识别 | 已有逻辑，E3 不改；失败时返回 None，不创建 companion |
| 孩子起的名字触发 `ForbiddenContentError` | create() 抛异常 | 捕获异常，返回温和提示让孩子重新起名 |
| 图片附件在第二轮消息中丢失 | image_context 为 None | AttachmentRecord 持久化在 repository 中，通过 attachment_id 可查 |
| `begin_seed_naming()` 的 pending 在内存中 | 服务重启后丢失 | K05 已知限制，v0.1 可接受 |
| 模型回复恰好符合模板但包含禁止表达 | 绕过安全检查 | `_image_context_repair_reply()` 在模型回复后执行，`_looks_like_image_refusal()` 只检测拒绝性文字；需额外检查禁止表达 |

---

## 16. 需要主控确认的问题

### Q1：温柔想象短语映射表是否可接受？

当前映射：

```text
child_drawing      -> 像一个小世界
art_feedback       -> 像一个小世界
toy                -> 像一个小伙伴
object             -> 像一个小秘密
handmade           -> 像一个小故事
daily_life         -> 像一幅小画
cloud              -> 像一朵小云
default/空         -> 软软的
```

这些短语是否符合产品方向？是否需要调整？

### Q2：图片分享的 safe_summary 格式是否可接受？

当前：`"{name}来自图片分享"`（如"小棉花来自图片分享"）

是否需要更自然的表述？如 `"孩子给{detail}起名{name}"`？

### Q3：图片失败时的 master-copy 文案确认

当前使用（来自四个核心场景话术与状态库 3.8）：

```text
这张图还没看到
可以再试一次，也可以先不看
```

是否需要补充"再试一次"和"先不看"两个按钮？还是只返回文案不返回按钮？

### Q4：child_summary 过长时的截断策略

当前计划截断到 20 字。是否需要更短（如 10 字）或更宽松（如 30 字）？

### Q5：图片分享场景是否需要排除特定 recognized_type 进入共创？

当前计划：除 `privacy_sensitive`、`unclear`、`low_confidence`、`unsafe_unknown` 外，所有类型都可以进入"起个名字"。

`homework_problem` 类型已在 AttachmentService 中走 homework 路径，不会进入图片分享共创。是否还有其他需要排除的类型？

### Q6：E3 是否需要同时处理 E5"加一个朋友"的图片路径？

当前 E3 只处理首次图片分享 -> 起名 -> create。E5 的"加一个朋友"是第二天召回后的延续，不在 E3 范围。确认此边界是否正确。
