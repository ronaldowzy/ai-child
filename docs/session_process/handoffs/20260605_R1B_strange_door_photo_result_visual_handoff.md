# R1-B：奇怪小门拍照结果视觉增强交接

日期：2026-06-05

执行角色：开发执行会话

任务范围：增强拍照结果页的视觉表达，让孩子更明确感到“我拍的东西 -> 变成了奇怪道具 -> 小门真的动了一下”；本轮只做视觉呈现增强，不新增新功能。

---

## 1. 本轮结论

R1-B 已完成。

已按主控确认后的边界落地：

```text
1. 拍照结果页保留孩子刚拍图片的缩略图。
2. 缩略图只作为结果页确认，不做相册或展台。
3. 可用拍照结果页把缩略图并入“变身道具卡”区域。
4. 变身道具卡继续使用 strange_door_tool_card_panel.webp。
5. 门状态变化时继续按 doorState 切换 closed / cracked / almost_open / open 对应素材。
6. 可用拍照结果推进后，门区域轻叠加 strange_door_success_glow.webp。
7. 门状态变化时加入轻微缩放 / 轻微晃动，不使用奖励、通关或领奖感动效。
8. 拍照结果按钮顺序保持：再找一个 / 动脑试试 / 放进小展台。
```

---

## 2. 修改文件

修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChildCompanionPageRulesTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
```

新增：

```text
docs/session_process/handoffs/20260605_R1B_strange_door_photo_result_visual_handoff.md
```

未修改：

```text
backend/
android/app/src/main/res/drawable-nodpi/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/ui/parent/
StrangeDoorPhotoTransformMapper 词池
StrangeDoorDoorStateReducer 门状态节奏
M1 / M2 相关逻辑
```

---

## 3. 行为变化

儿童端可见变化：

```text
1. 上传中仍可看到当前图片小预览。
2. 可用拍照结果页中，缩略图和变身道具卡合并为中间结果区。
3. 变身道具卡仍显示 D3 / R1-A 固定模板反馈。
4. 图片缩略图尺寸受控，不抢小门和小白狐主视觉。
5. 小门推进后显示柔和光效，强化“门动了一下”的感觉。
6. 横屏 / 平板中结果区优先采用横向组合；窄屏中采用上下组合。
```

未改变：

```text
1. 不改 image_purpose，仍为 share。
2. 不改 attachment 链路。
3. 不改 R1-A 门状态节奏。
4. 不改词池。
5. 不改怪问题路径。
6. 不改小展台保存逻辑。
7. 不改后端。
```

---

## 4. 视觉合同

新增展示状态：

```text
showPhotoResultCard
showDoorSuccessGlow
```

处理方式：

```text
1. 只有可用拍照结果 showPhotoResultCard=true。
2. blocked 图片 showPhotoResultCard=false，且保存按钮仍不可用。
3. 只有可用拍照结果推进后 showDoorSuccessGlow=true。
4. ChoosingMethod / PhotoPrompt / Riddle 路径不显示拍照结果光效。
5. success glow 使用已有 DoorSuccessGlow 素材，不新增素材。
```

---

## 5. 安全和边界

已落实：

```text
1. 不新增素材。
2. 不改 image2 素材。
3. 不新增儿童端文案。
4. 不改词池。
5. 不改后端。
6. 不新增 endpoint。
7. 不新增 image purpose。
8. 不新增新关卡。
9. 不新增地图。
10. 不新增奖励、积分、等级、任务、打卡。
11. 不新增小展台复杂功能。
12. 不改家长端。
13. 不改 R1-A 门状态节奏。
```

---

## 6. 测试结果

已通过：

```bash
git diff --check
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*' --tests 'com.childai.companion.ui.chat.ChildCompanionPageRulesTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest'
bash scripts/android_gradle.sh assembleDebug
```

覆盖：

```text
1. 拍照结果页包含图片缩略图。
2. 可用拍照结果显示变身结果卡。
3. 变身道具卡仍显示固定模板。
4. 门状态对应正确素材。
5. success glow 只在可用拍照结果推进后显示。
6. blocked 图片不显示可保存结果卡，保存按钮仍不可用。
7. 按钮顺序仍为：再找一个 / 动脑试试 / 放进小展台。
8. 横屏 / 平板结果区采用受控尺寸，不让缩略图抢主视觉。
9. D3 拍照路径回归通过。
10. D4 怪问题路径回归通过。
11. D5 小展台承接回归通过。
```

---

## 7. 截图 / 录屏

本轮未产出截图或录屏。

原因：

```text
本轮在代码侧完成视觉合同和构建验证；未执行真机截图流程。
```

---

## 8. 风险点

```text
1. 轻叠加 success glow 在真机屏幕上的亮度需要继续 QA，避免看起来像奖励光或胜利光。
2. 窄屏结果区采用缩略图在上、道具卡在下，实际可读性仍需真机检查。
3. 当前不新增素材，因此门状态变化依赖已有 door state 图片和 success glow 的组合表达。
```

---

## 9. 是否可进入下一轮

结论：

```text
可以进入下一轮真机 QA 或继续 R1 后续视觉层级优化。
```
