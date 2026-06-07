# S4：奇怪小门三种小机关计划

日期：2026-06-07

执行角色：开发执行会话

状态：仅计划，不编码

---

## 1. 目标与边界

S4 只在 Android 本地为“再玩一次”增加三种小机关轮换：

```text
round -> soft -> shiny -> round
```

目标是让孩子重玩时看到不同的小要求。S4 不新增第二扇门、第二关、地图、任务、奖励、积分、等级、连续打卡、排行榜、后端接口、image_purpose 或素材；怪问题路径和小展台列表详情不改。

---

## 2. 对 18 个问题的计划回答

### 2.1 当前 StrangeDoorDemoSnapshot 是否需要新增 doorNeed / mechanismType 字段

需要新增机制字段，但不建议新增自由文本 `doorNeed`。

计划新增：

```kotlin
enum class StrangeDoorMechanismType {
    Round,
    Soft,
    Shiny,
}
```

并在 `StrangeDoorDemoSnapshot` 增加：

```kotlin
val mechanismType: StrangeDoorMechanismType = StrangeDoorMechanismType.Round
```

原因：

```text
1. 机关类型会影响首屏气泡、PhotoPrompt、PhotoTransformMapper 和 replay 轮换。
2. 用 enum 可以避免在状态里保存任意儿童端文案。
3. doorNeed 文案从 mechanismType 派生，避免多处散落自由文本。
```

### 2.2 机关类型是放在 snapshot、reducer，还是 UI model

计划：

```text
1. snapshot 保存当前 mechanismType。
2. reducer 负责 reset / replay / requestAnotherPhoto 时保留或轮换 mechanismType。
3. UI model 只根据 snapshot.mechanismType 派生显示文案。
4. PhotoTransformMapper 接收 mechanismType，用于本地匹配和词池选择。
```

不把机关类型只放 UI model，因为 mapper 和 reducer 都需要知道当前机关；也不把它只放 reducer，因为 UI 文案需要稳定读取当前状态。

### 2.3 首次进入默认 round 是否合适

合适。

计划保持 `StrangeDoorDoorStateReducer.reset()` 返回默认：

```text
ChoosingMethod + Closed + Round
```

这符合主控倾向，也兼容当前 D2-D5/R1/S3 默认圆圆机关体验。

### 2.4 “再玩一次”如何轮换 round -> soft -> shiny

当前 `replay()` 只是 `reset()`，S4 计划改为基于当前 snapshot 轮换。

建议接口：

```kotlin
fun replay(snapshot: StrangeDoorDemoSnapshot): StrangeDoorDemoSnapshot
```

轮换规则：

```text
Round -> Soft
Soft -> Shiny
Shiny -> Round
```

重玩后状态：

```text
demoState = ChoosingMethod
doorState = Closed
attemptsCount = 0
lastPhotoTransform = null
lastRiddleEvaluation = null
lastPhotoMessageId = null
showcaseSaveIntentRequested = false
showcaseSavedName = null
mechanismType = nextMechanismType
```

小展台已保存内容不删除、不清空。

### 2.5 App 重启后是否可以重新从 round 开始

可以。

S4 首版只做 Android 本地 ViewModel 生命周期内状态，不做持久化。App 重启后通过 `reset()` 重新从 Round 开始，符合主控倾向。

### 2.6 PhotoPrompt 文案如何按机关类型切换

计划将当前固定 `photoPromptLines` 改为按 `mechanismType` 派生，只使用主控文档文本：

Round：

```text
找一个有点圆的东西就行
瓶盖、杯子、球、纽扣都可以
奇怪一点也可以
```

Soft：

```text
找一个软软的东西就行
毛巾、抱枕、布娃娃、纸巾都可以
奇怪一点也可以
```

Shiny：

```text
找一个有点亮的东西就行
勺子、杯盖、小灯、亮亮的贴纸都可以
奇怪一点也可以
```

按钮仍沿用现有主控文本：

```text
拍给小白狐看
先换个办法
```

### 2.7 首屏气泡如何按机关类型切换

当前首屏固定为圆圆。S4 计划改为根据 `mechanismType` 生成：

Round：

```text
你来得正好
我被这扇奇怪小门挡住了
它说：
找一个圆圆的东西
或者答对一个怪问题
```

Soft：

```text
你来得正好
我被这扇奇怪小门挡住了
它说：
找一个软软的东西
或者答对一个怪问题
```

Shiny：

```text
你来得正好
我被这扇奇怪小门挡住了
它说：
找一个亮亮的东西
或者答对一个怪问题
```

首屏按钮仍保持：

```text
找东西帮忙
动脑试试
```

### 2.8 PhotoTransformMapper 如何按机关类型做关键词匹配

计划将 mapper 从：

```kotlin
map(recognition)
```

扩展为：

```kotlin
map(recognition, mechanismType)
```

匹配规则：

```text
1. 先执行 blockedTypes / blockedTextKeywords 安全阻断。
2. 再按当前 mechanismType 优先匹配对应适合物品关键词。
3. 命中当前机关关键词时，生成当前机关对应的高匹配道具名。
4. 未命中当前机关但内容安全时，仍走 partial / unknown 的温柔接住。
5. 所有安全可用结果仍是 AdvanceOneStep。
6. blocked / privacy / homework 仍是 None。
```

建议关键词只来自主控文档中的“适合物品”和既有 R1-A 圆形关键词：

Round：

```text
瓶盖、杯子、球、纽扣、圆盘、饼干、盖子、圆形
```

Soft：

```text
毛巾、抱枕、布娃娃、纸巾、衣服、毯子
```

Shiny：

```text
勺子、杯盖、灯、金属、小贴纸、反光物
```

如需增加“软、布、棉、亮、闪、反光、银色”等更泛化词，需主控确认后再加入。

### 2.9 soft / shiny 词池如何接入

新增词池只接入 `StrangeDoorPhotoTransformMapper`，并纳入 `approvedChildFacingCopy()` 和禁止词测试。

Soft 道具名：

```text
软云开门垫
抱抱小推垫
毛毛门铃
轻轻擦门布
软软通行垫
棉花小按钮
```

Shiny 道具名：

```text
小闪光转轮
亮亮照门灯
星星反光片
银色小钥匙
闪闪门铃
小光斑按钮
```

小门反应词池沿用 R1-A 已批准词池，不新增反应文案。

### 2.10 拍错但安全时是否仍 AdvanceOneStep

计划仍 `AdvanceOneStep`。

依据主控文档：

```text
孩子拍错也要有趣；
但 unsafe / privacy / homework 仍不能进入道具链路。
```

实现含义：

```text
1. 不符合当前机关但安全时，仍生成可用的 partial / unknown 反馈。
2. doorState 推进一小步。
3. 反馈保持轻，不表达答错、失败、任务或通关。
```

### 2.11 blocked / privacy / homework 是否仍 None

是。

计划继续保持：

```text
blocked / privacy_sensitive / unsafe_unknown / homework_problem -> None
```

且：

```text
1. 不推进门状态。
2. 不生成道具名。
3. 不允许保存到小展台。
4. 不保存额外敏感图片信息。
```

### 2.12 怪问题路径是否保持不变

保持不变。

S4 不改题目、不改语音路径、不改本地判断规则。回答包含“水”仍直接让门进入 Open，并进入现有 Completed 收束。

### 2.13 小展台保存是否不改

不改小展台列表详情，也不改保存边界。

拍照变身结果仍只在 `canSaveToShowcase=true` 且孩子主动完成保存时进入现有小展台能力。保存内容继续取当次 `lastPhotoTransform` 的道具名和小白狐反馈；S4 不新增小展台分类、图鉴、背包或机关筛选。

### 2.14 会修改哪些文件

计划实现阶段会修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapper.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorStateContractTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapperTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorForbiddenWordsTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorDemoTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorPhotoTransformTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/handoffs/20260607_S4_strange_door_mechanism_variants_handoff.md
```

本轮计划阶段只新增：

```text
docs/session_process/handoffs/20260607_S4_strange_door_mechanism_variants_plan.md
```

### 2.15 不会修改哪些文件

计划实现阶段不会修改：

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

### 2.16 测试策略

计划新增或更新以下测试：

```text
1. 默认 StrangeDoorDemoSnapshot / reset() 的 mechanismType 为 Round。
2. replay 从 Round 轮换到 Soft。
3. replay 从 Soft 轮换到 Shiny。
4. replay 从 Shiny 轮换到 Round。
5. replay 重置门状态、attemptsCount 和 lastPhotoTransform，但不触碰小展台数据。
6. App 重启等价的 reset() 仍从 Round 开始。
7. 首屏气泡按 Round / Soft / Shiny 显示对应小门要求。
8. PhotoPrompt 按 Round / Soft / Shiny 显示对应提示。
9. mapper 在 Round 下命中圆形物品并使用圆形词池。
10. mapper 在 Soft 下命中软物并使用 soft 词池。
11. mapper 在 Shiny 下命中亮物并使用 shiny 词池。
12. 安全但不符合当前机关的内容仍 AdvanceOneStep。
13. blocked / privacy / homework 仍 None，且 canSaveToShowcase=false。
14. 怪问题答对仍直接 Open。
15. “再找一个”不轮换机关；Open 时重置 Closed + PhotoPrompt 并保留当前机关。
16. 新增 soft / shiny 词池全部进入 approvedChildFacingCopy 并通过禁止词测试。
17. D3 / D4 / D5 / R1-A / R1-B / R1-C / S2 / S3 相关回归继续通过。
```

计划运行：

```bash
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorDemoTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest'
bash scripts/android_gradle.sh testDebugUnitTest
bash scripts/android_gradle.sh assembleDebug
git diff --check
```

### 2.17 风险点

```text
1. recognizedContent 可能只给笼统描述，soft / shiny 如果只用严格物品词，命中率可能不稳定。
2. 如果允许泛化关键词，可能提升命中率，但需要主控确认，避免开发方自行扩写体验词池。
3. 拍错但安全仍推进门，体验更温柔，但“机关要求”和门变化的因果可能变弱。
4. 三种机关共用同一套门素材，不会表现不同机关外观；S4 仅体现为小门要求和变身道具变化。
5. App 重启回 Round，重玩新鲜感只在本次 ViewModel 生命周期内成立，不是长期进度。
6. “再找一个”和“再玩一次”都可从 Open 后重新开始，需避免用户误解两者轮换规则。
```

### 2.18 需要主控确认的问题

```text
1. soft / shiny 关键词是否只能使用主控文档列出的适合物品，还是允许加入“软、布、棉、亮、闪、反光、银色”等泛化匹配词？
2. 安全但不符合当前机关的物品是否确认仍 AdvanceOneStep？
3. “再找一个”是否确认不轮换机关，只在“再玩一次”轮换机关？
4. Open 后点击“再找一个”时，计划保留当前 mechanismType 并重置 Closed + PhotoPrompt，是否确认？
5. 小展台详情是否不展示机关类型，只保存当次变身反馈，是否确认？
```

---

## 3. 当前建议结论

建议 S4 按如下方式实现：

```text
1. 增加 Android 本地 mechanismType 字段，默认 Round。
2. replay 负责 Round -> Soft -> Shiny -> Round 轮换。
3. reset / App 重启仍从 Round 开始。
4. 首屏气泡和 PhotoPrompt 只按主控文本动态切换。
5. mapper 按当前机关选择关键词和道具名词池。
6. 安全但不匹配继续温柔推进；blocked / privacy / homework 继续阻断。
7. 怪问题和小展台保持现状。
```
