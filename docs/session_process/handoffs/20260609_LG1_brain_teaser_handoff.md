# LG1：脑筋急转弯 Demo 交接

日期：2026-06-09

执行角色：开发执行会话

状态：CODE PASS / 待合并真机验收

---

## 1. 本轮完成内容

已实现第一个可玩的语言小游戏：脑筋急转弯，并接入 LG0 已确认的聊天中游戏入口。

完成范围：

```text
1. 新增 Android 本地 LanguageGameSnapshot。
2. 新增 LanguageGameType。
3. 新增 BrainTeaserGameState。
4. 新增本地 5 题题库。
5. 新增 BrainTeaserEvaluator。
6. 接入 ChatViewModel。
7. 接入 ChildChatScreen。
8. 接入 voice-first 回答流程。
9. 脑筋急转弯进行中拦截普通 conversation。
10. “先聊别的”退出 languageGame 并恢复普通 conversation。
11. “换个游戏”回 GameMenu。
12. 奇怪小门进行中不触发语言游戏。
```

---

## 2. 关键行为

### 2.1 EntryPrompt

普通 opening 成功后，每个 `ChatViewModel` 生命周期最多自动显示一次：

```text
我们随便聊聊天
还是玩一个小游戏？
```

按钮：

```text
随便聊聊
玩个小游戏
```

点击“随便聊聊”后，本生命周期不再自动弹出语言游戏入口。

### 2.2 GameMenu

本轮菜单只显示：

```text
脑筋急转弯
先聊别的
```

不显示：

```text
词语接龙
猜谜语
```

原因：本轮不实现这两个游戏，避免出现不可点按钮。

### 2.3 脑筋急转弯

题库只包含主控确认的 5 题：

```text
1. 什么东西越洗越脏？ / 水 / 它常常在杯子里、河里、盆里
2. 什么门永远关不上？ / 球门 / 它常常在操场上
3. 什么东西越走越少？ / 路 / 你走过以后，它就被你走掉了一点点
4. 什么瓜不能吃？ / 傻瓜 / 它不是一种真的瓜
5. 什么布剪不断？ / 瀑布 / 它不是用来做衣服的布
```

答案判断只做包含主控答案原词，不做同义词扩展。

第 5 题后点击“下一题”，循环回第 1 题。

### 2.4 语音与 conversation 边界

```text
1. Question / Hint 状态下，ASR transcript 交给 BrainTeaserEvaluator。
2. 进入脑筋急转弯后，回答不发送普通 conversation。
3. DevSettings 文字调试输入也走同一套本地判断。
4. 退出语言游戏后，普通 conversation 恢复。
5. 孩子说“脑筋急转弯”直接进入 BrainTeaser。
6. 孩子说“玩游戏”进入 GameMenu。
7. 孩子说“词语接龙 / 接龙 / 猜谜语 / 谜语”进入 GameMenu。
```

---

## 3. 未做内容

```text
1. 未实现词语接龙。
2. 未实现猜谜语。
3. 未改后端。
4. 未新增 endpoint。
5. 未新增 GrowthEvent。
6. 未接小展台。
7. 未改奇怪小门。
8. 未新增家长端功能。
9. 未新增奖励、积分、等级、通关、任务或排行榜。
10. 未提交真实儿童测试材料。
```

---

## 4. 修改文件

新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameState.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/BrainTeaserQuestionBank.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/BrainTeaserEvaluator.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelLanguageGameTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/BrainTeaserEvaluatorTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/BrainTeaserQuestionBankTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModelTest.kt
docs/session_process/handoffs/20260609_LG1_brain_teaser_handoff.md
```

修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
```

---

## 5. 测试结果

已运行：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh testDebugUnitTest --tests "com.childai.companion.ui.chat.languagegame.*" --tests "com.childai.companion.ui.chat.ChatViewModelLanguageGameTest"
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
git diff --check
```

结果：

```text
1. doctor_local_env：通过；当前 adb 未连接真机。
2. LG1 相关 testDebugUnitTest：通过。
3. Android test：通过。
4. assembleDebug：通过。
5. git diff --check：通过。
```

测试覆盖：

```text
1. EntryPrompt 文案和按钮正确。
2. EntryPrompt 每个 ChatViewModel 生命周期最多自动出现一次。
3. “随便聊聊”后本生命周期不再自动弹出。
4. “玩个小游戏”进入 GameMenu。
5. GameMenu 只显示“脑筋急转弯 / 先聊别的”。
6. 不显示“词语接龙 / 猜谜语”。
7. 点击 / 触发“脑筋急转弯”进入第一题 Question。
8. 5 道题库内容与主控文本完全一致。
9. Question 状态下 ASR transcript 不发送普通 conversation。
10. transcript 包含答案关键词时进入 Correct。
11. transcript 不包含答案关键词时进入 Hint。
12. Hint 状态下再次回答，包含答案也能进入 Correct。
13. “给我提示”进入 Hint。
14. “告诉我答案”进入 Revealed。
15. “下一题”进入下一题，第 5 题后循环回第 1 题。
16. “换个游戏”回 GameMenu。
17. “先聊别的”退出 languageGame 并恢复普通 conversation。
18. strangeDoorDemo != null 时不触发语言游戏。
19. “脑筋急转弯 / 玩游戏 / 词语接龙 / 接龙 / 猜谜语 / 谜语”关键词路由。
20. 禁止词测试覆盖入口、菜单、题库、反馈、按钮。
```

---

## 6. 风险与后续验收

```text
1. 当前未做真机视觉 / 语音按钮体感验收。
2. “我来答 / 我再猜”已复用现有语音入口，但仍需要真机验证录音权限、按钮状态和 ASR 返回后的本地判断体感。
3. EntryPrompt 在普通 opening 后出现，未做“连续短句 / 不知道聊什么”触发。
4. 词语接龙和猜谜语本轮不显示；后续 LG2 / LG3 实现后再加入菜单。
```

结论：

```text
需要合并真机验收。
```
