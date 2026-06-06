# S3：奇怪小门 Demo 退出与重玩收口计划

日期：2026-06-06

执行角色：开发执行会话

任务状态：PLAN ONLY，不编码。

当前状态：

```text
1. S2 我的小展台列表与详情已完成，状态 CODE PASS / 待合并真机验收。
2. R1-C 仍为 CODE PASS / 待真机视觉验收。
3. 当前没有真机测试条件。
4. 本轮只做不依赖真机视觉判断的体验收口计划。
```

---

## 1. S3 目标

让孩子在奇怪小门 Demo 完成后，能自然选择：

```text
1. 再玩一次。
2. 再找一个东西。
3. 去小展台看看。
4. 先聊别的。
```

S3 不是新玩法，不做第二关、地图、任务、奖励或成长系统，只收口当前 Demo 的完成态、保存完成态、退出和重玩。

---

## 2. 当前奇怪小门 Demo 完成态有哪些

当前代码已有以下相关状态：

```text
StrangeDoorDemoState.Completed
StrangeDoorDemoState.ShowcaseSaved
```

当前完成判断：

```text
StrangeDoorDemoSnapshot.isCompleted = demoState == Completed || doorState == Open
```

当前进入 `Completed` 的路径：

```text
1. 拍照路径：有效拍照把 doorState 推进到 Open 后，reducer 将 demoState 置为 Completed。
2. 怪问题路径：答对“水”后，advanceSignal=Open，reducer 将 doorState 置为 Open，并将 demoState 置为 Completed。
```

当前进入 `ShowcaseSaved` 的路径：

```text
1. D3 拍照变身结果 canSaveToShowcase=true。
2. 孩子点击“放进小展台”。
3. 确认并起名。
4. 现有小展台保存成功后，ChatViewModel 将 demoState 置为 ShowcaseSaved，并记录 showcaseSavedName。
```

注意：

```text
ShowcaseSaved 不一定代表 doorState 已经 open。
孩子可以在门 cracked / almost_open 时就保存一个小发现。
```

---

## 3. 当前 doorState=open 后孩子还能做什么

当前代码表现：

```text
1. 如果 open 来自拍照路径，Completed 页面仍展示“现实物品 -> 奇怪道具 -> 小门反馈”结果。
2. 拍照完成态当前按钮为：再找一个 / 动脑试试 / 放进小展台。
3. 如果 open 来自怪问题路径，Completed 页面展示 D4 怪问题答对反馈。
4. 怪问题完成态当前按钮为：再找一个 / 先聊别的。
5. 当前没有“再玩一次”按钮。
6. 当前没有完成态主按钮“去小展台看看”。
7. 当前 photo completed 页面没有“先聊别的”按钮，只有 riddle completed 有。
```

当前问题：

```text
doorState=open 后，“再找一个”会进入 PhotoPrompt，但 doorState 仍是 Open。
下一次有效拍照从 Open 继续推进仍会保持 Open，孩子容易感觉没有新变化。
```

---

## 4. 当前保存到小展台后孩子还能做什么

当前 `ShowcaseSaved` 页面显示：

```text
{name}，放好啦
以后可以在小展台里看到它
```

当前按钮为：

```text
再找一个
动脑试试
先聊别的
```

当前问题：

```text
1. 保存完成态没有主按钮“去小展台看看”。
2. 保存完成态仍有“动脑试试”，但 S3 主控按钮只给了“去小展台看看 / 再找一个 / 先聊别的”。
3. S2 小展台入口虽然作为弱入口存在，但保存完成后缺少明确承接。
```

---

## 5. 是否已有“退出 Demo 回普通聊天”的能力

已有，但不完整。

已有实现：

```text
1. StrangeDoorHomeEventActionId.ExitDemo 已存在。
2. ChildChatScreen 已把 ExitDemo 接到 onStrangeDoorExitDemo。
3. ChatViewModel.exitStrangeDoorDemoAndRequestOpening() 已存在。
4. 该方法会将 strangeDoorDemo 置为 null。
5. 若普通 opening 之前被奇怪小门延后，会调用 requestOpeningGreeting() 恢复普通 opening。
6. strangeDoorDemo=null 后，普通 InputBar / conversation 页面会恢复。
```

当前不足：

```text
1. ExitDemo 并未出现在所有完成态按钮里。
2. ChildChatScreen 当前进入聊天页会自动 activateStrangeDoorDemo()。
3. 如果孩子点击“先聊别的”退出后又从小展台 / 家长页返回 ChatScreen，存在重新自动激活 Demo 的风险。
```

S3 计划：

```text
1. 保留现有 exitStrangeDoorDemoAndRequestOpening()。
2. 增加仅当前 ViewModel 生命周期内的本地内存标记，例如 strangeDoorDemoDismissed。
3. 孩子点击“先聊别的”后设置该标记，避免本次页面生命周期内再次自动激活 Demo。
4. 不把该标记写入后端、仓库、文件或持久化存储。
5. App 重启后仍可按当前 Demo 入口规则重新出现。
```

---

## 6. 是否已有“重置 Demo 再玩一次”的能力

只有底层能力，没有儿童端动作。

已有实现：

```text
1. StrangeDoorDoorStateReducer.reset() 已存在。
2. activateStrangeDoorDemo() 会使用 reset() 初始化 ChoosingMethod + Closed。
```

缺少：

```text
1. 没有 StrangeDoorHomeEventActionId.ReplayDemo。
2. 没有“再玩一次”按钮。
3. 没有 ChatViewModel.replayStrangeDoorDemo() 之类的儿童端动作。
```

S3 计划：

```text
新增“再玩一次”动作，调用 reset()，回到 ChoosingMethod + Closed。
```

---

## 7. S3 需要新增哪些本地状态

计划不新增复杂 Demo 状态，不新增关卡状态。

建议：

```text
1. 不新增 StrangeDoorDemoState 枚举。
2. 继续复用 Completed 表示门打开完成态。
3. 继续复用 ShowcaseSaved 表示保存完成态。
4. 新增 UI action id：
   - ReplayDemo
   - OpenShowcase
5. ChatViewModel 增加一个非持久化内存标记：
   - strangeDoorDemoDismissed
```

`strangeDoorDemoDismissed` 只用于避免孩子点击“先聊别的”后又被当前 ChatScreen 自动拉回奇怪小门，不写入后端，不写入本地文件，不进入小展台或 GrowthEvent。

---

## 8. S3 是否只改 Android 本地状态，不改后端

是。

S3 计划只改 Android 本地 UI 状态与本地 ViewModel 行为：

```text
1. 不新增后端 endpoint。
2. 不新增 image_purpose。
3. 不改 attachment 链路。
4. 不改 conversation API。
5. 不改小展台后端能力。
6. 不新增 GrowthEvent。
7. 不新增后端成长系统。
```

---

## 9. 完成态按钮如何设计

主控确认的完成态文案：

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

计划：

```text
1. `Completed` 状态统一展示上述完成态文本。
2. 不再让完成态继续显示 D3 拍照打开反馈或 D4 答对反馈作为主页面文本。
3. 完成态仍按 doorState=Open 显示 open 小门素材。
4. “再玩一次”是第一优先级。
5. “再找一个”是第二优先级，直接进入 PhotoPrompt。
6. “去小展台看看”打开 S2 小展台列表。
7. “先聊别的”退出 Demo 并恢复普通聊天。
```

说明：

```text
D3 / D4 的原有过程反馈仍来自拍照或语音答题处理链路；S3 收口重点是门已打开后的完成选择。
```

---

## 10. 保存完成态按钮如何设计

主控确认的保存完成态文案：

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

计划：

```text
1. 保持现有保存完成态文本。
2. 将保存完成态按钮改为主控确认顺序。
3. 移除保存完成态里的“动脑试试”按钮。
4. “去小展台看看”直接打开 S2 小展台列表。
5. “再找一个”进入 PhotoPrompt。
6. “先聊别的”退出 Demo 并恢复普通聊天。
```

---

## 11. 退出后普通 opening / conversation 如何恢复

现有恢复机制：

```text
1. exitStrangeDoorDemoAndRequestOpening() 将 strangeDoorDemo 置为 null。
2. 如果 openingDeferredByStrangeDoor=true 或 opening 尚未请求，则调用 requestOpeningGreeting()。
3. requestOpeningGreeting() 已有“Demo 活跃时延后 opening”的保护。
4. strangeDoorDemo=null 后，普通聊天页面和 InputBar 恢复。
```

S3 计划补强：

```text
1. 点击“先聊别的”后设置非持久化 strangeDoorDemoDismissed=true。
2. ChildChatScreen 自动激活 Demo 前检查该标记或由 ViewModel 内部拒绝再次自动激活。
3. 不自动发送 conversation 文本。
4. 不保存额外持久状态。
5. 如果 opening 已经出现过，不重复请求 opening。
```

---

## 12. 重玩后是否清空当前门状态

是。

点击“再玩一次”：

```text
1. 调用 StrangeDoorDoorStateReducer.reset()。
2. demoState 回到 ChoosingMethod。
3. doorState 回到 Closed。
4. attemptsCount 清零。
5. lastPhotoTransform / lastRiddleEvaluation / lastPhotoMessageId 清空。
6. showcaseSaveIntentRequested=false。
7. showcaseSavedName=null。
8. riddleAttempts 清零。
9. 不删除小展台内容。
10. 不清空已保存展品。
```

---

## 13. “再找一个”的门状态策略

主控规则要求：

```text
1. 一般情况下，“再找一个”进入 PhotoPrompt。
2. 一般情况下，保留当前 doorState，继续推进门状态。
3. 如果门已经 open，可以重新从 closed 开始，具体方案由计划说明后等主控确认。
```

当前计划建议：

```text
1. doorState 不是 Open 时：
   - “再找一个”沿用现有行为；
   - 进入 PhotoPrompt；
   - 保留当前 doorState；
   - 下一次有效拍照继续推进。

2. doorState 已经 Open 时：
   - “再找一个”进入 PhotoPrompt；
   - 同时将 doorState 重置为 Closed；
   - 清掉 lastPhotoTransform / lastRiddleEvaluation / showcaseSavedName；
   - 不删除小展台内容；
   - 不清空已保存展品。
```

理由：

```text
Open 已经是门状态终点。如果继续保留 Open，下一次拍照不会产生明显门变化，会像卡住或无效。
```

需要主控确认：

```text
门已 open 后，“再找一个”是否按上述方案重置为 Closed + PhotoPrompt。
```

---

## 14. 是否保留小展台已保存内容

保留。

S3 不删除、不清空、不迁移小展台内容：

```text
1. “再玩一次”不删除小展台内容。
2. “再找一个”不删除小展台内容。
3. “先聊别的”不删除小展台内容。
4. “去小展台看看”只打开 S2 小展台列表。
5. 不新增删除、收起、分类、图鉴、背包或收藏系统。
```

---

## 15. 会修改哪些文件

计划中的后续实现预计修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
```

说明：

```text
1. StrangeDoorHomeEventUiModel.kt：
   - 增加完成态主控文案常量；
   - 增加 ReplayDemo / OpenShowcase action id；
   - 调整 Completed 和 ShowcaseSaved 的 actions。

2. StrangeDoorDemoState.kt：
   - 不新增 enum；
   - 可增加 reducer helper，例如 resetForReplay() / startFreshPhotoRoundAfterOpen()，避免 ViewModel 手写字段。

3. ChatViewModel.kt：
   - 增加 replayStrangeDoorDemo()；
   - 调整 requestAnotherStrangeDoorPhoto() 的 Open 分支；
   - 在 exitStrangeDoorDemoAndRequestOpening() 中设置当前生命周期内的 dismiss 标记；
   - 自动激活 Demo 时尊重 dismiss 标记。

4. ChildChatScreen.kt：
   - 处理 ReplayDemo / OpenShowcase action；
   - OpenShowcase 复用现有 onOpenXiaozhantai。
```

预计新增或更新测试：

```text
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorDemoTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorPhotoTransformTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorShowcaseTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorForbiddenWordsTest.kt
```

本计划文档：

```text
docs/session_process/handoffs/20260606_S3_strange_door_finish_replay_plan.md
```

---

## 16. 不会修改哪些文件

S3 不修改：

```text
backend/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/data/growth/
android/app/src/main/java/com/childai/companion/ui/showcase/
android/app/src/main/java/com/childai/companion/ui/parent/
android/app/src/main/res/drawable-nodpi/
StrangeDoorPhotoTransformMapper 词池
StrangeDoorRiddleEvaluator 题目与判定
```

S3 不做：

```text
1. 不新增第二扇门。
2. 不新增第二关。
3. 不新增地图。
4. 不新增奖励。
5. 不新增积分。
6. 不新增等级。
7. 不新增任务。
8. 不新增打卡。
9. 不新增排行榜。
10. 不新增家长端功能。
11. 不改后端。
12. 不改素材。
13. 不改 R1-A / R1-B / R1-C 视觉和节奏。
14. 不改 S2 小展台列表详情。
15. 不提交真实儿童照片、截图、音频、转录或隐私材料。
```

---

## 17. 测试策略

S3 实施阶段建议验证：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorDemoTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest' --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh assembleDebug
git diff --check
```

新增或更新测试覆盖：

```text
1. Completed 状态显示主控完成态文案。
2. Completed 状态按钮顺序为：再玩一次 / 再找一个 / 去小展台看看 / 先聊别的。
3. ShowcaseSaved 状态按钮顺序为：去小展台看看 / 再找一个 / 先聊别的。
4. “再玩一次”重置 demoState=ChoosingMethod、doorState=Closed。
5. “再玩一次”不清空小展台已保存内容。
6. doorState 非 Open 时，“再找一个”保留当前门状态并进入 PhotoPrompt。
7. doorState Open 时，“再找一个”按主控确认方案处理。
8. “先聊别的”将 strangeDoorDemo 置为 null，并恢复普通 opening / conversation。
9. 退出后返回 ChatScreen 不自动重新激活奇怪小门 Demo。
10. “去小展台看看”复用现有 S2 小展台列表导航。
11. 怪问题答对仍不会调用普通 conversation。
12. D3 / D4 / D5 / R1-A / R1-B / R1-C / S2 回归不破。
13. 禁止词测试继续通过。
```

---

## 18. 风险点

```text
1. 完成态统一改成“开啦...”后，D3 / D4 原有打开过程反馈是否还需要在完成页保留，需要主控确认。
2. doorState Open 后点击“再找一个”如果重置为 Closed，孩子可能理解为新一轮；如果不重置，则下一次拍照没有明显门变化。计划建议重置。
3. `strangeDoorDemoDismissed` 是 ViewModel 生命周期内的非持久化标记；App 重启后 Demo 仍会按当前入口规则出现。
4. “去小展台看看”打开 S2 列表后，返回 ChatScreen 时会回到当前 Demo 状态；如果主控希望返回普通聊天，需要另行确认。
5. 完成态新增四个按钮，手机竖屏可能需要测试按钮换行与可读性，但本轮没有真机条件。
6. 保存完成态去掉“动脑试试”后，孩子若想答怪问题需要通过“再玩一次”或后续流程进入，不再从保存完成态直接进入。
```

---

## 19. 需要主控确认的问题

```text
1. doorState 已经 Open 后，点击“再找一个”是否确认重置为 Closed + PhotoPrompt？
2. Completed 页面是否确认统一使用“开啦...”完成态文案，覆盖当前 D3 / D4 的打开反馈展示？
3. “去小展台看看”返回 ChatScreen 后，是否保留当前 Demo 完成 / 保存状态，而不是自动退出到普通聊天？
4. 是否允许使用 ViewModel 生命周期内的非持久化 strangeDoorDemoDismissed 标记，防止“先聊别的”后返回 ChatScreen 又自动激活 Demo？
5. 完成态“去小展台看看”在没有任何已保存展品时是否仍保持可点击，进入 S2 空状态？
```

---

## 20. 计划结论

```text
S3 可以只通过 Android 本地状态和 UI action 收口完成态 / 保存态 / 退出 / 重玩。
不需要后端改造，不需要新素材，不需要新关卡。
核心新增是 ReplayDemo / OpenShowcase 两个本地动作，以及退出后的本地防重进保护。
计划等待主控确认后再进入实现。
```
