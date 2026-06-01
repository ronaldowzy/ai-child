# E3 交接：拍图后细节承接与图片共创创建链路

状态：DONE

更新时间：2026-06-01

---

## Summary

E3 已完成。图片成功后使用确定性模板回复（`我看到{细节}啦 + 像{温柔想象} + 要不要给它起个名字？`），不依赖模型自由生成。只返回一个 quick action（`companion_name: 起个名字`）。图片失败使用 master-copy 失败文案，不进入共创。起名时 object_type 从 recognized_type 推导，safe_summary 使用 `"孩子给图片里的小东西起名为{name}"`。

---

## Files

### 修改

```text
backend/app/domain/companion_object.py
  - 新增 _RECOGNIZED_TYPE_TO_OBJECT_TYPE 映射表
  - 新增 IMAGE_COCREATION_ALLOWED_TYPES allowlist（8 种类型）
  - 新增 resolve_object_type_from_image() 函数

backend/app/services/companion_object_service.py
  - PendingCompanionSeed 新增 recognized_image_type 字段
  - begin_seed_naming() 新增 recognized_image_type 参数

backend/app/services/attachment_service.py
  - 新增 get_latest_image_recognized_type() 方法

backend/app/services/modality_manager.py
  - 图片成功：确定性模板回复，只返回 companion_name 一个 quick action
  - 图片失败（低置信度/不在 allowlist）：master-copy 失败文案 + "再试一次" + "先不看"
  - 新增 _safe_child_detail() 方法（截断到 20 字，隐私过滤）
  - 新增 _IMAGINATION_PHRASES 映射和 _imagination_phrase() 函数

backend/app/services/child_agent_runtime.py
  - _image_context_repair_reply() 统一使用确定性模板
  - 新增 _safe_detail_for_repair() 静态方法
  - unclear/low_confidence/unsafe_unknown 类型走失败模板
  - 不在 allowlist 中的类型走失败模板

backend/app/services/conversation_service.py
  - 导入 resolve_object_type_from_image
  - _check_pending_companion_seed_creation() 新增 image_context 参数
  - 调用位置从 handle_message 开头移到 image_context 加载之后
  - companion_name 快速动作：从 attachment service 查询最近图片的 recognized_type
  - create() 时使用 resolve_object_type_from_image() 推导 object_type
  - safe_summary：图片分享用 "孩子给图片里的小东西起名为{name}"，opening seed 保持原模板
```

### 不修改

```text
backend/app/api/v1/conversation_attachment.py
backend/app/providers/
backend/app/core/
backend/app/db/models.py
backend/app/repositories/
backend/app/services/safety_engine.py
backend/app/services/scene_orchestrator.py
backend/app/services/parent_report_service.py
backend/app/services/parent_report_language_v4.py
backend/app/services/memory_service.py
backend/app/services/prompt_manager.py
backend/app/services/quick_action_service.py
android/
```

---

## 核心变更

### 1. 图片成功回复模板

```text
我看到{child_summary}啦
像{温柔想象短语}
要不要给它起个名字？
```

- `child_summary`：来自 vision provider，经隐私过滤，截断到 20 字，为空时兜底"一个小东西"
- 温柔想象短语：按 recognized_type 确定性映射

### 2. 温柔想象短语映射表

| recognized_type | 温柔想象 |
|---|---|
| child_drawing | 像一个小世界 |
| art_feedback | 像一个小世界 |
| toy | 像一个小伙伴 |
| handmade | 像一个小故事 |
| object | 像一个小发现 |
| daily_life | 像一幅小画 |
| cloud | 像一朵小云 |
| image_observation / 默认 | 软软的 |

### 3. 图片共创 allowlist

允许：child_drawing, art_feedback, toy, object, handmade, daily_life, cloud, image_observation

禁止（走失败模板）：privacy_sensitive, unclear, low_confidence, unsafe_unknown, 以及所有不在 allowlist 中的类型

### 4. quick actions

| 场景 | quick_actions |
|---|---|
| 图片成功 | `[companion_name: 起个名字]` |
| 图片失败（低置信度/不在 allowlist） | `[retake_photo: 再试一次, skip_photo: 先不看]` |
| 隐私敏感 | `[understand_privacy: 我知道了, ask_parent: 问家长]`（不变） |

### 5. object_type 映射

| recognized_type | object_type | visual_kind |
|---|---|---|
| child_drawing / art_feedback | DRAWING_CHARACTER | dino_shadow |
| toy / handmade | TOY_CHARACTER | block_light |
| object | OTHER | star |
| daily_life / cloud | CLOUD | cloud |
| image_observation / 默认 | STAR | star |

### 6. safe_summary

- 图片分享：`"孩子给图片里的小东西起名为{name}"`
- Opening seed：保持原模板 `"这颗星星叫{name}"`

---

## Tests

```text
后端全量：851 passed, 0 failed
后端 companion 专项：82 passed
后端 modality/image 专项：74 passed
后端 lint：41 errors（均为修改前已有，本次修改文件无 lint 错误）
Android assembleDebug：BUILD SUCCESSFUL
```

---

## Safety

```text
1. 不保存原始图片到 companion_object — 已遵守
2. 不保存详细图片描述到 companion_object — 已遵守
3. safe_summary 不含图片细节 — 已遵守
4. 不新增儿童端文案 — 已遵守（全部使用 master-copy 或主控批准的模板）
5. 不重写 prompt — 已遵守
6. 不改 Android 渲染 — 已遵守
7. 不改家长端边界 — 已遵守
8. "秘密"一词未出现在温柔想象短语中 — 已遵守
9. 隐私/人脸/学校等类型不进入共创 — 已遵守
10. 作业/文档类型不进入共创 — 已遵守
```

---

## Docs

```text
docs/session_process/handoffs/20260601_E3_image_detail_cocreation_plan.md（计划）
docs/session_process/handoffs/20260601_E3_image_detail_cocreation_handoff.md（本文）
```

---

## Product boundary

```text
1. E3 只处理"首次图片分享 -> 起名 -> create companion_object"
2. E5 "加一个朋友"的图片路径不在 E3 范围
3. 图片失败不进入共创，不创建 companion_object
4. 只返回一个 quick action（companion_name），不同时给"起个名字"和"编个小故事"
5. visual_kind 由 E1 的 resolve_visual_kind() 自动推导
6. Android 渲染由 E2 完成，E3 不改
```

---

## Known issues

```text
1. image_observation 是 vision provider 的默认 recognized_type，已加入 allowlist。
   如果未来需要更细粒度的类型区分，需修改 vision provider 的 prompt。
2. PendingCompanionSeed 仍在内存中（K05 已知限制），服务重启后丢失。
3. 真机验证未完成（需连接 Redmi K60 / Honor Pad 5）。
```

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是
