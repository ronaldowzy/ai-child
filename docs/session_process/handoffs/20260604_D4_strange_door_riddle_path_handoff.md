# D4：奇怪小门怪问题路径交接

日期：2026-06-05

执行角色：开发执行会话

任务范围：接通“动脑试试 -> 怪问题 -> 孩子语音回答 -> 本地判断 -> 小门反馈 -> 门状态变化”；不改后端、不接小展台保存、不新增题库、不改 D3 拍照路径。

---

## 1. 本轮结论

D4 已完成。

已按主控确认后的边界落地：

```text
1. “动脑试试”继续展示固定怪问题：什么东西越洗越脏？
2. RiddlePrompt 状态下，ASR transcript 被 Android 本地消费，不发送普通 conversation。
3. transcript 交给 StrangeDoorRiddleEvaluator，本地判断是否包含“水”。
4. 答对后展示主控确认反馈，并把门状态推进为 open。
5. 答错后展示主控确认提示，并保持门状态不直接 open。
6. 答错后只提供“再答一次”“找东西帮忙”两个本地按钮。
7. DevSettings / 调试文本入口如触发 sendText，也会在 RiddlePrompt 本地消费，不调用后端 conversation。
8. 未新增题库、第二题、第三题、奖励、积分、等级、通关表达。
```

---

## 2. 修改文件

修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorRiddleEvaluator.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorForbiddenWordsTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorRiddleEvaluatorTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

新增：

```text
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorRiddlePathTest.kt
docs/session_process/handoffs/20260604_D4_strange_door_riddle_path_handoff.md
```

未修改：

```text
backend/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/ui/parent/
M1 / M2 相关逻辑
```

---

## 3. 行为变化

儿童端可见变化：

```text
1. 点击“动脑试试”后，怪问题面板显示固定题目。
2. 怪问题等待回答时显示轻量语音图形控件，复用现有录音链路。
3. 孩子语音回答包含“水”时，门直接变为 open，并显示：

对，是水

小门被你说得愣住了
它低头想了三秒
然后咔哒一下打开了

4. 孩子回答不包含“水”时，门不打开，并显示：

这个答案有点勇敢
小门差点相信了

我给你一个提示
它常常在杯子里、河里、盆里

5. 答错后“再答一次”回到 RiddlePrompt。
6. 答错后“找东西帮忙”切回 PhotoPrompt。
```

---

## 4. 安全和边界

已落实：

```text
1. 怪问题路径不调用后端 conversation。
2. 不改后端。
3. 不新增 endpoint。
4. 不新增题库、第二题或第三题。
5. 不新增学习练习感。
6. 不新增奖励、积分、等级、地图、签到或通关表达。
7. 不接小展台保存。
8. 不改 D3 attachment / image_purpose=share 拍照路径。
9. 不改 M1/M2。
10. 禁止词测试继续覆盖“错了”“正确答案是”“这个很简单”等考试感表达。
```

---

## 5. 测试结果

已通过：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorDemoTest' --tests 'com.childai.companion.ui.chat.ChildCompanionPageRulesTest' --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh assembleDebug
```

覆盖：

```text
1. RiddlePrompt 状态下 ASR transcript 不发送 conversation。
2. 包含“水”判定答对。
3. 非水答案进入提示。
4. 答对后 doorState=open。
5. 答错后 doorState 不直接 open。
6. “再答一次”回到 RiddlePrompt。
7. “找东西帮忙”切回 PhotoPrompt。
8. 禁止词测试继续通过。
9. D3 拍照路径相关测试继续通过。
10. Android debug 构建通过。
```

---

## 6. 截图 / 录屏

本轮未产出截图或录屏。

原因：

```text
当前 doctor_local_env 显示 adb devices WARN：没有连接真机。
```

---

## 7. 风险点

```text
1. 尚未做真机语音回答路径 QA。
2. 轻量语音控件不新增可见文案；图形按钮在真机上是否足够清楚需要 Q1 验证。
3. 当前按 D4 要求只做包含“水”的本地判断，故“水杯”等包含“水”的回答也会判定答对。
4. D4 完成后仍未接小展台真实保存，D5 需要承接 D3 的保存意图。
```

---

## 8. 是否可进入 D5

结论：

```text
可以进入 D5：小展台承接。
```

D5 建议只做：

```text
1. 承接 D3 拍照变身结果。
2. 复用现有小展台保存能力。
3. 保留现有本地 showcase_item_saved GrowthEvent。
4. 不新增成长系统、不新增 GrowthEvent 类型。
5. 不改变 D4 怪问题路径。
```
