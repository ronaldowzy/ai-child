# M2 小屋小物件真机验收辅助与调试入口交接

状态：CODE PASS，真机回归待设备可用后执行

更新时间：2026-06-03

提交号：以本轮回传为准

---

## Summary

本轮完成 M2 内部调试能力，不进入正式儿童体验。Android 在家长入口长按后的弹窗里增加“开发调试”入口，只在 `BuildConfig.DEBUG && DevSettings.SHOW_HOUSE_OBJECT_DEBUG_TOOLS` 成立时显示；release build 不显示。后端新增受保护 debug API，默认关闭，需要非生产环境、`CHILD_AI_ENABLE_DEBUG_TOOLS=true`、`X-Child-AI-Debug-Token` 与 `CHILD_AI_DEBUG_TOOLS_TOKEN` 匹配，并且当前 child 认证有效。

---

## What Changed

1. Android 增加小屋小物件调试面板。
2. Android 支持 6 种 `visual_kind`、4 种状态、4 个位置的本地预览。
3. Android 支持通过 debug API 真实落库创建当前 child 的测试小客人。
4. Android 支持通过 debug API 将当前 child 的小客人数据默认置为 `retired`。
5. 后端新增 debug API 并加三层门禁，不影响正式 opening / conversation / parent report。

---

## Android

入口位置：

```text
家长入口长按 -> 家长入口选择弹窗 -> 开发调试
```

显示条件：

```text
BuildConfig.DEBUG == true
DevSettings.SHOW_HOUSE_OBJECT_DEBUG_TOOLS == true
```

支持素材：

```text
star
cloud
paper_boat
tiny_door
dino_shadow
block_light
```

支持状态：

```text
seed      -> state=seed, action=name_seed
co_create -> state=active, action=co_create
recall    -> state=active, action=recall
none      -> 本地预览清空，不创建真实数据
```

支持位置：

```text
窗边
地毯边
小白狐旁边
窗外
```

本地预览：

```text
Android 构造临时 CompanionObjectMeta。
只覆盖当前 XiaobaohuCompanionStage 的 companionObject 入参。
不写入 uiState.sessionState。
不影响 opening / recall / 家长端。
```

真实落库：

```text
POST /api/v1/debug/house-object/create
```

重置当前 child：

```text
POST /api/v1/debug/house-object/reset
```

Android debug token 来源：

```text
BuildConfig.DEBUG_TOOLS_TOKEN
Gradle property: debugToolsToken
环境变量兜底: CHILD_AI_DEBUG_TOOLS_TOKEN
默认值: local-dev-debug
```

---

## Backend

新增配置：

```text
CHILD_AI_ENABLE_DEBUG_TOOLS=false
CHILD_AI_DEBUG_TOOLS_TOKEN=
```

debug API 门禁：

```text
1. settings.environment 不能是 prod / production / release
2. CHILD_AI_ENABLE_DEBUG_TOOLS 必须为 true
3. X-Child-AI-Debug-Token 必须匹配 CHILD_AI_DEBUG_TOOLS_TOKEN
4. Authorization Bearer token 必须是有效当前 child 认证
```

创建接口：

```text
POST /api/v1/debug/house-object/create
```

请求只允许：

```text
visual_kind: star / cloud / paper_boat / tiny_door / dino_shadow / block_light
state: seed / co_create / recall
light_location: 窗边 / 地毯边 / 小白狐旁边 / 窗外
```

`none` 状态不允许真实落库，后端会拒绝，Android 真实创建按钮也会禁用。

重置接口：

```text
POST /api/v1/debug/house-object/reset
```

重置行为：

```text
只操作当前认证 child_id。
只将当前 child 的小客人置为 retired。
不做物理删除。
不跨 child。
```

---

## Safety

1. 未新增儿童端正式文案。
2. 未新增正式玩法、任务、奖励、收藏、图鉴。
3. 未修改 prompt。
4. 未修改家长端正式边界。
5. 未修改家长日报逻辑。
6. debug API 默认关闭，生产环境不可用。
7. debug API 不保存额外儿童照片、音频或长文本。
8. debug API 不接受 body 中的 child_id，始终使用当前认证 child。
9. `none` 只做本地 UI 边界预览，不允许真实落库。

---

## Files Changed

Android：

```text
android/app/build.gradle.kts
android/app/src/main/java/com/childai/companion/config/DevSettings.kt
android/app/src/main/java/com/childai/companion/data/debug/HouseObjectDebugApiClient.kt
android/app/src/main/java/com/childai/companion/data/debug/HouseObjectDebugRepository.kt
android/app/src/main/java/com/childai/companion/ui/AppNavHost.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/HouseObjectDebugDialog.kt
android/app/src/main/java/com/childai/companion/ui/chat/HouseObjectDebugModels.kt
android/app/src/test/java/com/childai/companion/ui/chat/HouseObjectDebugModelsTest.kt
```

Backend：

```text
backend/app/api/v1/debug_house_object.py
backend/app/core/config.py
backend/app/main.py
backend/app/services/companion_object_service.py
backend/app/tests/test_debug_house_object_api.py
```

---

## Tests

已运行：

```bash
bash scripts/doctor_local_env.sh
bash scripts/test_backend.sh app/tests/test_debug_house_object_api.py
bash scripts/test_backend.sh app/tests/test_debug_house_object_api.py app/tests/test_companion_object_service.py app/tests/test_companion_object_runtime.py
bash scripts/android_gradle.sh testDebugUnitTest --tests com.childai.companion.ui.chat.HouseObjectDebugModelsTest
bash scripts/android_gradle.sh testDebugUnitTest --tests com.childai.companion.ui.chat.CompanionObjectVisualTest --tests com.childai.companion.ui.chat.ParentEntryDeemphasisTest --tests com.childai.companion.ui.chat.HouseObjectDebugModelsTest
bash scripts/android_gradle.sh assembleDebug
```

结果：

```text
doctor: PASS；提示当前未连接物理 Android 设备；db migration OK，companion_objects.visual_kind present
backend debug API: 7 passed
backend companion 相关回归: 70 passed
Android debug 映射测试: PASS
Android companion / parent entry / debug 映射相关测试: PASS
assembleDebug: PASS
```

---

## True Device

本轮未做真机截图或录屏。

原因：

```text
bash scripts/doctor_local_env.sh 显示 adb devices: WARN no connected physical Android device
```

后续 M2 真机建议按主控确认的重点组合执行：

```text
A. 6 种素材 × co_create × 窗边
B. star × co_create × 窗边 / 地毯边 / 小白狐旁边
C. star × seed / co_create / recall × 窗边
D. star × none × 窗边
E. Redmi K60 和 Honor Pad 5 都至少覆盖 6 种素材 co_create 窗边，以及 star 的 seed/co_create/recall/none
```

---

## Known Issues

1. 本轮未连接真机，未产出 Honor Pad 5 / Redmi K60 截图。
2. 使用真实落库前，后端必须显式配置 `CHILD_AI_ENABLE_DEBUG_TOOLS=true` 和 `CHILD_AI_DEBUG_TOOLS_TOKEN`，Android 构建侧的 `debugToolsToken` 或环境变量也必须匹配。
3. 当前调试入口位于家长入口长按后的弹窗内，仍需真机确认入口可达性和面板布局。

