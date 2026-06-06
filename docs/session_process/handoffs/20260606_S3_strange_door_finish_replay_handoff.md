# S3：奇怪小门 Demo 退出与重玩收口交接

日期：2026-06-06

执行角色：开发执行会话

状态：CODE PASS / 待合并真机验收

---

## 1. 结论

S3 已按主控确认范围完成实现：

```text
1. Completed 完成态统一显示主控完成态文案。
2. Completed 完成态按钮顺序为：再玩一次 / 再找一个 / 去小展台看看 / 先聊别的。
3. ShowcaseSaved 保存完成态按钮顺序为：去小展台看看 / 再找一个 / 先聊别的。
4. “再玩一次”“再找一个”“去小展台看看”“先聊别的”均已接入 Android 本地行为。
5. 本轮未改后端、素材、S2 列表详情、R1-A / R1-B / R1-C 视觉和节奏。
```

---

## 2. 修改文件

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorDemoTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorPhotoTransformTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorShowcaseTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorStateContractTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/handoffs/20260606_S3_strange_door_finish_replay_handoff.md
```

---

## 3. 行为变化

### Completed 完成态

显示主控确认文本：

```text
开啦
你真的帮到我了

门后面有一点暖暖的风
我们先看到这里
```

按钮顺序：

```text
再玩一次
再找一个
去小展台看看
先聊别的
```

行为：

```text
1. 再玩一次：重置到 ChoosingMethod + Closed，attemptsCount 清零，清空 lastPhotoTransform / lastRiddleEvaluation / lastPhotoMessageId，不删除小展台内容。
2. 再找一个：如果 doorState 非 Open，保留当前 doorState 并进入 PhotoPrompt；如果 doorState 为 Open，重置为 Closed + PhotoPrompt。
3. 去小展台看看：复用 S2 小展台列表导航，不改变 Demo 状态。
4. 先聊别的：退出 Demo，恢复普通 opening / conversation，并设置 ViewModel 生命周期内的 dismissed 标记，避免返回 ChatScreen 后自动重新激活 Demo。
```

### ShowcaseSaved 保存完成态

保留主控确认文本：

```text
{name}，放好啦
以后可以在小展台里看到它
```

按钮顺序：

```text
去小展台看看
再找一个
先聊别的
```

行为：

```text
1. 去小展台看看：进入 S2 小展台列表，即使没有展品也进入 S2 空状态。
2. 再找一个：按当前门状态进入 PhotoPrompt；Open 时重新从 Closed 开始。
3. 先聊别的：退出 Demo 并恢复普通聊天。
```

---

## 4. 本地状态边界

```text
1. strangeDoorDemoDismissed 只存在于 ChatViewModel 生命周期内。
2. strangeDoorDemoDismissed 不写入后端。
3. strangeDoorDemoDismissed 不写入本地文件。
4. strangeDoorDemoDismissed 不进入 GrowthEvent。
5. “再玩一次”和“再找一个”都不删除、清空或迁移已保存小展台内容。
```

---

## 5. 安全与范围

本轮遵守以下限制：

```text
1. 未新增第二扇门、第二关、地图、奖励、积分、等级、任务、打卡或排行榜。
2. 未新增家长端功能。
3. 未改后端、endpoint、image_purpose 或 attachment 链路。
4. 未改素材。
5. 未改 R1-A / R1-B / R1-C 视觉和节奏。
6. 未改 S2 小展台列表详情。
7. 未提交真实儿童照片、截图、音频、转录或隐私材料。
```

---

## 6. 测试结果

```bash
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorDemoTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest' --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh testDebugUnitTest
```

结果：

```text
PASS，BUILD SUCCESSFUL。
完整 debug 单元测试已覆盖 S2 小展台列表详情与既有回归。
```

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh assembleDebug
git diff --check
```

结果：

```text
PASS，均已通过。
```

---

## 7. 覆盖项

已覆盖：

```text
1. Completed 状态显示主控完成态文案。
2. Completed 状态按钮顺序正确。
3. ShowcaseSaved 状态按钮顺序正确。
4. “再玩一次”重置到 ChoosingMethod + Closed。
5. “再玩一次”不清空小展台内容。
6. doorState 非 Open 时，“再找一个”保留门状态并进入 PhotoPrompt。
7. doorState Open 时，“再找一个”重置 Closed 并进入 PhotoPrompt。
8. “先聊别的”退出 Demo，并恢复普通 opening / conversation。
9. 退出后返回 ChatScreen 不自动重新激活奇怪小门 Demo。
10. “去小展台看看”复用 S2 小展台列表导航。
11. D3 / D4 / D5 / R1-A / R1-B / R1-C / S2 相关回归测试未破。
12. 禁止词测试继续通过。
13. assembleDebug 通过。
```

---

## 8. 风险点

```text
1. 当前无真机测试条件，四按钮在窄屏上的实际触达与布局仍需合并真机验收。
2. Completed 页面按主控确认统一收束为完成态文案，D3 / D4 的过程反馈仍在过程中保留。
3. strangeDoorDemoDismissed 是 ViewModel 生命周期内标记；App 重启后仍会按当前规则自动显示奇怪小门 Demo。
4. “去小展台看看”返回 ChatScreen 后保留当前 Demo 完成 / 保存状态；是否还需要更明确的返回焦点，需要真机体验后再判断。
```

---

## 9. 是否需要合并真机验收

需要。

建议随 Q1 / Q2 合并真机测试一起验证：

```text
1. Completed 四按钮在手机和平板上是否清晰。
2. 保存完成态“去小展台看看”是否自然。
3. 从小展台返回 ChatScreen 后是否保留当前 Demo 状态。
4. “先聊别的”后普通 opening / conversation 是否自然恢复。
5. App 重启后 Demo 重新出现是否符合当前内测预期。
```
