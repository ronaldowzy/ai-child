# LG0-A：语言游戏入口产品决策落档与最小入口实现计划

日期：2026-06-09

执行角色：开发执行会话

状态：PLAN ONLY / 产品决策已落档 / 待主控确认实现范围

---

## 1. 本轮结论

已将语言游戏入口方向写入产品决策：

```text
docs/PRODUCT_DECISIONS_V0_1.md
PD-060
```

LG0-A 只规划最小入口实现，不实现具体游戏内容、不写题库、不写游戏反馈、不新增后端。

建议下一步最小实现范围：

```text
1. 新增 Android 本地 LanguageGameSnapshot。
2. 新增 LanguageGameType：BrainTeaser / WordChain / Riddle。
3. 新增 languagegame 包承载状态、UI model 和禁止词测试。
4. 只实现 EntryPrompt 和 GameMenu。
5. GameMenu 三个游戏按钮本轮先 disabled，避免进入未确认游戏文案。
```

---

## 2. 计划问题逐项回答

### 1. 产品决策写入哪个文档

写入：

```text
docs/PRODUCT_DECISIONS_V0_1.md
```

新增决策：

```text
PD-060
```

### 2. 是否存在 docs/PRODUCT_DECISIONS_V0_1.md

存在。

本轮已读取并更新该文件。

### 3. 如果不存在，使用哪个现有产品决策文档

不适用。

因为 `docs/PRODUCT_DECISIONS_V0_1.md` 存在，且 `PD-008` 已确认“每次家长确认的新产品想法，必须先写入 `docs/PRODUCT_DECISIONS_V0_1.md`，再进入子会话实现”。

### 4. 最小入口实现是否只包含 EntryPrompt 和 GameMenu

建议是。

LG0-A 后续实现只做：

```text
1. EntryPrompt：显示聊天轻选择。
2. GameMenu：显示三个游戏选项和“先聊别的”。
3. 入口状态退出到普通聊天。
4. 奇怪小门优先级拦截。
```

不做具体游戏起始题目、提示、反馈、下一题、结束态。

### 5. 是否新增 LanguageGameSnapshot

建议新增。

建议结构只承载入口和菜单所需状态：

```text
LanguageGameSnapshot(
  state,
  selectedType,
  autoPromptShown,
  dismissedForLifecycle
)
```

字段命名以后续实现时的代码结构为准。

### 6. 是否新增 LanguageGameType

建议新增。

首版只允许：

```text
BrainTeaser
WordChain
Riddle
```

不加入其它候选游戏。

### 7. 是否新增 languagegame 包

建议新增 Android 本地包：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/
```

建议承载：

```text
LanguageGameState.kt
LanguageGameEntryUiModel.kt
```

测试包：

```text
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/
```

这样避免把语言游戏入口状态继续堆进奇怪小门包，也不污染小展台代码。

### 8. 是否只实现状态和 UI，不实现具体游戏题库

是。

后续最小入口实现只接：

```text
1. 状态；
2. UI model；
3. ChatViewModel 入口动作；
4. ChildChatScreen 入口展示；
5. 禁止词测试。
```

不实现：

```text
1. 脑筋急转弯题库；
2. 词语接龙词库；
3. 猜谜语题库；
4. 游戏判断；
5. 游戏反馈；
6. 游戏结束按钮。
```

### 9. 孩子点击具体游戏后，是否只进入占位起始状态

建议本轮不让孩子点击进入占位起始状态。

原因：

```text
1. 主控允许文案没有“准备中”或游戏占位文案。
2. 如果点击后进入占位状态，必须显示新的儿童端解释文案。
3. 开发方不得自行补写游戏内容或占位话术。
```

因此建议：

```text
1. GameMenu 三个游戏按钮先显示但 disabled。
2. 只验证菜单存在和按钮不可点。
3. 具体游戏点击行为留到 LG1 / LG2 / LG3 或主控确认占位文案后实现。
```

### 10. 占位起始状态是否只显示“这个小游戏还在准备中”，还是不允许点击

建议不允许点击。

不建议显示：

```text
这个小游戏还在准备中
```

原因：该文案不在本轮允许文案内。

### 11. 主控倾向：本轮只做入口和菜单，三个游戏按钮暂时可以 disabled，避免出现未确认游戏文案

建议按此执行。

本轮实现后，孩子可看到：

```text
我们随便聊聊天
还是玩一个小游戏？
随便聊聊
玩个小游戏
```

点击“玩个小游戏”后看到：

```text
想玩哪一个？
脑筋急转弯
词语接龙
猜谜语
先聊别的
```

其中三个游戏按钮 disabled，“先聊别的”可点击退出。

### 12. 会修改哪些文件

LG0-A 本轮已修改 / 新增：

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/session_process/handoffs/20260609_LG0A_language_game_entry_decision_plan.md
```

后续最小入口实现预计修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameState.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelLanguageGameEntryTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModelTest.kt
```

如当前 `ChatUiState` 定义独立在其它文件中，后续实现会按实际代码位置最小改动。

### 13. 不会修改哪些文件

LG0-A 不修改：

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

后续最小入口实现也不应修改：

```text
1. 后端 endpoint。
2. 奇怪小门 reducer / mapper / 视觉 / 门状态节奏。
3. 小展台列表详情和保存路径。
4. 家长端。
5. 素材资源。
```

### 14. 测试策略

LG0-A 本轮为文档和产品决策落档：

```bash
bash scripts/doctor_local_env.sh
git diff --check
```

后续最小入口实现建议测试：

```text
1. EntryPrompt 每个 ChatViewModel 生命周期最多自动出现一次。
2. 点“随便聊聊”后，本生命周期不再自动弹出游戏入口。
3. “玩个小游戏”进入 GameMenu。
4. GameMenu 标题为“想玩哪一个？”。
5. GameMenu 只包含：脑筋急转弯 / 词语接龙 / 猜谜语 / 先聊别的。
6. 三个游戏按钮 disabled。
7. “先聊别的”退出 languageGame 并恢复普通聊天。
8. strangeDoorDemo != null 时不触发语言游戏入口。
9. 奇怪小门退出后才允许 EntryPrompt。
10. 禁止词测试覆盖新增文案。
11. D3 / D4 / D5 / S2 / S3 / S4 / S5 回归不破。
12. assembleDebug 通过。
```

如果主控确认要实现具体游戏名语音触发，则还需测试：

```text
1. “玩游戏”进入 GameMenu。
2. “脑筋急转弯”进入 BrainTeaser 起始状态。
3. “词语接龙 / 接龙”进入 WordChain 起始状态。
4. “猜谜语 / 谜语”进入 Riddle 起始状态。
```

但这需要先确认可显示的游戏起始态文案，否则 LG0-A 不建议实现。

### 15. 需要主控确认的问题

```text
1. LG0-A 最小实现是否确认只做 EntryPrompt + GameMenu？
2. 三个游戏按钮本轮是否确认 disabled？
3. 既然游戏按钮 disabled，孩子语音说具体游戏名时是否也先不进入占位起始状态，等 LG1 / LG2 / LG3 再接？
4. 如果仍要求语音说具体游戏名直接进入起始状态，请主控提供每个起始状态允许显示的精确儿童端文案。
5. EntryPrompt 是否只在普通 opening 完成后自动出现，还是也可在孩子连续短句 / 不知道聊什么时出现？本轮建议只做 opening 后一次。
```

---

## 3. 已落档产品决策摘要

`PD-060` 已记录：

```text
1. 语言游戏是普通聊天中的轻选择入口。
2. 不做首页大功能区、学习入口或复杂游戏系统。
3. EntryPrompt 生命周期内最多自动出现一次。
4. 点“随便聊聊”后本生命周期不再自动弹出。
5. “玩游戏”进入 GameMenu。
6. 具体游戏名进入对应类型的起始状态。
7. 奇怪小门进行中不触发语言游戏。
8. 首版菜单只允许三个游戏。
9. 游戏内容由后续 LG1 / LG2 / LG3 确认。
10. 不改后端、不接小展台、不新增 GrowthEvent。
```

---

## 4. 允许文案

LG0-A 及后续最小入口实现仅允许：

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

禁止新增其它儿童端文案。

---

## 5. 状态

```text
PLAN ONLY。
产品决策已落档。
等待主控确认最小入口实现范围后再编码。
```
