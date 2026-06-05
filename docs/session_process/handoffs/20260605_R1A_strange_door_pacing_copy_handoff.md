# R1-A：奇怪小门词池、门状态节奏与按钮优先级优化交接

日期：2026-06-05

执行角色：开发执行会话

任务范围：不新增功能，只优化“孩子愿意再拍一个”的吸引力；本轮只调整拍照门状态推进节奏、R1 主控词池、拍照结果按钮顺序和测试覆盖。

---

## 1. 本轮结论

R1-A 已完成。

已按主控确认后的边界落地：

```text
1. 拍照 round 不再一次直接 open，改为 AdvanceOneStep。
2. 拍照 partial 继续 AdvanceOneStep。
3. 拍照 unknown 继续 AdvanceOneStep，并使用更轻的反馈。
4. 拍照 blocked 仍为 None，不推进门、不允许保存。
5. 怪问题答对仍由 Open 信号直接打开门。
6. 当前门已经 almost_open 时，下一次有效拍照可推进到 open。
7. StrangeDoorPhotoTransformMapper 词池只接入主控 R1 文档词池。
8. 拍照结果按钮顺序改为：再找一个 / 动脑试试 / 放进小展台。
```

---

## 2. 修改文件

修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapper.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorPhotoTransformTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorShowcaseTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorForbiddenWordsTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapperTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorStateContractTest.kt
```

新增：

```text
docs/session_process/handoffs/20260605_R1A_strange_door_pacing_copy_handoff.md
```

未修改：

```text
backend/
android/app/src/main/res/drawable-nodpi/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/ui/parent/
M1 / M2 相关逻辑
```

---

## 3. 行为变化

儿童端可见变化：

```text
1. 第一次有效拍照后，小门从 closed 推进到 cracked。
2. 第二次有效拍照后，小门从 cracked 推进到 almost_open。
3. almost_open 后再次有效拍照，小门推进到 open。
4. 圆形物品不再让小门一次直接打开。
5. 拍照结果页主按钮顺序变为：再找一个 / 动脑试试 / 放进小展台。
6. 小展台仍只承接保存，不抢主玩法。
```

未改变：

```text
1. 拍照入口仍走现有 attachment 链路。
2. image_purpose 仍为 share。
3. 不新增后端 endpoint。
4. 不新增 strange_door image purpose。
5. 不新增第二关、地图、奖励、积分、等级、任务、打卡。
6. 不改怪问题真实交互；怪问题答对仍直接 open。
7. 不改小展台复杂功能。
```

---

## 4. R1 词池接入

已接入主控 R1 词池：

```text
1. 圆形 / 接近圆形道具名词池。
2. 不太圆 / 有点奇怪道具名词池。
3. 看不太清 / unknown 道具名词池。
4. 轻推进反馈词池。
5. 半成功 / 乱拍反馈词池。
6. 打开反馈词池。
```

处理方式：

```text
1. recognizedContent 仍先映射为现实物品名。
2. mapper 根据识别文本归类为 round / partial / unknown / blocked。
3. round / partial / unknown 均返回 AdvanceOneStep。
4. blocked 返回 None。
5. 展示层根据推进后的 doorState，在 open 时显示 R1 打开反馈。
```

---

## 5. 安全和边界

已落实：

```text
1. 不改 UI 布局。
2. 不改素材。
3. 不改后端。
4. 不新增 endpoint。
5. 不新增 image purpose。
6. 不新增新关卡。
7. 不新增地图。
8. 不新增奖励、积分、等级、任务、打卡。
9. 不新增小展台复杂功能。
10. 不改家长端。
11. 不自行扩写儿童端文案。
```

---

## 6. 测试结果

已通过：

```bash
git diff --check
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest'
bash scripts/android_gradle.sh assembleDebug
```

覆盖：

```text
1. round 不再一次直接 open。
2. round 从 closed 推进到 cracked。
3. 第二次有效拍照推进到 almost_open。
4. almost_open 后再有效拍照可 open。
5. 怪问题答对仍然直接 open。
6. blocked 仍然 None。
7. R1 新词池全部进入 approvedChildFacingCopy。
8. 禁止词测试继续通过。
9. 按钮顺序为“再找一个 / 动脑试试 / 放进小展台”。
10. D3 拍照路径回归通过。
11. D4 怪问题路径回归通过。
12. D5 小展台承接回归通过。
```

---

## 7. 截图 / 录屏

本轮未产出截图或录屏。

原因：

```text
R1-A 不改 UI 布局、不改素材；本轮验证以状态合同、mapper、按钮顺序和 Android 构建为主。
```

---

## 8. 风险点

```text
1. R1-A 已让拍照首次反馈更慢，真机上需要验证孩子是否理解“门只开一点”是可继续尝试，而不是卡住。
2. unknown 当前也会推进一小步；如果真实识别结果过于宽泛，可能让模糊图片也推进，后续可由主控决定是否收紧。
3. mapper 仍是确定性模板，不调用模型生成，因此表现稳定但变化有限。
4. open 反馈由推进后的 doorState 决定，保存到小展台的 foxQuote 也会使用对应门状态反馈。
```

---

## 9. 需要主控确认的问题

```text
1. 是否按计划进入 R1-B：小门视觉层级与“挡住小白狐”的表现优化。
2. unknown 有效拍照推进一小步是否在真机试玩中继续保留，还是后续需要提高识别门槛。
3. 小展台按钮保持第三优先级后，是否需要在下一轮真机 QA 中重点观察点击率。
```
