# M3：小白狐轻记忆 Android 展示实现计划

日期：2026-06-13

状态：PLAN / 待主控审核

范围：只规划 Android 展示实现，不编码，不修改后端，不新增数据持久化。

---

## 0. 依据

已阅读并遵守：

```text
docs/session_process/handoffs/20260613_M2_light_memory_copy_and_display_strategy_plan.md
docs/session_process/handoffs/20260613_M2_light_memory_copy_and_display_strategy_handoff.md
docs/小白狐轻记忆儿童端文案_2026_06_13_V0_1.md
docs/session_process/handoffs/20260612_M1_light_memory_local_state_contract_handoff.md
docs/session_process/handoffs/20260612_M1_light_memory_local_state_contract_plan.md
docs/小白狐轻记忆产品方向设计_2026_06_12_V0_1.md
docs/PRODUCT_DECISIONS_V0_1.md
```

最高优先级产品决策：

```text
PD-061
```

---

## 1. M3 目标

把 M1 的本地状态合同和 M2 的 master-copy 文案接入儿童端展示策略。

M3 首版建议只做：

```text
1. opening 轻记忆展示；
2. LightMemoryCopyMapper；
3. LightMemoryUiModel；
4. 多候选优先级选择；
5. opening 展示后标记 recalled；
6. 禁止文案扫描测试；
7. 相关 ViewModel / mapper 测试；
8. CODEX_PROGRESS_BOARD 更新。
```

M3 首版建议暂缓：

```text
普通聊天 relatedChatCandidate 可规划，但不接入主 conversation。
```

原因：普通聊天接入会影响主 conversation 发送与回复节奏，主控已倾向 M3 先只接 opening，普通聊天可放 M4。

---

## 2. opening 轻记忆文案插在哪里

建议插入位置：

```text
普通 opening greeting 成功展示之后，作为一段本地追加的小白狐消息。
```

实现层建议：

```text
ChatViewModel.requestOpeningGreeting()
  -> backend opening response 成功
  -> renderAgentReply(response, replaceMessageId = "agent-welcome")
  -> 尝试生成 LightMemoryUiModel
  -> 如果有可展示文案，追加一条本地 Agent ChatMessage
  -> markLightMemoryOpeningRecalled()
```

不建议：

```text
1. 不替换 backend opening 文案；
2. 不拼接进 backend opening response；
3. 不调用后端重新生成；
4. 不新增按钮；
5. 不新增小展台或奇怪小门入口。
```

---

## 3. 替代原 opening，还是 opening 后一段

建议：作为 opening 后的一段。

原因：

```text
1. 原 opening 仍由现有 opening 逻辑负责，不改变后端接口。
2. 轻记忆是低频补充，不应该抢普通 opening。
3. 单独本地消息更容易测试是否使用 M2 master-copy。
4. 不需要修改 opening API schema。
5. 失败时可以静默不展示，不影响普通 opening。
```

语音策略建议：

```text
M3 首版只做文本展示，不新增 TTS 播报策略。
```

原因：M2 任务目标是儿童端文案与展示，未确认轻记忆是否需要自动语音播报；如果同时播报，可能和普通 opening / 语言游戏入口产生重复听感。是否播报建议作为主控确认问题。

---

## 4. 如何读取 ChatUiState.lightMemory.openingRecallCandidate

读取入口：

```text
state.lightMemory.openingRecallCandidate
```

使用边界：

```text
1. 只读取 M1 已暴露的安全摘要字段。
2. 不读取 rawTranscript / rawPhotoBytes / recognizedText / childAnswer。
3. 不读取 image bytes。
4. 不读取后端 memory。
5. 不读取语言游戏偏好。
```

实现建议：

```kotlin
LightMemoryCopyMapper.toOpeningUiModel(
    snapshot = state.lightMemory,
)
```

`toOpeningUiModel` 内部只接受 `openingRecallCandidate` 或按 M3 优先级从 `activeCandidates` 中选出一条，并返回可展示的 `LightMemoryUiModel?`。

---

## 5. 如何按 source 映射 M2 master-copy

建议新增纯函数：

```text
LightMemoryCopyMapper
```

映射规则：

```text
ShowcaseAssist / ShowcaseItem：
  默认使用 M3 确认的更轻版本：
  我想起了小展台里的 {name}
  它好像轻轻动了一下

  不过今天想聊新的也可以

StrangeDoorCompleted 且有 displayName：
  我好像想起 {name}
  它曾经帮过一扇奇怪小门

  今天也可以从新的事情开始

StrangeDoorCompleted 无 displayName：
  我好像想起一扇奇怪小门
  有个小东西曾经帮过忙

  今天也可以从新的事情开始

StrangeDoorMechanism / Round：
  我好像想起一个圆圆的小机关
  它轻轻咔哒了一下

  今天想玩什么都可以

StrangeDoorMechanism / Soft：
  我好像想起一个软软的小机关
  它轻轻挪了一点点

  今天想玩什么都可以

StrangeDoorMechanism / Shiny：
  我好像想起一个亮亮的小机关
  它闪了一下又安静了

  今天想玩什么都可以
```

`StrangeDoorTool` 的处理建议：

```text
若只有 StrangeDoorTool，按“StrangeDoorCompleted 且有 displayName”的轻小门文案处理。
```

原因：M2 没有为单独 StrangeDoorTool 提供独立 master-copy；M3 不新增儿童端文案，只复用已确认的 displayName 小门文案。

---

## 6. 多候选时如何只选一条

按主控确认优先级：

```text
1. ShowcaseAssist；
2. ShowcaseItem；
3. StrangeDoorCompleted 且有 displayName；
4. StrangeDoorTool；
5. StrangeDoorCompleted 无 displayName；
6. StrangeDoorMechanism。
```

同一优先级内：

```text
选择 lastTouchedAtMillis 最新的一条。
```

实现建议：

```text
1. 在 LightMemoryCopyMapper 内实现 selectOpeningCandidate。
2. M3 可同步调整 LightMemoryReducer.withOpeningRecallEligibility 的候选选择逻辑，让 openingRecallCandidateId 与 M3 优先级一致。
3. 不新增字段，不改 LightMemorySource，不改已有数据合同语义。
```

---

## 7. 如何调用 markLightMemoryOpeningRecalled

建议在 ChatViewModel 中完成，不放到 Compose UI 副作用里。

原因：

```text
1. 避免 Compose 重组导致重复标记。
2. 便于 ViewModel 单测。
3. opening 消息追加和 recalled 状态更新可以在同一逻辑中完成。
```

建议流程：

```text
1. opening response 成功并通过 childInteractionStarted 检查；
2. renderAgentReply 完成普通 opening；
3. 从当前 state 生成 LightMemoryUiModel；
4. 若 uiModel != null，追加本地 Agent 消息；
5. 调用 LightMemoryReducer.markOpeningRecalled；
6. 更新 uiState.lightMemory。
```

已有 public 方法：

```text
markLightMemoryOpeningRecalled()
```

M3 实现时可复用，也可在 private opening 渲染函数内直接使用 reducer；计划建议保留 public 方法给测试使用。

---

## 8. 如何保证每个 ChatViewModel 生命周期最多一次

依赖 M1 状态：

```text
recalledInCurrentLifecycle
lastRecalledCandidateId
openingRecallCandidateId
mutedForCurrentLifecycle
```

M3 需要保证：

```text
1. 只有 openingRecallCandidateId != null 时才生成文案；
2. 展示后立即 markOpeningRecalled；
3. mark 后 openingRecallCandidateId 清空；
4. recalledInCurrentLifecycle == true 时不再展示；
5. requestOpeningGreeting 重复调用仍受 openingRequested 保护；
6. App 重启后本地 LightMemorySnapshot 为空，不做跨天恢复。
```

---

## 9. 如何在先聊别的 / 换题 / 跳过后 mute

M1 已提供：

```text
muteLightMemoryForLifecycle()
LightMemoryReducer.muteForCurrentLifecycle()
```

M3 实现建议：

```text
1. 保持已有“先聊别的”路径调用 mute。
2. 语言游戏 dismiss / exit 继续调用 mute。
3. 奇怪小门 exit / 先聊别的继续调用 mute。
4. M3 不新增“跳过”按钮，因此不新增跳过入口。
5. 如果孩子在轻记忆展示后直接输入普通新话题，因已 mark recalled，本生命周期不会再次 opening 召回。
```

“换题”处理：

```text
M3 不改语言游戏逻辑；若后续 M4/M5 需要把语言游戏换题也视为 mute，应单独确认。
```

---

## 10. 普通聊天 relatedChatCandidate 是否在 M3 接入

建议 M3 不接入。

结论：

```text
M3 只接 opening 展示；
relatedChatCandidate 继续只作为 M1 状态条件保留；
普通聊天主动相关文案放到 M4。
```

原因：

```text
1. 普通聊天接入会影响主 conversation 行为。
2. 需要决定轻记忆文案由 Android 本地插入，还是作为后端 conversation 上下文。
3. M3 禁止新增后端，因此不适合把相关候选传给 conversation。
4. 主控已倾向 M3 先只接 opening。
```

---

## 11. 如果接入普通聊天，如何保证只按关键词触发

M3 不实现，但 M4 可采用：

```text
1. 只读取 state.lightMemory.relatedChatCandidate；
2. relatedChatCandidate 只能由 LightMemorySafetyGate.isRelatedChatText 允许关键词触发；
3. 允许关键词继续限制为：
   - 小门
   - 奇怪小门
   - 小展台
   - 小发现
   - 刚才那个
   - 我放进去的
   - 帮小白狐
4. 不对普通聊天做自由抽取；
5. 不把候选写入后端；
6. 不保存孩子原始输入。
```

---

## 12. 是否只先接 opening，不接普通聊天

建议：是。

M3 首版只验证：

```text
1. opening 后轻轻想起是否自然；
2. 是否低频；
3. 是否不抢奇怪小门和语言游戏；
4. 是否不像监控或系统复盘。
```

普通聊天接入留到 M4，先由 M3 真机验收反馈决定是否继续。

---

## 13. 是否新增自动禁止文案扫描测试

建议：新增。

测试范围：

```text
LightMemoryCopyMapperTest
```

覆盖：

```text
1. 输出不包含 M2 禁止文案；
2. 输出不包含“通关 / 奖励 / 任务 / 等级 / 分数 / 排名 / 打卡”；
3. 输出不包含“我一直记得你 / 我一直在等你 / 只有我记得 / 这是我们的秘密”；
4. 输出不包含 rawTranscript / rawPhotoBytes / recognizedText / childAnswer；
5. 所有 source 映射结果完全等于 M2 master-copy。
```

---

## 14. 是否更新 CODEX_PROGRESS_BOARD

建议 M3 实现时更新。

计划：

```text
1. 当前阶段从 M2 文档收口切到 M3 Android 展示实现。
2. 标记 M3 目标为 opening 轻记忆展示。
3. 标记 M3 不接普通聊天、不改后端、不改家长端。
```

本计划轮只新增计划文档，不更新进度板。

---

## 15. 是否需要更新已有 ChatViewModel 测试

需要。

建议更新 / 新增：

```text
1. ChatViewModelOpeningTest：
   - opening 成功后追加轻记忆消息；
   - child input 先发生时不追加轻记忆；
   - opening 失败时不追加轻记忆；
   - 展示后 markLightMemoryOpeningRecalled；
   - 每生命周期最多一次。

2. ChatViewModelLightMemoryTest：
   - 多候选按 M3 优先级选择；
   - mutedForCurrentLifecycle 时不展示；
   - strangeDoorDemo != null 时不展示；
   - languageGame != null 时不展示；
   - 语言游戏不写入轻记忆仍通过。
```

---

## 16. 是否需要新增 LightMemoryCopyMapper

建议新增。

建议路径：

```text
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/LightMemoryCopyMapper.kt
```

职责：

```text
1. 从 LightMemorySnapshot 中选择 opening 候选；
2. 按 source / mechanismType / displayName 映射 M2 master-copy；
3. 输出 LightMemoryUiModel?；
4. 不访问 Android Context；
5. 不访问网络；
6. 不访问 repository；
7. 不保存状态。
```

---

## 17. 是否需要新增 LightMemoryUiModel

建议新增。

建议放在：

```text
LightMemoryCopyMapper.kt
```

建议字段：

```text
candidateId: String
source: LightMemorySource
text: String
lines: List<String>
```

边界：

```text
1. 只包含可展示文案；
2. 不包含 raw transcript；
3. 不包含图片引用；
4. 不包含 recognizedContent；
5. 不包含孩子原始回答；
6. 不包含分数、等级、排名。
```

---

## 18. 会修改哪些文件

M3 实现预计修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/LightMemoryCopyMapper.kt
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/LightMemoryReducer.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/lightmemory/LightMemoryCopyMapperTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelLightMemoryTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelOpeningTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/handoffs/20260613_M3_light_memory_android_display_handoff.md
```

是否修改 `ChildChatScreen.kt`：

```text
首选不修改。
```

原因：如果轻记忆作为本地 Agent ChatMessage 追加到 `messages`，现有聊天气泡 UI 可直接渲染，不需要新增 UI 组件和按钮。

---

## 19. 不会修改哪些文件

M3 实现不应修改：

```text
backend/
家长端
小展台数据模型
小展台列表 / 详情 UI
奇怪小门玩法节奏
奇怪小门素材
奇怪小门门状态 reducer
语言游戏题库
语言游戏词库
语言游戏状态机
attachment 后端链路
conversation / opening 后端接口
GrowthEvent
image_purpose
数据库 migration
```

也不应提交：

```text
真实儿童照片
真实儿童音频
原始聊天转录
私有截图
家庭测试材料
prompt trace
本地数据库
模型权重
TTS cache
```

---

## 20. 真机验收重点

M3 真机验收建议重点看：

```text
1. opening 后轻记忆是否像小白狐轻轻想起，而不是系统复盘。
2. 是否只出现一次，不重复刷屏。
3. 是否不打断奇怪小门首屏事件。
4. 是否不在语言游戏进行中出现。
5. 是否不新增按钮或入口。
6. 是否不催孩子继续旧流程。
7. 是否不出现任务、奖励、通关、等级、打卡、排名感。
8. 孩子先聊别的后，本生命周期不再自动提。
9. 如果与语言游戏 EntryPrompt 同时存在，首屏是否显得拥挤。
10. 文案是否短、轻、可放下。
```

---

## 21. 需要主控确认的问题

```text
1. 是否确认 M3 首版只接 opening，不接普通聊天 relatedChatCandidate。
2. 是否确认 opening 轻记忆作为普通 opening 后的一段本地 Agent 消息，而不是替代原 opening。
3. 是否确认 M3 首版不自动 TTS 播报轻记忆文案。
4. 是否确认 StrangeDoorTool 可复用“displayName 小门文案”，不新增独立道具文案。
5. 是否确认 M3 可调整 LightMemoryReducer.withOpeningRecallEligibility 的候选选择逻辑，以匹配本轮多候选优先级。
6. 是否确认轻记忆展示与语言游戏 EntryPrompt 的关系：
   - 方案 A：二者可同次出现，M3 不改语言游戏入口逻辑；
   - 方案 B：若轻记忆已展示，本次 opening 不自动弹语言游戏入口。
7. 是否确认 M3 实现时更新 CODEX_PROGRESS_BOARD。
8. 是否确认新增禁止文案扫描测试。
9. 是否确认 M3 不修改 ChildChatScreen，优先使用现有消息气泡承接。
10. 是否确认 M4 再评估普通聊天主动相关接入。
```

---

## 22. 本计划轮交付边界

本计划轮只新增：

```text
docs/session_process/handoffs/20260613_M3_light_memory_android_display_plan.md
```

不修改：

```text
android/
backend/
docs/CODEX_PROGRESS_BOARD_V0_1.md
家长端
小展台代码
奇怪小门代码
语言游戏代码
素材
题库
词库
```
