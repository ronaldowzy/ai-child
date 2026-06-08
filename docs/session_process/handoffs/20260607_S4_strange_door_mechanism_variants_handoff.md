# S4：奇怪小门三种小机关交接

日期：2026-06-08

执行角色：开发执行会话

状态：CODE PASS / 待合并真机验收

---

## 1. 本轮结论

S4 已按主控确认范围完成 Android 本地实现：

```text
1. 新增 Round / Soft / Shiny 三种 mechanismType。
2. reset / App 重启默认从 Round 开始。
3. “再玩一次”按 Round -> Soft -> Shiny -> Round 轮换。
4. “再找一个”不轮换机关；Open 后保留当前机关并重置 Closed + PhotoPrompt。
5. 首屏气泡、PhotoPrompt 和拍照 mapper 已按当前机关切换。
```

本轮未改后端、endpoint、image_purpose、素材、小展台列表详情、怪问题路径或小展台保存路径。

---

## 2. 修改文件

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapper.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorDemoTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorPhotoTransformTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapperTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorStateContractTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/handoffs/20260607_S4_strange_door_mechanism_variants_handoff.md
```

未修改：

```text
backend/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/data/growth/
android/app/src/main/java/com/childai/companion/ui/showcase/
android/app/src/main/java/com/childai/companion/ui/parent/
android/app/src/main/res/drawable-nodpi/
docs/assets/strange_door/
```

---

## 3. 行为变化

### 3.1 本地状态

新增：

```text
StrangeDoorMechanismType.Round
StrangeDoorMechanismType.Soft
StrangeDoorMechanismType.Shiny
```

`StrangeDoorDemoSnapshot` 新增 `mechanismType`，默认 `Round`。

### 3.2 重玩与再找一个

```text
1. reset / App 重启：ChoosingMethod + Closed + Round。
2. 再玩一次：重置门状态和过程数据，并轮换到下一个 mechanismType。
3. 再找一个：doorState 非 Open 时，保留当前 doorState 和 mechanismType 进入 PhotoPrompt。
4. 再找一个：doorState 为 Open 时，保留当前 mechanismType，重置为 Closed + PhotoPrompt。
```

小展台已保存内容不删除、不清空。

### 3.3 首屏与拍照提示

首屏气泡已按三种机关切换：

```text
找一个圆圆的东西
找一个软软的东西
找一个亮亮的东西
```

PhotoPrompt 已按三种机关切换，使用主控确认文本，不新增儿童端文案。

### 3.4 拍照 mapper

`StrangeDoorPhotoTransformMapper.map()` 已支持传入当前 `mechanismType`：

```text
1. Round 命中圆形词池。
2. Soft 命中 soft 精确词和允许泛化词。
3. Shiny 命中 shiny 精确词和允许泛化词。
4. 安全但不符合当前机关的内容仍 AdvanceOneStep。
5. blocked / privacy / homework 仍 None，且不可保存。
```

Soft / Shiny 道具名只使用主控确认词池，并纳入禁止词测试。

---

## 4. 测试结果

已运行：

```bash
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorDemoTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest'
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh testDebugUnitTest
bash scripts/android_gradle.sh assembleDebug
```

结果：

```text
PASS，均为 BUILD SUCCESSFUL。
```

`doctor_local_env.sh` 结果：

```text
JDK OK
Android SDK OK
adb OK
adb devices WARN：no connected physical Android device
```

说明：当前代码侧和构建验收通过；本轮未完成真机体验验收。

---

## 5. 覆盖项

已覆盖：

```text
1. reset 默认 Round。
2. replay 从 Round 到 Soft。
3. replay 从 Soft 到 Shiny。
4. replay 从 Shiny 到 Round。
5. replay 清空门状态和过程数据。
6. 首屏气泡按三种机关显示。
7. PhotoPrompt 按三种机关显示。
8. mapper 在 Round 下命中圆形词池。
9. mapper 在 Soft 下命中 soft 精确词和泛化词。
10. mapper 在 Shiny 下命中 shiny 精确词和泛化词。
11. 安全但不匹配当前机关仍 AdvanceOneStep。
12. blocked / privacy / homework 仍 None 且不可保存。
13. 怪问题答对仍直接 Open。
14. “再找一个”不轮换机关。
15. Open 后“再找一个”保留当前机关并重置 Closed + PhotoPrompt。
16. soft / shiny 词池进入 approvedChildFacingCopy 并通过禁止词测试。
17. D3 / D4 / D5 / R1-A / R1-B / R1-C / S2 / S3 相关回归未破。
18. assembleDebug 通过。
```

---

## 6. 安全与范围

本轮保持：

```text
1. 不新增第二扇门、第二关、地图、任务、奖励、积分、等级、连续打卡或排行榜。
2. 不改后端。
3. 不新增 endpoint。
4. 不新增 image_purpose。
5. 不新增素材。
6. 不改小展台列表详情。
7. 不改怪问题路径。
8. 不改小展台保存路径。
9. 不提交真实儿童测试材料。
10. 不保存额外敏感图片信息。
```

---

## 7. 风险点

```text
1. 本轮未做真机体验验收，三种机关在儿童实际重玩时是否足够明显，需要合并真机测试确认。
2. soft / shiny 依赖 recognizedContent 文本，识别结果过于笼统时仍可能进入 unknown 温柔推进。
3. 安全但不匹配当前机关仍推进门，体验更低挫败，但机关因果感需真机试玩观察。
4. 三种机关共用同一套小门素材，差异主要来自文本要求和道具名，不来自门外观。
```

---

## 8. 是否需要合并真机验收

需要。

建议随 D1-D5 + R1-A/R1-B/R1-C + S2 + S3 合并真机测试一起验证：

```text
1. “再玩一次”后小门要求是否真的变化。
2. 孩子是否能理解这次要找软软 / 亮亮的东西。
3. 拍错但安全时是否仍像被温柔接住。
4. 玩法是否没有变成任务、关卡或奖励。
5. 小展台是否仍只是承接，不抢主玩法。
```
