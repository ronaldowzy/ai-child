# LG3：猜谜语 Demo 交接

日期：2026-06-09

执行角色：开发执行会话

状态：CODE PASS / 待合并真机验收

---

## 1. 本轮完成内容

已在 LG1 / LG2 语言游戏架构下实现第三个可玩的语言小游戏：猜谜语。

完成范围：

```text
1. 复用 LanguageGameSnapshot。
2. 启用 LanguageGameType.Riddle。
3. 新增 RiddleGameState。
4. 新增 RiddleSnapshot。
5. 新增 RiddleQuestionBank。
6. 新增 RiddleEvaluator。
7. GameMenu 加入“猜谜语”。
8. Riddle 进行中拦截普通 conversation。
9. “换个游戏”返回 GameMenu。
10. “先聊别的”退出 languageGame 并恢复普通聊天。
11. strangeDoorDemo != null 时不触发 Riddle。
```

---

## 2. 关键行为

### 2.1 GameMenu

LG3 后菜单显示：

```text
脑筋急转弯
词语接龙
猜谜语
先聊别的
```

### 2.2 关键词路由

```text
1. 孩子说“玩游戏”：进入 GameMenu。
2. 孩子说“脑筋急转弯”：直接进入 BrainTeaser。
3. 孩子说“词语接龙 / 接龙”：直接进入 WordChain。
4. 孩子说“猜谜语 / 谜语”：直接进入 Riddle。
5. 奇怪小门进行中：不触发语言游戏。
```

### 2.3 猜谜语规则

```text
1. 第一题固定从题 1 开始，不随机。
2. 小白狐展示“我们来猜一个小谜语”加多行谜面。
3. transcript 只用于当前本地判断。
4. 只做答案原词包含判断。
5. 不做同义词、拼音、近音或模糊语义。
6. 不查词典，不调用模型，不让后端判断。
7. 不保存孩子原始回答，不写 GrowthEvent。
8. 第 5 题后点击“下一题”循环回第 1 题。
```

### 2.4 题库

只写入主控确认的 5 题：

```text
1. 小小房子圆又圆 / 里面住着甜甜水 / 橘子 / 它是一种水果，剥开以后可以一瓣一瓣吃
2. 白白一片天上走 / 有时像羊有时像狗 / 云 / 它在天上，会慢慢变形
3. 肚子大大装书本 / 每天跟你一起出门 / 书包 / 上学或出门时，常常背在身上
4. 一根小棍黑又尖 / 走到纸上留下线 / 铅笔 / 它可以在纸上画画写字
5. 晚上出来眨眼睛 / 天一亮就躲起来 / 星星 / 它常常在夜晚的天上
```

未写入旧设计文档里的其它谜题。

### 2.5 状态与按钮

Question：

```text
我来猜
给我提示
换个游戏
先聊别的
```

Hint：

```text
我来猜
告诉我答案
换个游戏
先聊别的
```

Correct / Revealed：

```text
下一题
换个游戏
先聊别的
```

未新增：

```text
再玩一次
换一题
我猜到了
这个小游戏先玩到这里
随便聊聊
```

---

## 3. 修改文件

新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/RiddleQuestionBank.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/RiddleEvaluator.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/RiddleQuestionBankTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/RiddleEvaluatorTest.kt
docs/session_process/handoffs/20260609_LG3_riddle_handoff.md
```

修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameState.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelLanguageGameTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModelTest.kt
```

---

## 4. 未做内容

```text
1. 未改 LG1 脑筋急转弯题库和判断。
2. 未改 LG2 词语接龙词库和判断。
3. 未复用或修改 StrangeDoorRiddleEvaluator。
4. 未修改奇怪小门怪问题路径。
5. 未改后端。
6. 未新增 endpoint。
7. 未新增 GrowthEvent。
8. 未接小展台。
9. 未新增家长端功能。
10. 未新增分数、等级、奖励、连续答对、排行榜、通关、任务或学习入口。
11. 未提交真实儿童测试材料。
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
2. LG3 相关 testDebugUnitTest：通过。
3. Android test：通过。
4. assembleDebug：通过。
5. git diff --check：通过。
```

测试覆盖：

```text
1. GameMenu 显示“脑筋急转弯 / 词语接龙 / 猜谜语 / 先聊别的”。
2. 点击 / 触发“猜谜语”进入 Riddle 第一题 Question。
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
20. 禁止词测试覆盖猜谜语入口、题库、提示、反馈和按钮。
```

---

## 6. 风险与后续验收

```text
1. 当前未做真机语音按钮体感验收。
2. 猜谜语依赖 ASR transcript，真机需验证“我来猜”按钮录音、停止、回填后的本地判断是否顺畅。
3. 答案判断只认原词；孩子说近义描述时会进入提示，这是本轮主控确认的边界。
4. 语言游戏 Riddle 和奇怪小门“动脑试试”已保持代码隔离，但真机 QA 仍需验证奇怪小门进行中不会误进语言游戏。
```

结论：

```text
需要合并真机验收。
```
