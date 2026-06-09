# LG3：猜谜语 Demo 计划

日期：2026-06-09

执行角色：开发执行会话

状态：PLAN ONLY / 待主控确认

---

## 1. 本轮结论

LG3 建议在 LG1 / LG2 已落地的 `LanguageGameSnapshot` 架构下新增第三个可玩的语言小游戏：猜谜语。

本轮只输出计划，不编码、不新增题库文件、不改现有游戏代码。

实现方向：

```text
1. 复用现有 ChatViewModel 内的 languageGame 本地状态。
2. 启用现有 LanguageGameType.Riddle。
3. 新增 RiddleGameState、RiddleSnapshot、本地谜题库和本地 evaluator。
4. GameMenu 增加“猜谜语”，显示三项游戏和“先聊别的”。
5. 猜谜语进行中拦截普通 conversation。
6. 不复用、不修改奇怪小门 StrangeDoorRiddleEvaluator。
7. 不改后端、不新增 GrowthEvent、不接小展台、不改家长端。
```

阅读结论：

```text
1. PD-060 已确认语言游戏是聊天中的轻选择，不是首页大功能区或复杂游戏系统。
2. LG1 已完成 BrainTeaser，本地包含判断和 5 题循环。
3. LG2 已完成 WordChain，本地接龙判断、固定词链和菜单中的“词语接龙”。
4. 旧设计文档中的猜谜语样例与本轮 LG3 主控题库不完全一致；LG3 实现必须以本轮主控给出的 5 题为准。
```

---

## 2. 计划问题逐项回答

### 1. 是否复用 LG1/LG2 的 LanguageGameSnapshot

复用。

建议在现有 `LanguageGameSnapshot` 中新增：

```kotlin
val riddle: RiddleSnapshot? = null
```

保持现有入口、菜单和游戏状态同属 Android 本地 `languageGame`，不新增页面级 ViewModel，不新增后端状态。

### 2. 是否启用 LanguageGameType.Riddle

启用。

当前代码中 `LanguageGameType.Riddle` 已存在占位。LG3 实现时只需要把该类型接入 reducer、UI model、ChatViewModel 和测试。

如果目标分支实现时发现枚举缺失，再按主控确认补齐；不新增其它游戏类型。

### 3. 是否新增 RiddleGameState

需要。

建议新增：

```kotlin
enum class RiddleGameState {
    Question,
    Hint,
    Correct,
    Revealed,
}
```

说明：

```text
1. Question：展示开场和谜面，等待孩子语音回答。
2. Hint：展示提示反馈，孩子可以继续猜或要求揭晓。
3. Correct：孩子猜中后的反馈。
4. Revealed：孩子点击“告诉我答案”后的揭晓反馈。
```

不建议新增 Finished，因为主控明确第 5 题后“下一题”循环回第 1 题，不做结束页、不做通关。

### 4. 是否新增 RiddleSnapshot

需要。

建议新增：

```kotlin
data class RiddleSnapshot(
    val questionIndex: Int = 0,
    val gameState: RiddleGameState = RiddleGameState.Question,
)
```

首版不保存孩子原始回答，不保存猜测历史，不写后端、不写本地文件、不写 GrowthEvent。

### 5. 谜题库放在哪个本地文件

建议新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/RiddleQuestionBank.kt
```

建议结构：

```kotlin
data class RiddleQuestion(
    val lines: List<String>,
    val answer: String,
    val hint: String,
)
```

判断逻辑建议新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/RiddleEvaluator.kt
```

与奇怪小门包内 `StrangeDoorRiddleEvaluator` 分离，避免两个“谜语 / 怪问题”路径互相污染。

### 6. 是否只写入主控确认的 5 题

是。

LG3 只写入本轮主控确认的 5 题：

```text
1. 小小房子圆又圆 / 里面住着甜甜水 / 橘子 / 它是一种水果，剥开以后可以一瓣一瓣吃
2. 白白一片天上走 / 有时像羊有时像狗 / 云 / 它在天上，会慢慢变形
3. 肚子大大装书本 / 每天跟你一起出门 / 书包 / 上学或出门时，常常背在身上
4. 一根小棍黑又尖 / 走到纸上留下线 / 铅笔 / 它可以在纸上画画写字
5. 晚上出来眨眼睛 / 天一亮就躲起来 / 星星 / 它常常在夜晚的天上
```

不写入旧设计文档里未被本轮确认的其它谜面，不新增备选题，不新增随机题。

### 7. 如何处理多行谜面

建议在 `RiddleQuestion.lines` 中存为多行列表。

UI model 展示时：

```text
1. 第一行显示“我们来猜一个小谜语”。
2. 后面按原顺序显示谜面每一行。
```

示例：

```text
我们来猜一个小谜语
小小房子圆又圆
里面住着甜甜水
```

不把多行谜面拼成一行，避免手机上阅读拥挤。

### 8. 如何处理孩子语音 transcript

Riddle 进行中，ASR transcript 只交给本地 `RiddleEvaluator`。

规则：

```text
1. transcript 只用于当前本地判断。
2. 不保存孩子原始回答。
3. 不写 GrowthEvent。
4. 不写聊天历史。
5. 不发送普通 conversation。
6. 不调用后端。
7. DevSettings 文字调试入口如果已有，走同一套本地判断。
```

如果 transcript 为空或不包含答案原词，按提示反馈处理，但不说“我没听懂”。

### 9. Riddle 进行中是否拦截普通 conversation

是。

建议：

```text
1. Riddle Question / Hint 状态下，孩子语音回答交给 RiddleEvaluator。
2. Riddle Correct / Revealed 状态下，只响应“下一题 / 换个游戏 / 先聊别的”等按钮或明确命令。
3. Riddle 进行中不发送普通 conversation。
4. 点击“先聊别的”后清空 languageGame，再恢复普通 conversation。
```

### 10. 如何判断猜中

本地判断：

```text
transcript.contains(answer)
```

建议实现前先做轻量归一化：

```text
1. 去掉空白和常见标点。
2. 保留汉字原词。
3. 不做同义词、拼音、近音或模糊匹配。
```

例如：

```text
“我猜是橘子” -> 包含“橘子” -> 猜中
“水果” -> 不包含“橘子” -> 提示
```

### 11. 是否只做答案原词包含判断

是。

不做：

```text
1. 同义词。
2. 拼音。
3. 近音。
4. 模糊语义。
5. 词典查询。
6. 模型判断。
7. 后端判断。
```

### 12. 如何进入提示

两种进入方式：

```text
1. Question / Hint 状态下，孩子回答不包含答案原词。
2. 孩子点击“给我提示”。
```

提示反馈只使用主控文案：

```text
这个想法也挺像
我再给你一点提示
{hint}
```

不新增“没猜中”“再认真一点”等表达。

### 13. 如何告诉答案

Hint 或 Question 状态都可以点击：

```text
告诉我答案
```

进入 `RiddleGameState.Revealed`，展示：

```text
我悄悄告诉你
谜底是{answer}
是不是藏得有点好？
```

不使用“正确答案”表达。

### 14. 第 5 题后如何处理

第 5 题后点击：

```text
下一题
```

循环回第 1 题。

不做：

```text
1. 结束页。
2. 通关。
3. 奖励。
4. 分数。
5. 连续答对。
```

### 15. GameMenu 如何加入“猜谜语”

LG3 实现后，GameMenu 显示：

```text
脑筋急转弯
词语接龙
猜谜语
先聊别的
```

点击“猜谜语”进入 `LanguageGameState.Riddle` 的第一题 Question。

### 16. 如何保证 LG1 / LG2 不变

实现边界：

```text
1. 不修改 BrainTeaserQuestionBank 的 5 题。
2. 不修改 BrainTeaserEvaluator 的包含判断。
3. 不修改 BrainTeaser 的第 5 题循环逻辑。
4. 不修改 WordChainWordBank 的 5 条词链。
5. 不修改 WordChainEvaluator 的首汉字判断。
6. 不修改 WordChain 的最多 5 轮和重玩轮换规则。
```

只在公共菜单、公共 reducer 和公共 UI action 分发中接入 Riddle 分支。

### 17. 如何保证奇怪小门 riddle path 不变

明确隔离：

```text
1. 不复用 StrangeDoorRiddleEvaluator。
2. 不修改 StrangeDoorRiddleEvaluator。
3. 不修改 StrangeDoorDemoState。
4. 不修改 StrangeDoorDoorStateReducer。
5. 不修改 StrangeDoorHomeEventUiModel。
6. 不修改奇怪小门“动脑试试”固定怪问题。
7. 不修改门状态、门节奏、拍照、小展台回到小门路径。
```

ChatViewModel 入口层继续保持：

```text
strangeDoorDemo != null 时，不触发 languageGame。
```

### 18. 如何退出普通聊天

继续使用：

```text
先聊别的
```

行为：

```text
1. languageGame = null。
2. 设置本生命周期 dismissed 标记，避免 EntryPrompt 反复自动出现。
3. 恢复普通 conversation。
4. 不保存游戏状态。
5. 不写后端。
```

### 19. 如何换回 GameMenu

使用：

```text
换个游戏
```

行为：

```text
1. 清空当前 Riddle 运行态。
2. 回到 GameMenu。
3. 菜单显示 BrainTeaser / WordChain / Riddle / 先聊别的。
4. 不自动开始其它游戏。
```

### 20. 会修改哪些文件

如果主控批准 LG3 实现，预计修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameState.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelLanguageGameTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModelTest.kt
```

预计新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/RiddleQuestionBank.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/RiddleEvaluator.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/RiddleQuestionBankTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/RiddleEvaluatorTest.kt
docs/session_process/handoffs/20260609_LG3_riddle_handoff.md
```

本轮计划只新增：

```text
docs/session_process/handoffs/20260609_LG3_riddle_plan.md
```

### 21. 不会修改哪些文件

LG3 不修改：

```text
backend/
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/
android/app/src/main/java/com/childai/companion/ui/showcase/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/data/growth/
android/app/src/main/java/com/childai/companion/ui/parent/
android/app/src/main/res/drawable-nodpi/
docs/assets/
```

LG3 不改：

```text
1. LG1 脑筋急转弯题库和判断。
2. LG2 词语接龙词库和判断。
3. 奇怪小门怪问题路径。
4. 小展台列表详情和保存路径。
5. 后端 endpoint。
6. GrowthEvent 类型。
7. 家长端功能。
```

### 22. 测试策略

实现后建议运行：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh testDebugUnitTest --tests "com.childai.companion.ui.chat.languagegame.*" --tests "com.childai.companion.ui.chat.ChatViewModelLanguageGameTest"
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
git diff --check
```

新增或更新测试覆盖：

```text
1. GameMenu 显示“脑筋急转弯 / 词语接龙 / 猜谜语 / 先聊别的”。
2. 点击“猜谜语”进入 Riddle 第一题 Question。
3. “猜谜语 / 谜语”关键词直接进入 Riddle。
4. “玩游戏 / 脑筋急转弯 / 词语接龙 / 接龙”现有路由不破。
5. Riddle 起始文案为“我们来猜一个小谜语”加多行谜面。
6. 5 题题库内容与主控文本完全一致。
7. Question 状态下 ASR transcript 不发送普通 conversation。
8. transcript 包含答案原词时进入 Correct。
9. transcript 不包含答案原词时进入 Hint。
10. Hint 状态下再次回答，包含答案也能进入 Correct。
11. “给我提示”进入 Hint。
12. “告诉我答案”进入 Revealed。
13. Correct / Revealed 点击“下一题”进入下一题。
14. 第 5 题后“下一题”循环回第 1 题。
15. “换个游戏”回 GameMenu。
16. “先聊别的”退出 languageGame 并恢复普通 conversation。
17. strangeDoorDemo != null 时不触发 Riddle。
18. BrainTeaser 现有题库和循环逻辑不变。
19. WordChain 现有词库、5 轮结束和重玩轮换不变。
20. 不修改 StrangeDoorRiddleEvaluator 相关测试。
21. 禁止词测试覆盖猜谜语入口、题库、提示、反馈和按钮。
22. D3 / D4 / D5 / S2 / S3 / S4 / S5 / LG1 / LG2 回归不破。
23. assembleDebug 通过。
```

本轮计划阶段已运行：

```bash
bash scripts/doctor_local_env.sh
```

结果：通过；当前 adb 未连接真机。

计划阶段还会执行文档 diff 与敏感信息扫描，不运行 Android 构建。

### 23. 需要主控确认的问题

见本文第 4 节。

---

## 3. 儿童端文案边界

LG3 只使用主控允许文案。

菜单：

```text
猜谜语
```

开场：

```text
我们来猜一个小谜语
```

答中反馈：

```text
猜到啦
就是{answer}
小白狐把这个谜底轻轻收好
```

没猜中 / 提示反馈：

```text
这个想法也挺像
我再给你一点提示
{hint}
```

告诉答案：

```text
我悄悄告诉你
谜底是{answer}
是不是藏得有点好？
```

按钮：

```text
我来猜
给我提示
告诉我答案
下一题
换个游戏
先聊别的
```

不新增：

```text
再玩一次
换一题
我猜到了
这个小游戏先玩到这里
随便聊聊
```

说明：这些文案来自旧设计或其它游戏，不在本轮 LG3 允许文案内。

---

## 4. 需要主控确认的问题

```text
1. 是否确认 GameMenu 在 LG3 后显示“脑筋急转弯 / 词语接龙 / 猜谜语 / 先聊别的”？
2. 是否确认“猜谜语 / 谜语”关键词在 LG3 后直接进入 Riddle，而不是停在 GameMenu？
3. 是否确认 Riddle 第一题固定从题 1 开始，不随机？
4. 是否确认第 5 题后“下一题”循环回第 1 题，不新增结束页？
5. 是否确认 Correct 状态按钮只显示“下一题 / 换个游戏 / 先聊别的”？
6. 是否确认 Revealed 状态按钮只显示“下一题 / 换个游戏 / 先聊别的”？
7. 是否确认 Hint 状态按钮显示“我来猜 / 告诉我答案 / 换个游戏 / 先聊别的”，不额外新增按钮？
8. 是否确认“给我提示”在 Question 状态可用，展示同一套提示反馈？
9. 是否确认空 transcript 或无答案原词时统一进入提示反馈，不新增兜底文案？
10. 是否确认 LG3 不复用奇怪小门的 StrangeDoorRiddleEvaluator，保持两条 riddle path 完全隔离？
```
