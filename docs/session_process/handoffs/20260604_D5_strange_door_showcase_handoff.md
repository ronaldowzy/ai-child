# D5：奇怪小门小展台承接交接

日期：2026-06-05

执行角色：开发执行会话

任务范围：承接 D3 拍照变身结果，让孩子可以把可保存的“现实物品变成的奇怪道具 / 小发现”放进现有小展台；不改后端、不新增成长系统、不改变 D3 拍照路径或 D4 怪问题路径。

---

## 1. 本轮结论

D5 已完成。

已按主控确认后的边界落地：

```text
1. 只有 D3 拍照变身结果 canSaveToShowcase=true，且当前有小展台保存能力时，才允许进入保存流程。
2. 点击“放进小展台”后先显示：
   要不要把这个小发现放进小展台？
3. 孩子确认后显示：
   给它起个名字吧
4. 起名后复用现有 SaveXiaozhantaiItemUseCase 保存。
5. 保存内容包含原图 bytes、展品名字、变身道具名和小白狐当时的小门反馈。
6. 保存完成后在 Demo 页面显示：
   {name}，放好啦
   以后可以在小展台里看到它
7. 保留现有本地 showcase_item_saved GrowthEvent。
8. 不新增 GrowthEvent 类型。
9. 不新增后端成长系统。
10. 不改后端、不改家长端、不改 M1/M2。
```

---

## 2. 修改文件

修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorForbiddenWordsTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

新增：

```text
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorShowcaseTest.kt
docs/session_process/handoffs/20260604_D5_strange_door_showcase_handoff.md
```

未修改：

```text
backend/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/data/growth/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/ui/parent/
M1 / M2 相关逻辑
```

---

## 3. 行为变化

儿童端可见变化：

```text
1. D3 拍照变身结果如果允许保存，“放进小展台”按钮可进入保存流程。
2. blocked / unsafe / homework / privacy 图片不能保存。
3. 点击“放进小展台”后先确认，不直接创建小展台 item。
4. 确认后进入起名。
5. 孩子输入名字或语音识别名字后，才调用现有小展台保存能力。
6. 保存完成后留在奇怪小门 Demo 页面，显示保存完成反馈。
```

关键边界已保持：

```text
图片上传成功 ≠ 放进小展台。
拍照变身成功 ≠ 放进小展台。
只有孩子点击“放进小展台”并完成起名，才创建小展台 item。
```

---

## 4. 保存内容

保存请求复用现有：

```text
SaveXiaozhantaiItemUseCase.saveCapturedPhoto
```

保存内容：

```text
1. photoBytes：D3 拍照 / 相册原图 bytes。
2. name：孩子输入或语音识别得到的名字；默认值为变身道具名。
3. foxQuote：由 D3 变身反馈片段组成，包含变身道具名、小白狐动作和小门反应。
4. GrowthEvent：仍由现有 SaveXiaozhantaiItemUseCase 记录 showcase_item_saved。
```

---

## 5. 安全和边界

已落实：

```text
1. 不新增百宝箱。
2. 不新增复杂列表逻辑。
3. 不新增分类、图鉴、背包。
4. 不新增奖励、积分、等级、通关表达。
5. blocked / unsafe / homework / privacy 图片不能保存。
6. 不保存额外敏感图片信息。
7. 不改后端。
8. 不改家长端。
9. 不改 M1/M2。
10. 不新增儿童端文案，新增展示文本均来自 D5 主控确认文本。
```

---

## 6. 测试结果

已通过：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorDemoTest' --tests 'com.childai.companion.ui.chat.ChildCompanionPageRulesTest' --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh assembleDebug
```

覆盖：

```text
1. canSaveToShowcase=false 不允许保存。
2. 点击“放进小展台”进入确认状态。
3. 确认后进入起名状态。
4. 起名后调用现有小展台保存用例。
5. 保存内容包含变身道具名和小白狐反馈。
6. blocked 图片不能保存。
7. 保存成功后出现主控确认反馈。
8. D3 拍照路径继续通过。
9. D4 怪问题路径继续通过。
10. 禁止词测试继续通过。
```

---

## 7. 截图 / 录屏

本轮未产出截图或录屏。

原因：

```text
当前 doctor_local_env 显示 adb devices WARN：没有连接真机。
```

---

## 8. 风险点

```text
1. 尚未做真机保存流程 QA。
2. 当前小展台 item 仍沿用现有字段：photoUri / name / foxQuote；没有新增数据模型字段保存“变身道具名”，而是把变身道具名放入默认展品名和 foxQuote。
3. D5 保存成功后留在 Demo 页面，不自动跳转小展台，避免新增未确认按钮文案。
4. 真机上起名输入体验仍需 Q1 验证。
```

---

## 9. 是否可进入 Q1

结论：

```text
可以进入 Q1：真机试玩验收。
```

Q1 建议重点验证：

```text
1. 拍照变身后“放进小展台”是否清楚但不抢主玩法。
2. 确认和起名弹窗是否适合横屏 / 平板。
3. 保存完成反馈是否自然。
4. blocked 图片是否不能保存。
5. 保存完成后小展台列表能看到对应图片和名字。
```
