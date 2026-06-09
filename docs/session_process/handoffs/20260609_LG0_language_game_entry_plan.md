# LG0：聊天中游戏入口与游戏选择计划

日期：2026-06-09

执行角色：开发执行会话

状态：PLAN ONLY / 待主控确认

---

## 1. 本轮结论

LG0 只规划“聊天中随时可以选择随便聊聊或玩小游戏”的入口与状态架构，不编码、不实现具体游戏。

本轮按主控最新提示收窄首批游戏，只规划：

```text
1. 脑筋急转弯
2. 词语接龙
3. 猜谜语
```

说明：`docs/小白狐语言游戏扩展与聊天入口设计_2026_06_09_V0_1.md` 中曾列出更多候选项，`docs/小白狐语言类游戏方向设计_2026_06_09_V0_1.md` 中也有不同首批建议；本计划以后续主控提示为准，不把其它玩法纳入 LG0。

总体方案：

```text
1. 语言游戏入口是聊天里的轻选择，不做首页大功能区。
2. 奇怪小门优先；奇怪小门激活时不自动弹出语言游戏入口。
3. 语言游戏首版以 Android 本地状态为主，复用 ChatViewModel。
4. 首版不改后端、不新增 endpoint、不新增家长端。
5. 游戏菜单只显示主控确认的三个游戏和“先聊别的”。
```

---

## 2. 计划问题逐项回答

### 1. 语言游戏入口从哪里出现

入口只从普通儿童聊天页出现，作为聊天气泡 / 轻量面板，不做首页功能区、不做底部固定游戏入口、不做地图或游戏大厅。

入口文案使用主控文本：

```text
我们随便聊聊天
还是玩一个小游戏？
```

按钮：

```text
随便聊聊
玩个小游戏
```

点击“玩个小游戏”后进入游戏选择。

### 2. 是否在普通 opening 后出现

建议可以在普通 opening 完成后出现，但必须满足以下条件：

```text
1. strangeDoorDemo == null。
2. 当前没有图片上传、语音识别、TTS 播放中的关键流程。
3. 当前没有小展台保存命名弹窗。
4. 不在 ChatScreen 首屏抢奇怪小门。
5. 每个 ChatViewModel 生命周期内只轻触发一次，孩子点“随便聊聊”后本生命周期不再自动弹出。
```

这样不会把 App 打开后的第一眼从奇怪小门切走，也不会把普通聊天页改成游戏首页。

### 3. 是否在孩子说“玩游戏 / 脑筋急转弯 / 接龙 / 猜谜语”时出现

建议支持，但首版只做受控本地关键词触发，不做复杂意图分类：

```text
1. 孩子说“玩游戏”：进入 GameMenu。
2. 孩子说“脑筋急转弯”：进入 BrainTeaser 类型的游戏起始状态。
3. 孩子说“接龙”或“词语接龙”：进入 WordChain 类型的游戏起始状态。
4. 孩子说“猜谜语”：进入 Riddle 类型的游戏起始状态。
```

如果主控希望首版先统一进入菜单，也可以改成所有关键词都只打开 GameMenu。开发方不自行扩展触发词。

### 4. 奇怪小门和语言游戏谁优先

奇怪小门优先。

规则：

```text
1. strangeDoorDemo != null 时，不自动显示语言游戏入口。
2. 奇怪小门进行中，语音输入优先交给奇怪小门已有状态。
3. 孩子点击奇怪小门“先聊别的”退出后，恢复普通聊天，再允许语言游戏入口出现。
4. “去小展台看看”返回 ChatScreen 后，若奇怪小门仍保留完成 / 保存状态，不自动弹出语言游戏入口。
```

这样不影响奇怪小门主线和 S3 / S5 的完成态、重玩态、旧物帮忙路径。

### 5. 是否需要新增 LanguageGameState

建议需要。

建议新增 Android 本地状态，表达语言游戏当前处于入口、菜单或某个游戏流程中。例如：

```text
LanguageGameState.Inactive
LanguageGameState.EntryPrompt
LanguageGameState.GameMenu
LanguageGameState.InGame
```

LG0 不实现具体代码，后续实现时可用 sealed class 或 enum + snapshot，按现有奇怪小门本地状态风格收敛。

### 6. 是否需要新增 LanguageGameType

建议需要。

首版只允许：

```text
LanguageGameType.BrainTeaser
LanguageGameType.WordChain
LanguageGameType.Riddle
```

不加入其它候选项，不预留儿童端可见入口。

### 7. 是否需要新增本地 GameMenu 状态

建议需要，但不做独立系统。

`GameMenu` 应作为 `LanguageGameState` 的一个本地状态，用于展示：

```text
想玩哪一个？
```

按钮：

```text
脑筋急转弯
词语接龙
猜谜语
先聊别的
```

不新增独立导航页、不新增游戏大厅、不新增持久化。

### 8. 是否复用 ChatViewModel

建议复用 `ChatViewModel`。

理由：

```text
1. 语言游戏入口属于聊天里的轻选择。
2. 现有语音、TTS、普通 conversation、奇怪小门本地状态都在 ChatViewModel 协调。
3. 复用可以统一处理“先聊别的”、ASR transcript 和普通 conversation 互斥。
4. 不需要新增 AppNavHost 页面或独立 ViewModel。
```

后续实现时可在 `ChatUiState` 中增加 `languageGame` 本地 snapshot。

### 9. 是否需要后端

LG0 和首版菜单不需要后端。

首版三个游戏建议先按 Android 本地确定性规则实现：

```text
1. 题库 / 词池 / 谜题来自主控文档。
2. 判断规则本地执行。
3. 不新增 endpoint。
4. 不新增数据库表。
5. 不新增 GrowthEvent。
6. 不新增家长端报告。
```

如果未来需要模型生成题目或扩展题库，必须另开计划并由主控确认。

### 10. 是否影响普通 conversation

不应影响普通 conversation。

规则：

```text
1. languageGame == null 时，普通聊天完全走现有 conversation。
2. EntryPrompt / GameMenu 状态下，孩子点“随便聊聊”或“先聊别的”后清空 languageGame，再恢复普通 conversation。
3. InGame 状态下，游戏回答不发送普通 conversation，除非退出游戏。
4. 本地关键词触发只匹配主控确认的短触发词，不扩大成泛化意图拦截。
```

### 11. 如何从游戏返回普通聊天

统一使用主控确认文案：

```text
先聊别的
```

行为：

```text
1. 清空 languageGame 本地状态。
2. 不清空普通聊天历史。
3. 不触发奇怪小门。
4. 不写后端状态。
5. 后续孩子说话继续走普通 conversation。
```

### 12. 如何从普通聊天进入游戏选择

入口有两类：

```text
1. 普通 opening 后的轻入口：EntryPrompt -> GameMenu。
2. 孩子主动触发：关键词 -> GameMenu 或对应 LanguageGameType 起始状态。
```

入口只在普通聊天可用，不覆盖奇怪小门、小展台保存命名、图片上传等流程。

### 13. 每个游戏如何退出

首版统一：

```text
1. 游戏中按钮始终包含“先聊别的”。
2. 点击后清空 languageGame，回到普通聊天。
3. 不记录游戏结果。
4. 不展示分数、等级、奖励、连续记录或排名。
```

每个具体游戏的“下一题 / 再玩一次 / 换个游戏”等按钮文案，需要主控在后续 LG1 / LG2 / LG3 任务中精确确认，开发方不自行补。

### 14. 是否需要小展台承接

LG0 不接小展台。

首批三类游戏都先作为聊天里的短回合本地互动，不保存到小展台、不创建展品、不新增 GrowthEvent。

如果未来某个语言游戏要保存一句话、小故事或谜题结果，必须另开计划，并明确：

```text
1. 保存什么；
2. 是否保存原文；
3. 是否涉及儿童隐私；
4. 是否复用小展台；
5. 是否新增文案。
```

### 15. 会修改哪些文件

LG0 本轮只会新增计划文档：

```text
docs/session_process/handoffs/20260609_LG0_language_game_entry_plan.md
```

后续实现阶段预计会修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatUiState.kt 或 ChatViewModel.kt 内的状态定义位置
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/
android/app/src/test/java/com/childai/companion/ui/chat/
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/
```

如果当前代码没有独立 `ChatUiState.kt`，则在现有定义所在文件内做最小改动。

### 16. 不会修改哪些文件

LG0 本轮不会修改：

```text
android/
backend/
scripts/
android/app/src/main/res/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/data/growth/
android/app/src/main/java/com/childai/companion/ui/parent/
```

后续实现也不应修改：

```text
backend/
后端 endpoint
image_purpose
小展台列表详情
小展台保存路径
奇怪小门 reducer / mapper / 素材 / 门状态节奏
家长端
```

除非主控另行确认。

### 17. 测试策略

LG0 本轮为文档计划，只需要：

```bash
git diff --check
```

后续实现阶段建议测试：

```text
1. EntryPrompt 显示主控入口文案。
2. EntryPrompt 按钮为“随便聊聊 / 玩个小游戏”。
3. GameMenu 显示“想玩哪一个？”。
4. GameMenu 只显示“脑筋急转弯 / 词语接龙 / 猜谜语 / 先聊别的”。
5. 普通 opening 后可出现 EntryPrompt。
6. strangeDoorDemo 激活时不出现语言游戏入口。
7. 孩子说“玩游戏”进入 GameMenu。
8. 孩子说三个游戏名时进入对应 LanguageGameType。
9. EntryPrompt 点“随便聊聊”后恢复普通 conversation。
10. GameMenu 点“先聊别的”后恢复普通 conversation。
11. InGame 状态下 ASR transcript 不发送普通 conversation。
12. 退出游戏后下一句恢复普通 conversation。
13. 禁止词测试覆盖新增入口和菜单文案。
14. D3 / D4 / D5 / S2 / S3 / S4 / S5 回归不破。
15. assembleDebug 通过。
```

### 18. 风险点

```text
1. 普通 opening 后自动出现入口，可能让聊天像流程菜单，需要真机观察是否打断陪伴感。
2. 本地关键词拦截如果过宽，可能误伤普通 conversation。
3. 奇怪小门仍是当前主线，语言游戏入口不能抢首屏或抢“再找一个”的动机。
4. 三个游戏都需要主控提供完整题库、判断规则、提示文案和退出文案，开发方不能补写。
5. 词语接龙容易变成语文练习，需要后续明确“接住但不纠错”的规则。
6. 脑筋急转弯和猜谜语容易出现“答案 / 提示”结构，需要避免考试感。
7. 如果未来接小展台，必须避免保存长篇原始儿童文本。
```

### 19. 需要主控确认的问题

```text
1. 普通 opening 后的 EntryPrompt 是每个 ChatViewModel 生命周期只出现一次，还是每次进入 ChatScreen 都可以出现？
2. 孩子点击“随便聊聊”后，本生命周期是否不再自动弹出游戏入口？
3. 孩子说具体游戏名时，是直接进入对应游戏，还是先统一显示“想玩哪一个？”菜单？
4. 奇怪小门进行中孩子说“玩游戏”时，是否完全忽略语言游戏触发，直到孩子点击“先聊别的”？
5. 首版三个游戏的题库、提示、通过反馈、未接住反馈、结束按钮是否由后续 LG1 / LG2 / LG3 分别确认？
6. 语言游戏新方向是否需要同步写入 `docs/PRODUCT_DECISIONS_V0_1.md`，再进入实现？
```

---

## 3. 首版状态建议

建议后续实现使用一个本地 snapshot：

```text
LanguageGameSnapshot(
  state,
  selectedType,
  roundIndex,
  lastPrompt,
  lastChildAnswer
)
```

其中：

```text
state = Inactive / EntryPrompt / GameMenu / InGame
selectedType = BrainTeaser / WordChain / Riddle
```

LG0 不落代码；具体字段名以后续实现前代码结构为准。

---

## 4. 与奇怪小门的边界

保持 S5 之后的奇怪小门行为不变：

```text
1. 不改 StrangeDoorDemoState。
2. 不改 StrangeDoorDoorStateReducer。
3. 不改 StrangeDoorPhotoTransformMapper。
4. 不改 StrangeDoorRiddleEvaluator。
5. 不改小门素材、门状态节奏或小展台回到小门路径。
6. 不改 S3 的完成态、退出态和重玩逻辑。
```

语言游戏是普通聊天里的轻选择，不是奇怪小门的新机关。

---

## 5. 儿童端文案边界

LG0 计划只允许使用主控给出的入口和菜单文案。

允许文案：

```text
我们随便聊聊天
还是玩一个小游戏？
随便聊聊
玩个小游戏
想玩哪一个？
脑筋急转弯
词语接龙
猜谜语
先聊别的
```

开发方不得自行新增儿童端文案；具体游戏内文案留给后续主控任务。

禁止引入：

```text
考试
答错
错误
正确答案
分数
闯关
通关
任务
等级
奖励
金币
排名
PK
背诵
默写
纠错
语法错误
你说错了
我没听懂
再认真一点
```

---

## 6. 本轮测试与提交范围

本轮不编码、不运行 Android 构建。

已执行：

```bash
git pull --ff-only origin main
bash scripts/doctor_local_env.sh
```

计划提交前执行：

```bash
git diff --check
```

---

## 7. 状态

```text
PLAN ONLY。
等待主控确认后，才能进入 LG1 / 实现阶段。
```
