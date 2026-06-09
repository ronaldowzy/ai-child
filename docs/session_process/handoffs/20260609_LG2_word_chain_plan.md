# LG2：词语接龙 Demo 计划

日期：2026-06-09

执行角色：开发执行会话

状态：PLAN ONLY / 待主控确认

---

## 1. 本轮结论

LG2 建议在 LG1 已落地的 `LanguageGameSnapshot` 架构上新增词语接龙 Demo。

本轮计划只覆盖实现方案，不编码、不改题库、不改后端。

实现方向：

```text
1. 复用 ChatViewModel 内的 languageGame 本地状态。
2. 复用现有 EntryPrompt / GameMenu。
3. GameMenu 增加“词语接龙”，仍不显示“猜谜语”。
4. 新增 WordChain 本地状态、词库和本地 evaluator。
5. 词语接龙进行中拦截普通 conversation。
6. 不新增 GrowthEvent，不接小展台，不改奇怪小门。
```

当前代码中 `LanguageGameType.WordChain` 已有枚举占位，LG2 实现时不需要重复新增枚举值，只需要接入对应状态、UI 和 reducer。

---

## 2. 计划问题逐项回答

### 1. 是否复用 LG1 的 LanguageGameSnapshot

复用。

建议在现有 `LanguageGameSnapshot` 中新增词语接龙运行态字段：

```kotlin
val wordChain: WordChainSnapshot? = null
```

保留现有字段：

```kotlin
state
selectedType
brainTeaser
autoPromptShown
dismissedForLifecycle
```

这样 LG2 仍是 Android 本地轻状态，不引入新 ViewModel、不做导航级游戏页面。

### 2. 是否新增 LanguageGameType.WordChain

当前代码已经存在：

```kotlin
LanguageGameType.WordChain
```

LG2 只需要启用它。

如果实现分支意外缺少该枚举，再按主控确认补齐；不新增其它游戏类型。

### 3. 是否新增 WordChainGameState

需要。

建议新增：

```kotlin
enum class WordChainGameState {
    Start,
    ChildTurn,
    Correct,
    Hint,
    FoxTurn,
    Finished,
}
```

建议新增运行态：

```kotlin
data class WordChainSnapshot(
    val previousWord: String,
    val roundIndex: Int,
    val missCount: Int,
    val gameState: WordChainGameState,
    val childWord: String? = null,
    val foxWord: String? = null,
)
```

说明：

```text
1. previousWord 是当前要接的上一个词。
2. roundIndex 最多推进到 5。
3. missCount 用于连续没接上后的降难度。
4. childWord / foxWord 只存在当前 ViewModel 内存态，不落库、不写后端。
```

### 4. 词语接龙词库放在哪个文件

建议新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/WordChainWordBank.kt
```

职责：

```text
1. 存放主控确认的起始词。
2. 存放主控确认的小白狐安全接词词池。
3. 暴露 approvedChildFacingCopy，纳入禁止词测试。
4. 不从后端拉取词库。
5. 不调用模型生成词语。
```

判断逻辑建议放入：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/WordChainEvaluator.kt
```

### 5. 如何设计儿童安全词库

词库原则：

```text
1. 生活化，5-10 岁儿童能懂。
2. 避免“子 / 了 / 的 / 儿”等难接尾字作为小白狐主动给出的下一轮尾字。
3. 避免暴力、惊吓、医疗、隐私、学校压力和学习考核感词语。
4. 不使用成语，不做成语接龙。
5. 不追求完整真实词典，只做首版 Demo 的安全固定词池。
6. 未经主控确认的候选词不进入代码。
```

开发方建议的首版词库方案是“固定安全词池 + 难尾字兜底”，待主控确认后再实现。

建议优先确认以下稳定接龙链：

```text
苹果 -> 果汁 -> 汁水 -> 水池 -> 池塘 -> 塘边
月亮 -> 亮光 -> 光点 -> 点心 -> 心愿 -> 愿望
小猫 -> 猫毛 -> 毛笔 -> 笔盒 -> 盒饭 -> 饭团
大树 -> 树枝 -> 枝条 -> 条纹 -> 纹路 -> 路灯
水杯 -> 杯口 -> 口琴 -> 琴声 -> 声音 -> 音乐
```

说明：

```text
1. “苹果”来自主控示例，虽然不在“起始词候选 1-5”列表中，但稳定性最好。
2. “月亮 / 小猫 / 大树 / 水杯”来自主控推荐候选。
3. “云朵”的尾字“朵”可接生活词较少，建议不作为默认起始词，除非主控补充安全词。
4. 上述词库只是候选方案，需主控确认后才能进入代码。
```

### 6. 如何避免难接尾字

实现侧建议做三层处理：

```text
1. 小白狐主动给出的词，优先选择尾字容易接的词。
2. 如果孩子接上的词尾字没有安全接词，仍判定孩子接上，但下一步从安全词池切回容易词。
3. 连续 2 次没接上时，小白狐自动帮接并降低难度。
```

不使用以下方式：

```text
1. 不现场编词。
2. 不查后端词典。
3. 不调用模型生成。
4. 不说孩子失败。
5. 不做惩罚式结束。
```

### 7. 如何处理孩子语音 transcript

词语接龙进行中，ASR transcript 走本地 evaluator。

建议规则：

```text
1. 去掉空白、标点和明显语气词。
2. 提取 transcript 中第一个有效汉字作为 firstChar。
3. 提取第一个连续汉字片段作为 childWord，用于展示“{previous}”接“{childWord}”。
4. childWord 只保存在当前 languageGame 内存态。
5. 不发送普通 conversation。
6. 不落库，不写 GrowthEvent，不写小展台。
```

如果 transcript 为空或没有有效汉字，按没接上处理，但不说“我没听懂”。

### 8. WordChain 进行中是否拦截普通 conversation

是。

规则：

```text
1. WordChain 的 Start / ChildTurn / Hint 状态下，孩子语音优先交给 WordChainEvaluator。
2. WordChain 进行中，不发送普通 conversation。
3. “换个游戏”回 GameMenu。
4. “先聊别的”清空 languageGame 后恢复普通 conversation。
5. 退出后孩子下一句再按普通聊天处理。
```

### 9. 如何判断接上

按主控规则：

```text
1. 取 previousWord 的最后一个有效汉字 lastChar。
2. 取孩子 transcript 的第一个有效汉字 firstChar。
3. firstChar == lastChar，则接上。
4. firstChar != lastChar，则进入温柔提示。
```

判断只看汉字，不做拼音、近音、同义词扩展。

### 10. 是否校验真实词语

不校验。

LG2 不查词典、不调用后端、不判断孩子说的是不是标准词。

原因：

```text
1. 主控要求首版不校验真实词语。
2. 低龄孩子可能说出有想象力的词。
3. 本轮目标是连续玩几轮，不是学习纠错。
```

### 11. 小白狐如何自动接词

小白狐只从主控确认的 `WordChainWordBank` 中接词。

建议顺序：

```text
1. 孩子接上后，取 childWord 最后一个有效汉字。
2. 在安全词池中找一个以该字开头的 foxWord。
3. 找到后进入 FoxTurn，展示：
   我来接一个
   “{previous}”接“{foxWord}”
4. 若没有安全 foxWord，不现场编词，切换到容易词。
```

为了避免新增“继续”按钮，UI 可以把接上反馈和小白狐帮接反馈合并在一次结果页中展示：

```text
接上啦
“{previous}”接“{childWord}”
这个小词跑得还挺快

我来接一个
“{childWord}”接“{foxWord}”
```

随后按钮仍使用：

```text
我来接
换个游戏
先聊别的
```

### 12. 连续没接上如何降难度

建议：

```text
1. 第一次没接上：进入 Hint，展示主控提示文案。
2. 第二次连续没接上：仍展示温柔提示，同时内部切到更容易的 previousWord。
3. missCount 清零。
4. 不增加分数、失败次数、惩罚或通关表达。
```

可复用主控允许文案：

```text
这个词也可以玩
不过这次要从“{lastChar}”开始
我给你换个容易的
```

不新增“你不会”“再认真一点”等表达。

### 13. 最多几轮

最多 5 轮。

建议定义：

```text
1. 一次孩子接上并由小白狐接出下一个词，算 1 轮有效推进。
2. 小白狐连续没接上后的自动帮接，也可以算 1 轮辅助推进。
3. 没接上但还在提示状态，不单独计轮。
```

该计数方式需要主控确认。

### 14. 第 5 轮后如何收束

第 5 轮后进入 `WordChainGameState.Finished`。

只展示主控允许文案：

```text
我们已经接了好多小词
先让它们排队休息一下
```

按钮：

```text
再玩一次
换个游戏
先聊别的
```

点击“再玩一次”只重置当前 WordChain 状态，不重置 BrainTeaser，不触碰奇怪小门和小展台。

### 15. GameMenu 如何加入词语接龙

LG2 实现后，GameMenu 改为显示：

```text
脑筋急转弯
词语接龙
先聊别的
```

按钮顺序按主控范围执行。

点击“词语接龙”进入 `LanguageGameType.WordChain` 的起始状态。

### 16. 是否仍不显示猜谜语

是。

LG2 不显示：

```text
猜谜语
```

原因：

```text
1. LG2 不实现猜谜语。
2. 不显示不可点按钮，避免挫败。
3. 保持 LG1 已采用的体验原则。
```

### 17. 如何退出普通聊天

使用主控确认按钮：

```text
先聊别的
```

行为：

```text
1. languageGame = null。
2. 设置本生命周期 dismissed 标记，避免自动再次弹 EntryPrompt。
3. 普通 opening / conversation 恢复。
4. 不写后端，不写本地文件。
```

### 18. 如何换回 GameMenu

使用按钮：

```text
换个游戏
```

行为：

```text
1. 当前 WordChain 运行态清空。
2. languageGame.state = GameMenu。
3. GameMenu 显示“脑筋急转弯 / 词语接龙 / 先聊别的”。
4. 不自动开始其它游戏。
```

### 19. 如何保证奇怪小门优先

沿用 LG1 规则：

```text
1. strangeDoorDemo != null 时，不自动显示语言游戏入口。
2. strangeDoorDemo != null 时，语言游戏关键词不触发。
3. showLanguageGameSnapshot 继续检查 strangeDoorDemo。
4. 奇怪小门退出后，才允许语言游戏入口。
```

LG2 不改奇怪小门任何状态、门节奏、拍照、小展台或视觉逻辑。

### 20. 会修改哪些文件

如果主控批准 LG2 实现，预计修改：

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
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/WordChainWordBank.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/WordChainEvaluator.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/WordChainWordBankTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/WordChainEvaluatorTest.kt
docs/session_process/handoffs/20260609_LG2_word_chain_handoff.md
```

本轮计划只新增：

```text
docs/session_process/handoffs/20260609_LG2_word_chain_plan.md
```

### 21. 不会修改哪些文件

LG2 不修改：

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

LG2 不改：

```text
1. LG1 脑筋急转弯题库。
2. 猜谜语。
3. 奇怪小门 D3 / D4 / D5 / S2 / S3 / S4 / S5 路径。
4. 小展台列表详情。
5. 小展台保存能力。
6. 后端 endpoint。
7. GrowthEvent 类型。
8. 家长端功能。
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
1. GameMenu 显示“脑筋急转弯 / 词语接龙 / 先聊别的”。
2. GameMenu 不显示“猜谜语”。
3. 点击“词语接龙”进入 WordChain 起始状态。
4. WordChain 起始说明使用主控文案。
5. “我来接”触发语音优先回答流程。
6. WordChain ChildTurn 下 ASR transcript 不发送普通 conversation。
7. 第一个有效汉字等于 previousWord 最后一个字时进入 Correct / FoxTurn。
8. 第一个有效汉字不匹配时进入 Hint。
9. 不校验真实词语。
10. 小白狐只从确认词库接词。
11. 难接尾字不现场编词。
12. 连续 2 次没接上后降低难度。
13. 最多 5 轮后进入 Finished。
14. Finished 显示主控结束文案。
15. “再玩一次”只重置 WordChain。
16. “换个游戏”回 GameMenu。
17. “先聊别的”退出 languageGame 并恢复普通 conversation。
18. “词语接龙 / 接龙”关键词进入 WordChain，前提是主控确认更新 LG1 路由。
19. “猜谜语 / 谜语”仍进入 GameMenu 或不暴露猜谜语，按主控确认执行。
20. strangeDoorDemo != null 时不触发语言游戏。
21. BrainTeaser 现有题库和循环逻辑不变。
22. 禁止词测试覆盖词语接龙入口、反馈、结束、按钮和确认词库。
23. D3 / D4 / D5 / S2 / S3 / S4 / S5 回归不破。
24. assembleDebug 通过。
```

本轮计划阶段只需检查文档 diff 和敏感信息，不运行 Android 构建。

### 23. 需要主控确认的问题

见本文第 4 节。

---

## 3. 儿童端文案边界

LG2 只使用主控允许文案。

入口：

```text
词语接龙
```

规则说明：

```text
我们玩词语接龙
我先说一个词
你接一个从“{lastChar}”开始的词就行
```

接上反馈：

```text
接上啦
“{previous}”接“{childWord}”
这个小词跑得还挺快
```

没接上反馈：

```text
这个词也可以玩
不过这次要从“{lastChar}”开始
我给你换个容易的
```

小白狐帮接：

```text
我来接一个
“{previous}”接“{foxWord}”
```

结束：

```text
我们已经接了好多小词
先让它们排队休息一下
```

按钮：

```text
我来接
换个游戏
先聊别的
再玩一次
```

本轮计划不使用可选按钮：

```text
给我一个提示
```

原因：没接上反馈已经承担轻提示作用，增加该按钮会让玩法更像练习。

---

## 4. 需要主控确认的问题

```text
1. 是否确认 LG2 GameMenu 只显示“脑筋急转弯 / 词语接龙 / 先聊别的”，继续不显示“猜谜语”？
2. 是否确认孩子说“词语接龙 / 接龙”后直接进入 WordChain，而不是停在 GameMenu？
3. 是否确认“猜谜语 / 谜语”在 LG2 阶段仍回 GameMenu，不直接进入未实现内容？
4. 是否确认首版默认起始词优先使用“苹果”或“月亮”，而不是从五个候选中随机？
5. 是否确认开发方提出的候选安全词库，或由主控提供最终词库？
6. 是否确认“云朵”暂不作为默认起始词，除非补充“朵”开头的低龄安全词？
7. 是否确认连续 2 次没接上后，小白狐自动帮接并切到更容易词？
8. 是否确认最多 5 轮按“有效推进轮”计数，而不是按所有回答次数计数？
9. 是否确认 LG2 不使用“给我一个提示”按钮？
10. 如果孩子接上的词尾字没有安全接词，是否允许内部切回容易词，避免现场编词？
```
