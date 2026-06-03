# M2 小屋小物件真机验收辅助与调试入口计划

状态：PLAN

更新时间：2026-06-03

---

## Summary

M2 只做内部调试和真机验收辅助能力，不进入正式儿童体验，不新增儿童端正式玩法。目标是让主控和监理在 Honor Pad 5 / Redmi K60 上快速查看 6 种小屋小物件素材、4 种状态和 4 个位置的实际效果，并能快速准备或清理当前 child 的测试小客人数据。

本计划不继续用代码手调 Canvas 形状、alpha、path 来设计小物件。M1 已接入的正式素材是主路径，当前 Canvas 只保留为资源加载失败 fallback。

---

## 1. 当前是否已有 debug/dev 设置入口

当前 Android 已有基础开发配置：

```text
android/app/src/main/java/com/childai/companion/config/DevSettings.kt
```

已有相关开关：

```text
SHOW_SESSION_STATE_DEBUG = false
SHOW_MASCOT_DEBUG_SWITCHER = false
SHOW_TTS_DIAGNOSTICS = true
```

当前儿童主界面附近也已有小白狐状态调试开关路径：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
```

但目前没有“小屋小物件 visual_kind / state / location”专用调试入口，也没有一键创建或重置小客人的调试能力。

---

## 2. 如何只在 debug build 或开发配置下启用

Android 侧建议双重限制：

```text
BuildConfig.DEBUG == true
DevSettings.SHOW_HOUSE_OBJECT_DEBUG_TOOLS == true
```

即使是 debug 包，也需要显式开发开关打开；release build 中不显示入口，不触发任何 debug 请求。

后端侧如新增 debug API，建议双重限制：

```text
settings.environment != "prod"
settings.enable_debug_tools == true
```

生产环境即使误调用也应返回不可用，不允许执行创建、重置或覆盖 child 数据。

---

## 3. 如何选择 visual_kind

调试入口固定提供 6 个选项：

```text
star
cloud
paper_boat
tiny_door
dino_shadow
block_light
```

Android 侧展示可以使用简短中文标签，但内部值必须保持正式 `visual_kind`：

```text
小星星 -> star
小云朵 -> cloud
小纸船 -> paper_boat
小门 -> tiny_door
小恐龙影子 -> dino_shadow
小积木光点 -> block_light
```

调试入口选择后，直接刷新本地预览用的 `CompanionObjectMeta.visualKind`，或通过 debug API 创建真实测试小客人。

---

## 4. 如何选择状态

调试入口固定提供 4 个状态：

```text
seed
co_create
recall
none
```

映射规则：

```text
seed      -> state=seed, action=name_seed
co_create -> state=active, action=co_create
recall    -> state=active, action=recall
none      -> state=active, action=none 或清空本地预览对象
```

`none` 只用于验证“不显示小物件”的边界，不应落库为真实 active 小客人状态。

---

## 5. 如何选择位置

调试入口固定提供 4 个位置：

```text
窗边
地毯边
小白狐旁边
窗外
```

内部直接写入：

```text
light_location
```

并复用现有 `toCompanionLocation()` 和 `placementForViewport()` 逻辑，避免调试入口另起一套坐标系统。

---

## 6. 如何快速创建测试小客人

建议提供两个模式：

```text
1. 仅本地预览
2. 真实落库创建
```

仅本地预览：

```text
Android 构造临时 CompanionObjectMeta，只影响当前 UI。
不写数据库。
不影响 opening / recall / 家长端摘要。
用于快速看素材、状态、位置。
```

真实落库创建：

```text
Android 调用后端 debug API。
后端为当前 child 创建或覆盖一个测试小客人。
用于验证重启后 recall、持久化和真实 session_state。
```

测试小客人建议使用固定安全名称：

```text
测试小星星
```

或根据 visual_kind 生成：

```text
测试小云朵 / 测试小纸船 / 测试小门
```

这些名称只用于 debug 数据，不进入正式儿童引导文案设计。

---

## 7. 如何重置当前 child 的小客人数据

建议后端 debug API 提供：

```text
POST /api/v1/debug/companion-object/reset
```

作用范围：

```text
仅当前认证 token 对应 child_id
```

重置策略建议：

```text
优先 retired，不做物理删除
```

原因：

```text
1. 避免误删历史数据。
2. 更符合当前 companion_objects 已有 retired 语义。
3. 后续仍可排查测试数据轨迹。
```

如果主控明确要求“测试环境物理删除”，可以只在本地 dev 环境增加硬删除参数，但默认不开放。

---

## 8. 是否需要后端 debug API

建议需要。

仅 Android 本地构造能解决：

```text
1. 6 种素材看起来是否正确。
2. 4 个位置是否合理。
3. co_create / recall 的视觉强弱是否合适。
```

但无法验证：

```text
1. companion_objects 是否真实落库。
2. 后端重启后是否仍可 recall。
3. opening response 是否能带回 session_state.companion_object。
4. 家长端轻共创摘要是否能基于真实数据出现。
```

因此 M2 最低可以先做 Android 本地预览；完整 M2 建议同时做后端 debug API。

---

## 9. 是否只在本地/开发环境开放

是。

后端 debug API 必须满足：

```text
1. 默认关闭。
2. prod 环境不可用。
3. 需要显式 CHILD_AI_ENABLE_DEBUG_TOOLS=true。
4. 只允许操作当前 child_id。
```

Android debug 入口必须满足：

```text
1. release build 不显示。
2. DevSettings 开关关闭时不显示。
3. 不作为儿童正式入口。
4. 不写入正式功能导航。
```

---

## 10. Android 会修改哪些文件

预计修改：

```text
android/app/src/main/java/com/childai/companion/config/DevSettings.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
```

预计新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/HouseObjectDebugPanel.kt
android/app/src/main/java/com/childai/companion/data/debug/CompanionObjectDebugDtos.kt
android/app/src/main/java/com/childai/companion/data/debug/CompanionObjectDebugRepository.kt
```

预计测试：

```text
android/app/src/test/java/com/childai/companion/ui/chat/HouseObjectDebugPanelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelHouseObjectDebugTest.kt
```

如果主控选择先做“仅本地预览”，可以不新增 `data/debug` 网络层。

---

## 11. 后端会修改哪些文件

如果主控确认需要后端 debug API，预计修改：

```text
backend/app/core/config.py
backend/app/main.py
backend/app/services/companion_object_service.py
```

预计新增：

```text
backend/app/api/v1/debug_companion_object.py
backend/app/tests/test_debug_companion_object_api.py
```

如果只做 Android 本地预览，后端本轮不修改。

---

## 12. 不会修改哪些文件

不改：

```text
backend/app/prompts/
backend/app/services/parent_report_service.py
backend/app/services/child_agent_runtime.py
backend/app/services/prompt_manager.py
backend/app/services/modality_manager.py
android/app/src/main/assets/mascot/xiaobaohu/v2/
android/app/src/main/java/com/childai/companion/ui/parent/
```

不改业务主链路：

```text
opening 正式逻辑
conversation 正式逻辑
图片上传正式逻辑
家长端正式展示
小白狐 10 状态资源
```

---

## 13. 安全边界

必须遵守：

```text
1. 不新增儿童端正式文案。
2. 不新增正式玩法。
3. 不新增任务、奖励、收藏、图鉴。
4. 不改家长端边界。
5. 不改 prompt。
6. 不影响 release build。
7. debug 能力不得暴露给真实儿童用户。
8. 不保存额外儿童照片、音频或长文本。
9. reset 只作用当前 child，不跨 child。
10. prod 环境 debug API 默认不可用。
```

---

## 14. 测试策略

Android 自动化：

```text
1. debug 开关关闭时入口不可见。
2. release 或 BuildConfig.DEBUG=false 时入口不可见。
3. 6 种 visual_kind 都能生成预览 CompanionObjectMeta。
4. 4 种状态映射正确。
5. 4 个位置映射正确。
6. none 状态不显示小物件。
```

后端自动化：

```text
1. enable_debug_tools=false 时 debug API 返回不可用。
2. environment=prod 时 debug API 返回不可用。
3. dev + enable_debug_tools=true 时可创建测试小客人。
4. reset 只 retired 当前 child 的小客人。
5. 创建后 opening / recall 可读取真实 active 记录。
```

构建验证：

```text
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh testDebugUnitTest --tests <M2 相关测试>
conda run -n child-ai pytest backend/app/tests/test_debug_companion_object_api.py -q
```

真机验证：

```text
Honor Pad 5：6 种素材 x 重点状态截图
Redmi K60：6 种素材 x 重点状态截图
横竖屏：至少验证窗边 / 地毯边 / 小白狐旁边
```

---

## 15. 需要主控确认的问题

1. M2 是否允许新增后端 debug API？
2. Android 调试入口放在儿童页临时开发按钮，还是放到家长入口后的开发区？
3. M2 是否需要同时支持“仅本地预览”和“真实落库创建”两个模式？
4. 重置当前 child 小客人数据时，主控希望默认 retired 还是物理删除？
5. debug API 是否需要额外本地 header，例如 `X-Child-AI-Debug-Token`？
6. `none` 状态是否只做本地预览，不提供真实落库？
7. 真机截图验收是否只要求 6 种素材在 `co_create + 窗边` 可见，还是要覆盖 6 x 4 x 4 全组合？

---

## Recommended First Cut

建议第一版 M2 先做：

```text
1. Android 本地预览面板。
2. visual_kind / state / location 三组选择。
3. 一键清空本地预览。
4. 不接后端 debug API。
```

原因：

```text
1. 能最快解决 M1 真机视觉验收效率。
2. 不碰真实数据，风险最低。
3. 后续确认需要持久化 / recall 辅助后，再加后端 debug API。
```

如果主控要求验证真实 recall 和落库，则第二步再补：

```text
后端 debug API + Android 调用入口
```

