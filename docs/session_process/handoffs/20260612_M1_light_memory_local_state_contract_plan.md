# M1：小白狐轻记忆本地状态与数据合同计划

日期：2026-06-13（文件名沿用主控指定的 20260612 批次）

状态：PLAN

范围：只规划 Android 本地轻状态与数据合同，不编码，不新增儿童端最终文案，不改后端，不改家长端，不扩小展台数据模型，不接语言游戏偏好。

---

## 0. 依据

已确认依据：

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/小白狐轻记忆产品方向设计_2026_06_12_V0_1.md
docs/session_process/handoffs/20260612_M0_light_memory_product_direction_plan.md
docs/session_process/handoffs/20260612_M0A_light_memory_decision_and_M1_boundary_plan.md
docs/session_process/handoffs/20260608_S5_showcase_item_back_to_door_handoff.md
docs/session_process/handoffs/20260609_LG_review_language_game_suite_handoff.md
```

最高优先级产品决策：

```text
PD-061
```

M1 只服务一个目标：

```text
让小白狐能在低敏、低频、可放下的前提下，轻轻记得一点点共同经历。
```

---

## 1. LightMemorySnapshot 放在哪里

建议放在 Android 本地 `ui/chat` 范围内，作为儿童聊天体验的本地状态合同。

建议路径：

```text
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/LightMemorySnapshot.kt
```

原因：

```text
1. M1 不做后端记忆。
2. M1 轻召回依赖 ChatViewModel 生命周期。
3. 轻记忆只服务儿童聊天、小门和小展台之间的本地连续性。
4. 放在 chat 范围内能避免误解为全局成长系统或后端长期记忆。
```

---

## 2. 是否放入 ChatUiState

建议放入 `ChatUiState`，但只作为派生后的只读 UI snapshot。

建议形式：

```text
ChatUiState.lightMemory: LightMemorySnapshot
```

边界：

```text
1. ChatViewModel 持有和更新本生命周期内的轻状态。
2. ChatUiState 只暴露 UI 和测试需要的轻状态摘要。
3. 不在 ChatUiState 中暴露原始识别文本、原始回答、图片 bytes 或聊天全文。
4. 不把 lightMemory 写入后端或本地文件。
```

---

## 3. 是否新增 lightmemory 包

建议新增。

建议包名：

```text
com.childai.companion.ui.chat.lightmemory
```

建议只放本地合同和纯函数：

```text
LightMemorySnapshot
LightMemorySource
LightMemoryCandidate
LightMemoryStatus
LightMemoryReducer
LightMemorySafetyGate
```

M1 不建议新增 repository、service、database、network client 或后端 schema。

---

## 4. LightMemorySource 有哪些枚举

M1 来源白名单建议仅包含：

```text
StrangeDoorCompleted
StrangeDoorMechanism
StrangeDoorTool
ShowcaseItem
ShowcaseAssist
```

含义：

```text
StrangeDoorCompleted：
  奇怪小门已完成的低敏摘要。

StrangeDoorMechanism：
  最近安全机关类型，Round / Soft / Shiny。

StrangeDoorTool：
  最近安全道具名，只来自已通过 mapper 的安全结果。

ShowcaseItem：
  既有小展台 item 的安全字段读取。

ShowcaseAssist：
  小展台小发现回来帮过门的本地摘要。
```

M1 明确不包含：

```text
LanguageGamePreference
ConversationExtracted
BackendMemorySummary
ParentReportMemory
LearningProfile
```

---

## 5. LightMemoryCandidate 有哪些字段

建议字段：

```text
id: String
source: LightMemorySource
status: LightMemoryStatus
safeLabel: String
displayName: String?
mechanismType: StrangeDoorMechanismType?
toolName: String?
showcaseItemId: String?
showcaseItemName: String?
showcaseCreatedAtMillis: Long?
showcaseFoxQuote: String?
assistedDoorInCurrentLifecycle: Boolean
lastTouchedAtMillis: Long
```

字段边界：

```text
id：
  本地派生 id，只用于本生命周期内去重和测试，不落库。

safeLabel：
  内部低敏标签，例如 strange_door_completed / round / soft / shiny / showcase_item。

displayName：
  可展示名称的安全摘要，只能来自安全道具名或小展台 name。

mechanismType：
  只允许 Round / Soft / Shiny。

toolName：
  只允许来自 StrangeDoorPhotoTransformMapper 已批准词池的道具名。

showcaseItemId / showcaseItemName / showcaseCreatedAtMillis / showcaseFoxQuote：
  只读既有小展台安全字段，不复制图片、不修改 item、不新增副本。

assistedDoorInCurrentLifecycle：
  只标记本生命周期内该小发现是否回来帮过门，不写 GrowthEvent。
```

禁止字段：

```text
rawTranscript
rawPhotoBytes
photoBytes
recognizedText
recognizedContentRaw
privacySignal
childRawAnswer
conversationText
score
level
rank
school
address
phone
realName
promptTrace
```

---

## 6. LightMemoryStatus 有哪些状态

建议状态：

```text
Active
RecalledInCurrentLifecycle
MutedForCurrentLifecycle
Blocked
```

含义：

```text
Active：
  可作为低频召回候选。

RecalledInCurrentLifecycle：
  本 ChatViewModel 生命周期已经用过，不再自动 opening 召回。

MutedForCurrentLifecycle：
  孩子选择先聊别的、换题、跳过或表现出暂放后，本生命周期不再提。

Blocked：
  因 blocked / privacy / homework / unsafe / 敏感字段命中而不可使用。
```

`Blocked` 只用于测试和内部过滤，不进入儿童端 UI。

---

## 7. 如何从奇怪小门生成完成摘要

生成条件：

```text
1. StrangeDoorDemoSnapshot 存在。
2. doorState == Open 或 demo 状态进入 Completed。
3. 当前路径不是 blocked / privacy / homework。
4. 若来自拍照，lastPhotoTransform 必须 canSaveToShowcase == true 或 advanceSignal != None 且通过安全门。
5. 若来自怪问题，只记录完成过，不记录孩子原始回答。
```

生成内容：

```text
source = StrangeDoorCompleted
safeLabel = strange_door_completed
mechanismType = 当前 mechanismType
toolName = 最近安全道具名，可为空
displayName = 最近安全道具名或最近小展台小发现名称，可为空
lastTouchedAtMillis = 当前本地时间
```

不记录：

```text
1. 原始照片。
2. 原始图片引用。
3. recognizedContent 原文。
4. 孩子怪问题原始回答。
5. 失败、错误、分数或排名。
```

---

## 8. 如何记录最近安全机关类型

来源：

```text
StrangeDoorDemoSnapshot.mechanismType
```

允许值：

```text
Round
Soft
Shiny
```

更新时机：

```text
1. 奇怪小门完成时。
2. 有效拍照推进门状态时。
3. 小展台小发现回来帮门并推进门状态时。
```

过滤：

```text
blocked / privacy / homework / unsafe 不更新最近安全机关类型。
```

---

## 9. 如何记录最近安全道具名

来源白名单：

```text
1. StrangeDoorPhotoTransformMapper 输出的 approved toolName。
2. 小展台小发现回来帮门时的 showcaseItemName。
```

拍照来源必须满足：

```text
1. transformResult.advanceSignal != None。
2. transformResult.canSaveToShowcase == true。
3. transformResult.toolName 来自主控批准词池。
4. transformResult 不属于 blocked / privacy / homework。
```

小展台来源必须满足：

```text
1. item.name 非空。
2. item.name 通过轻记忆安全过滤。
3. item 不被复制、不被修改、不新增副本。
```

不允许把 `recognizedContent` 原文作为道具名保存。

---

## 10. 如何从既有小展台读取最近小发现名称

读取方式：

```text
复用现有小展台数据读取能力，按 createdAt 取最近的安全 item。
```

读取目的：

```text
1. 为轻记忆候选提供最近小发现名称。
2. 为奇怪小门 PhotoPrompt 后续选择小展台物品提供本地候选依据。
3. 为普通聊天孩子主动提到小展台 / 小发现时提供可接住的安全摘要。
```

不做：

```text
1. 不新增小展台字段。
2. 不修改 XiaozhantaiItem。
3. 不复制图片。
4. 不新增小展台历史。
5. 不新增成长事件。
```

---

## 11. 是否允许读取小展台 item 的 id、name、createdAt、foxQuote

建议允许读取以下字段：

```text
id
name
createdAt
foxQuote
```

使用边界：

```text
id：
  只用于定位既有 item 和本地去重。

name：
  作为小发现名称候选，必须经过轻记忆安全过滤。

createdAt：
  只用于选择最近 item，不做连续打卡或历史排行。

foxQuote：
  只作为既有小展台当时一句话的安全摘要来源，不扩写、不改写、不生成新儿童端最终文案。
```

不建议读取到轻记忆合同：

```text
photoUri
imageBytes
recognizedContent
privacySignals
```

如果现有小展台列表 UI 需要 `photoUri` 显示图片，那仍属于 S2 / S5 既有 UI 行为；M1 轻记忆合同不读取、不复制、不保存图片引用。

---

## 12. 如何标记小展台小发现是否回来帮过门

建议通过本地候选状态标记：

```text
source = ShowcaseAssist
showcaseItemId = 既有 item id
showcaseItemName = 既有 item name
assistedDoorInCurrentLifecycle = true
lastTouchedAtMillis = 当前本地时间
```

触发条件：

```text
1. 孩子从 S5 选择模式选择已有小展台 item。
2. item 回到奇怪小门后推进门状态。
3. 当前门状态不是 Open 入口态。
```

不做：

```text
1. 不修改 XiaozhantaiItem。
2. 不新增副本。
3. 不写入历史。
4. 不新增 GrowthEvent。
5. 不改变小展台普通列表和详情。
```

---

## 13. 如何确保 blocked / privacy / homework 不进入轻状态

建议新增本地安全门函数：

```text
LightMemorySafetyGate.accept(candidateInput): Boolean
```

过滤规则：

```text
1. StrangeDoorPhotoTransformMapper 输出 blocked 时，不生成 candidate。
2. canSaveToShowcase == false 时，不生成道具类 candidate。
3. recognizedContent 原文永远不进入 candidate。
4. homework / privacy / unsafe / face / school / address / phone / certificate / medical 命中时，直接 Blocked。
5. 小展台 name / foxQuote 若命中隐私、作业、学习答案、真实身份信息，不能作为 Active candidate。
6. 语言游戏 transcript 和普通聊天 transcript 不进入 candidate。
```

测试要求：

```text
blocked / privacy / homework 输入不能生成 Active 轻记忆；
也不能通过小展台回来帮门间接生成 Active 轻记忆。
```

---

## 14. 如何记录本生命周期是否已经轻召回

建议在 `LightMemorySnapshot` 记录：

```text
recalledInCurrentLifecycle: Boolean
lastRecalledCandidateId: String?
```

规则：

```text
1. 每个 ChatViewModel 生命周期最多自动 opening 召回一次。
2. 一旦 opening 召回过，recalledInCurrentLifecycle = true。
3. 奇怪小门进行中不触发 opening 召回。
4. 孩子选择先聊别的后，本生命周期不再自动召回。
```

不写入后端、不写入本地文件、不跨 App 重启持久化。

---

## 15. 如何记录跳过 / 暂放

建议在 `LightMemorySnapshot` 记录：

```text
skipCountInCurrentLifecycle: Int
mutedForCurrentLifecycle: Boolean
```

触发条件：

```text
1. 孩子点击先聊别的。
2. 孩子在 opening 轻召回后立即转到无关话题。
3. 孩子短答、沉默或表现出不继续此话题。
```

M1 只规划状态，不新增儿童端最终文案，不实现孩子端显式“忘掉这个”。

---

## 16. opening 召回条件是什么

建议同时满足：

```text
1. strangeDoorDemo == null。
2. languageGame == null。
3. 普通 opening 可展示。
4. lightMemory.recalledInCurrentLifecycle == false。
5. lightMemory.mutedForCurrentLifecycle == false。
6. 至少存在一个 Active candidate。
7. candidate 来源属于 M1 白名单。
8. 当前不是安全、高风险、隐私、学习、睡前收尾等优先场景。
9. 当前没有正在进行的拍照、上传、怪问题、小展台选择或语言游戏流程。
```

输出边界：

```text
M1 不写 opening 最终儿童端文案，只输出“可以召回哪类低敏候选”的状态合同。
```

---

## 17. 普通聊天主动相关接住条件是什么

只在孩子主动提到相关内容时接住。

建议触发关键词范围：

```text
小门
奇怪小门
小展台
小发现
刚才那个
我放进去的
帮小白狐
```

限制：

```text
1. 不做普通聊天自由抽取。
2. 不从普通聊天中生成新轻记忆。
3. 不保存孩子原始输入。
4. 只使用已有 Active candidate 作为低敏上下文。
5. 不引导孩子回去继续玩，不做任务式召回。
```

M1 不新增普通聊天儿童端最终文案，只定义何时允许 UI / ViewModel 使用轻记忆上下文。

---

## 18. 奇怪小门 PhotoPrompt 是否读取最近小展台小发现

建议允许读取，但仅作为本地候选和状态条件。

用途：

```text
1. 判断是否可以显示 S5 已有的“用小展台里的”入口。
2. 为选择模式提供最近 item 排序。
3. 记录某个小发现是否回来帮过门。
```

边界：

```text
1. 不新增 PhotoPrompt 儿童端最终文案。
2. 不改变 S5 选择模式普通行为。
3. 不复制图片或图片引用到轻记忆。
4. 不强匹配 Round / Soft / Shiny。
5. 不把小展台改成背包、图鉴、任务列表。
```

---

## 19. 是否完全不触碰后端

是。

M1 禁止修改：

```text
backend/
backend/app/api/
backend/app/services/
backend/app/repositories/
backend/app/domain/
backend/app/db/
backend/app/providers/
migrations
```

M1 禁止新增：

```text
memory endpoint
memory service
memory repository
database table
migration
GrowthEvent
image_purpose
conversation / opening API schema
```

---

## 20. 是否完全不新增儿童端最终文案

是。

M1 只规划状态和合同，不新增儿童端最终文案。

如后续 M1 实现需要任何儿童端可见文本，必须先由主控提供精确文案，并写入对应 master-copy 文档或产品决策。

---

## 21. public repo 数据扫描清单如何落文档

M1 交接文档应包含 public repo 扫描清单，建议检查：

```text
.env
API key
token
production credential
真实儿童姓名
真实家庭信息
真实学校
住址
电话
证件
人脸
原始儿童音频
原始儿童照片
私有截图
原始聊天转录
prompt trace
本地数据库
模型权重
生成的 TTS cache
家庭测试材料
```

建议执行命令：

```bash
git status --short
git diff --cached --name-only
git diff --cached --check
rg -n "api[_-]?key|token|secret|BEGIN PRIVATE KEY|prompt trace|真实姓名|学校|住址|电话|证件|身份证" .
find . -path "./.git" -prune -o \( -name "*.wav" -o -name "*.mp3" -o -name "*.m4a" -o -name "*.sqlite" -o -name "*.db" -o -name "*.pt" -o -name "*.onnx" \) -print
```

注意：

```text
真机截图 / 录屏如要入库，必须使用测试账号、测试素材、无真实儿童隐私内容。
M1 不要求新增扫描脚本，只要求交接文档落清单。
```

---

## 22. 真机验收清单如何落文档

M1 交接文档应新增真机验收清单：

```text
1. 奇怪小门完成后，本地轻状态存在完成摘要。
2. 最近安全机关类型只出现 Round / Soft / Shiny。
3. 最近安全道具名只来自主控批准词池或既有小展台 item name。
4. blocked / privacy / homework 拍照不进入 Active 轻状态。
5. 小展台保存成功后，轻状态只读取 id / name / createdAt / foxQuote。
6. 小展台小发现回来帮门后，只记录本生命周期 assistedDoorInCurrentLifecycle。
7. opening 轻召回每个 ChatViewModel 生命周期最多一次。
8. 孩子选择先聊别的后，本生命周期不再自动召回。
9. 普通聊天只有孩子主动提小门 / 小展台 / 小发现时才允许接住。
10. 语言游戏过程不写入轻记忆。
11. 后端、家长端、小展台数据模型无变化。
12. 仓库不包含真实儿童照片、音频、聊天转录、私有截图或家庭测试材料。
```

验收判断：

```text
孩子感觉小白狐像朋友一样轻轻想起一点点；
不是系统复盘、监控、评价或催促继续。
```

---

## 23. 会修改哪些文件

本轮计划只新增：

```text
docs/session_process/handoffs/20260612_M1_light_memory_local_state_contract_plan.md
```

如主控确认进入 M1 实现，预计后续才可能修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatUiState.kt 或等价状态文件
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/*
android/app/src/test/java/com/childai/companion/ui/chat/lightmemory/*
android/app/src/test/java/com/childai/companion/ui/chat/*
docs/session_process/handoffs/20260612_M1_light_memory_local_state_contract_handoff.md
```

后续实现文件以代码实际结构为准，仍不得扩大到后端、家长端或小展台数据模型。

---

## 24. 不会修改哪些文件

本轮不会修改：

```text
android/
backend/
小展台代码
奇怪小门代码
语言游戏代码
家长端代码
题库
词库
素材
docs/PRODUCT_DECISIONS_V0_1.md
```

M1 实现阶段也不应修改：

```text
backend/
家长端
语言游戏题库
语言游戏词库
小展台数据模型
奇怪小门玩法节奏
attachment 链路
conversation / opening 后端接口
```

---

## 25. 需要主控确认的问题

1. `LightMemorySnapshot` 是否确认放入 `ChatUiState`，还是先作为 `ChatViewModel` 私有状态、只在测试中读取。
2. 是否确认新增 `ui/chat/lightmemory/` 包承载本地合同和纯函数。
3. 小展台 `foxQuote` 是否确认可读；若 `foxQuote` 含隐私或不适合召回内容，是否直接过滤整条 item。
4. `LightMemoryStatus` 是否接受 `Active / RecalledInCurrentLifecycle / MutedForCurrentLifecycle / Blocked` 四态。
5. opening 轻召回是否只允许在同一 ChatViewModel 生命周期内验证，App 重启后重新为空。
6. 普通聊天主动相关关键词是否以上述范围为准，还是需要主控提供更严格的关键词白名单。
7. M1 实现是否需要同步更新 `CODEX_PROGRESS_BOARD_V0_1.md`，标记阶段进入轻记忆 M1。
8. public repo 数据扫描本阶段是否只落清单，还是 M1 实现时需要新增脚本。
9. opening 和普通聊天中的轻记忆最终儿童端文案由哪个主控文档承接。

---

## 26. 测试策略

M1 实现阶段建议覆盖：

```text
1. reset 后 LightMemorySnapshot 为空或默认安全态。
2. 奇怪小门 Completed 生成 StrangeDoorCompleted candidate。
3. Round / Soft / Shiny 只记录为最近安全机关类型。
4. 安全道具名只来自 mapper 批准结果。
5. blocked / privacy / homework 不生成 Active candidate。
6. 小展台只读取 id / name / createdAt / foxQuote。
7. 小展台小发现回来帮门后 assistedDoorInCurrentLifecycle == true。
8. opening 召回每生命周期最多一次。
9. 先聊别的后 mutedForCurrentLifecycle == true。
10. 普通聊天未主动提相关内容时不使用轻记忆。
11. 语言游戏不写入 LightMemorySnapshot。
12. 禁止词 / 禁存字段测试覆盖 rawTranscript、rawPhotoBytes、recognizedText、score、rank、school、address、phone、realName、promptTrace。
```

本轮计划文档校验：

```bash
git diff --check -- docs/session_process/handoffs/20260612_M1_light_memory_local_state_contract_plan.md
```

---

## 27. 风险点

1. 如果轻记忆被过早做成跨天持久化，会触发家长授权、清除和管理问题。
2. 如果从普通聊天自由抽取，会滑向隐私档案和画像。
3. 如果读取小展台 `foxQuote` 不做安全过滤，可能把旧文本中的不适合内容带入召回。
4. 如果 opening 召回过频，会让孩子感觉被系统复盘或催促继续。
5. 如果把语言游戏结果写入轻记忆，容易变成成绩或表现记录。
6. 如果把小展台图片引用纳入轻记忆，容易扩大图片隐私边界。
7. public repo 下如果提交真机真实素材，会造成儿童隐私风险。
