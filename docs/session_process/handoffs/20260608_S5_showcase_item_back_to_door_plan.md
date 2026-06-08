# S5：用小展台的小发现帮忙计划

日期：2026-06-08

执行角色：开发执行会话

状态：仅计划，不编码

---

## 1. 目标与边界

S5 目标是让孩子在 `PhotoPrompt` 里除了重新拍照，也可以从现有小展台选择一个以前保存的小发现，让它回到奇怪小门场景，推动小门一小步。

核心体验：

```text
我以前放进小展台的小东西，又回来帮小白狐了。
```

S5 不把小展台改成背包、图鉴、装备、任务或奖励系统；不改后端，不新增 endpoint、数据表、GrowthEvent 或 image_purpose；不修改小展台 item，不写入历史。

---

## 2. 对 15 个问题的计划回答

### 2.1 是否复用 S2 XiaozhantaiListScreen，还是新增选择模式页面

计划新增一个选择模式页面，但复用 S2 的列表内容、卡片模型、图片缩略图、名字和保存时间展示能力。

不直接复用普通 `XiaozhantaiListScreen` 原行为，原因：

```text
1. 普通入口标题是“我的小展台”，点击 item 进入详情。
2. S5 选择入口标题必须是“选一个小发现”，点击 item 要回到奇怪小门。
3. 空状态文案不同。
4. 普通列表和详情不能被 S5 行为污染。
```

建议实现形态：

```text
1. 在 XiaozhantaiScreens.kt 中增加选择模式 copy / content。
2. 复用 XiaozhantaiViewModel 的 items。
3. 复用 XiaozhantaiThumbCard / toGalleryCardUiModel / xiaozhantaiDateLabel。
4. 新增 XiaozhantaiPickScreen 或给列表内容增加 mode/config 参数。
```

### 2.2 如何从 PhotoPrompt 打开选择模式

首屏仍只显示：

```text
找东西帮忙
动脑试试
```

点击“找东西帮忙”进入 `PhotoPrompt` 后，按钮顺序改为：

```text
拍给小白狐看
用小展台里的
先换个办法
```

计划新增本地 action：

```text
StrangeDoorHomeEventActionId.OpenShowcasePicker
```

`ChildChatScreen` 处理该 action，调用从 `AppNavHost` 传入的 `onStrangeDoorOpenShowcasePicker`，进入小展台选择目的地。

### 2.3 选择 item 后如何回到 StrangeDoorDemo

计划在 `AppNavHost` 新增一个目的地：

```text
AppDestination.XiaozhantaiPickForStrangeDoor
```

流程：

```text
1. ChatScreen 的 PhotoPrompt 点击“用小展台里的”。
2. AppNavHost 切到 XiaozhantaiPickForStrangeDoor。
3. 选择页读取同一个 XiaozhantaiViewModel.items。
4. 孩子点击某个 item。
5. AppNavHost 调用 ChatViewModel.useXiaozhantaiItemForStrangeDoor(item)。
6. destination 回到 Chat。
7. ChatScreen 显示 StrangeDoorDemo 的旧物帮忙反馈。
```

为避免 `ChatViewModel` 在切走 Chat 分支后不可访问，计划把 `ChatViewModel` 的 `viewModel(key = "chat-${session.childId}")` 创建提升到 `AppNavHost` 的 `when` 外，与 `XiaozhantaiViewModel` 同级持有。

### 2.4 是否需要新增 StrangeDoorDemoState，例如 ShowcasePickPrompt / ShowcaseItemResult

计划不新增 `ShowcasePickPrompt`，因为选择页属于 `AppNavHost` 的页面目的地，不是奇怪小门主画面内部状态。

计划新增：

```text
StrangeDoorDemoState.ShowcaseItemResult
```

原因：

```text
1. 旧物帮忙不是拍照结果，不应塞进 lastPhotoTransform。
2. 旧物帮忙也不是保存完成态，不应复用 ShowcaseSaved。
3. 需要在返回 Chat 后稳定显示“{name} 又来帮忙啦”结构。
```

同时建议新增轻量本地结果结构：

```kotlin
data class StrangeDoorShowcaseAssistResult(
    val itemName: String,
    val doorEffect: String,
)
```

并在 `StrangeDoorDemoSnapshot` 中增加：

```text
lastShowcaseAssistResult
```

只保存 ViewModel 生命周期内的 item name 和门反应，不保存额外图片、音频或敏感信息。

### 2.5 旧物帮忙反馈如何进入 UI model

`StrangeDoorDemoSnapshot.toHomeEventUiModel()` 增加 `ShowcaseItemResult` 分支。

反馈 lines 使用主控确认文本：

```text
{name} 又来帮忙啦

小白狐把它轻轻放到门前
{小门反应}
```

其中 `{小门反应}` 从 R1-A 已批准小门反应词池中确定性选择，不新增反应文案。

旧物帮忙结果页建议按钮使用既有文案，不新增按钮文案：

```text
再找一个
动脑试试
```

不显示“放进小展台”，避免把同一个旧 item 再保存一次，也避免形成副本。

### 2.6 旧物帮忙如何推进门状态

计划新增 reducer 方法：

```text
applyShowcaseAssist(snapshot, itemName)
```

规则：

```text
1. doorState 非 Open：AdvanceOneStep。
2. doorState 为 Open：不从 Completed 暴露“用小展台里的”入口。
3. 如果孩子在 Open 后点“再找一个”，继续沿用 S3 逻辑：保留当前 mechanismType，重置 Closed + PhotoPrompt。
4. 从 PhotoPrompt 再进入选择模式后，旧物帮忙可推进一小步。
```

若从 `AlmostOpen` 推进到 `Open`，计划沿用 S3 完成态收束，显示 Completed 页面，不新增新的开门完成文案。这个点列入主控确认问题。

### 2.7 空小展台时如何回到拍照路径

选择页为空时显示主控确认文案：

```text
小展台还空空的
我们先找一个东西拍给小白狐看
```

计划：

```text
1. 仍停留在选择页，避免假装有可选 item。
2. 顶栏“关上”返回 ChatScreen。
3. 返回后保持 StrangeDoorDemo 在 PhotoPrompt。
4. 孩子可继续点击“拍给小白狐看”。
```

不新增空状态按钮文案。如主控希望空状态直接出现按钮“拍给小白狐看”，可以使用现有已批准文案，但需确认是否要一键回到拍照入口。

### 2.8 是否改小展台普通列表 / 详情

不改普通列表 / 详情行为。

允许做的最小改动：

```text
1. 抽出或参数化列表 content，供普通模式和选择模式复用。
2. 普通入口仍显示“我的小展台”。
3. 普通入口点击 item 仍进入详情。
4. 详情页仍只显示大图、名字、小白狐那时说。
5. 详情页不展示机关类型。
```

### 2.9 是否改后端

不改后端。

S5 只读取 Android 本地小展台 item，不新增 endpoint、不新增数据表、不新增 image_purpose、不发后端 conversation。

### 2.10 是否新增 GrowthEvent

不新增 GrowthEvent。

使用小展台物品帮忙时：

```text
1. 不新增 showcase_item_recalled。
2. 不新增任何“使用 item”事件。
3. 不写入本地成长事件。
4. 不写入后端。
```

现有 `showcase_item_saved` 保持只在保存小展台 item 时发生。

### 2.11 会修改哪些文件

计划实现阶段会修改：

```text
android/app/src/main/java/com/childai/companion/ui/AppNavHost.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/main/java/com/childai/companion/ui/showcase/XiaozhantaiScreens.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorShowcaseTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorStateContractTest.kt
android/app/src/test/java/com/childai/companion/ui/showcase/XiaozhantaiGalleryContractTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/handoffs/20260608_S5_showcase_item_back_to_door_handoff.md
```

如果为旧物帮忙反应抽独立 mapper，可能新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorShowcaseAssistMapper.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorShowcaseAssistMapperTest.kt
```

本轮计划阶段只新增：

```text
docs/session_process/handoffs/20260608_S5_showcase_item_back_to_door_plan.md
```

### 2.12 不会修改哪些文件

计划实现阶段不会修改：

```text
backend/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/data/showcase/XiaozhantaiModels.kt
android/app/src/main/java/com/childai/companion/data/showcase/XiaozhantaiRepository.kt
android/app/src/main/java/com/childai/companion/data/showcase/SaveXiaozhantaiItemUseCase.kt
android/app/src/main/java/com/childai/companion/data/growth/
android/app/src/main/java/com/childai/companion/ui/parent/
android/app/src/main/res/drawable-nodpi/
docs/assets/strange_door/
```

不提交：

```text
.env
API key
token
生产凭据
真实儿童姓名
真实家庭信息
原始儿童音频
原始儿童照片
私有截图
原始聊天转录
prompt trace
本地数据库
模型权重
生成的 TTS cache
真实家庭测试材料
```

### 2.13 测试策略

计划新增或更新测试：

```text
1. PhotoPrompt 按钮顺序为：拍给小白狐看 / 用小展台里的 / 先换个办法。
2. Completed 状态不显示“用小展台里的”。
3. S5 选择模式标题为“选一个小发现”。
4. S5 空状态显示“小展台还空空的 / 我们先找一个东西拍给小白狐看”。
5. 普通小展台入口仍显示“我的小展台”。
6. 普通小展台点击 item 仍进入详情。
7. 选择模式点击 item 不进入详情，而是回到 StrangeDoorDemo。
8. 选择 item 后进入 ShowcaseItemResult。
9. ShowcaseItemResult 显示“{name} 又来帮忙啦 / 小白狐把它轻轻放到门前 / {小门反应}”。
10. 旧物帮忙在 doorState 非 Open 时 AdvanceOneStep。
11. 旧物帮忙从 Closed 推进到 Cracked。
12. 旧物帮忙从 Cracked 推进到 AlmostOpen。
13. 旧物帮忙从 AlmostOpen 推进到 Open，并按 S3 Completed 收束。
14. 使用旧物帮忙不新增 GrowthEvent。
15. 使用旧物帮忙不修改 XiaozhantaiItem。
16. 使用旧物帮忙不新增副本。
17. 怪问题路径不变。
18. 小展台保存路径不变。
19. 禁止词测试继续覆盖新增文案。
20. D3 / D4 / D5 / S2 / S3 / S4 回归不破。
```

计划运行：

```bash
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.showcase.XiaozhantaiGalleryContractTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest' --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorDemoTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest'
bash scripts/android_gradle.sh testDebugUnitTest
bash scripts/android_gradle.sh assembleDebug
git diff --check
```

### 2.14 风险点

```text
1. AppNavHost 当前以简单 destination 分支管理页面，S5 需要确保 ChatViewModel 在选择页期间不丢失。
2. 如果选择页直接复用普通 XiaozhantaiListScreen，容易误把点击行为带到详情页，所以需要明确选择模式。
3. 旧物帮忙不按 Round / Soft / Shiny 强匹配，体验重点更清楚，但机关因果感比拍照弱，需要真机观察。
4. 小展台为空时如果只显示空状态，孩子可能还要点一次“关上”再拍照；是否需要一键回拍照需主控确认。
5. 旧物帮忙从 AlmostOpen 推进到 Open 时，是否显示旧物反馈还是 S3 Completed，需要主控确认。
```

### 2.15 需要主控确认的问题

```text
1. 选择页空状态是否只显示两行文案 + 顶栏“关上”返回 PhotoPrompt，还是要额外显示现有按钮“拍给小白狐看”？
2. 旧物帮忙从 AlmostOpen 推进到 Open 时，是否按 S3 Completed 统一收束，还是仍先显示“{name} 又来帮忙啦”反馈？
3. 旧物帮忙结果页按钮是否确认只显示“再找一个 / 动脑试试”，不显示“放进小展台”？
4. 选择模式是否允许复用 S2 卡片动效和视觉样式，只改标题、空状态和点击行为？
5. ChatViewModel 在 AppNavHost 中上提到 when 外创建，是否接受为实现选择页回调所需的结构调整？
```

---

## 3. 当前建议结论

建议 S5 按如下方式实现：

```text
1. 首屏不变，PhotoPrompt 增加“用小展台里的”。
2. 新增 AppDestination.XiaozhantaiPickForStrangeDoor。
3. 选择页复用 S2 列表内容，但使用选择模式标题、空状态和点击行为。
4. ChatViewModel 新增 useXiaozhantaiItemForStrangeDoor(item)。
5. StrangeDoorDemoState 新增 ShowcaseItemResult，不新增 ShowcasePickPrompt。
6. 旧物帮忙只做本地 AdvanceOneStep，不强匹配机关，不改 item，不写历史。
7. 后端、GrowthEvent、小展台普通列表详情、怪问题路径均不改。
```
