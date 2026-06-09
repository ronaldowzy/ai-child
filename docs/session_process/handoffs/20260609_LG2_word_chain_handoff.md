# LG2：词语接龙 Demo 交接

日期：2026-06-09

执行角色：开发执行会话

状态：CODE PASS / 待合并真机验收

---

## 1. 本轮完成内容

已在 LG1 语言游戏架构下实现第二个可玩的语言小游戏：词语接龙。

完成范围：

```text
1. 复用 LanguageGameSnapshot。
2. 启用 LanguageGameType.WordChain。
3. 新增 WordChainGameState。
4. 新增 WordChainSnapshot。
5. 新增 WordChainWordBank。
6. 新增 WordChainEvaluator。
7. GameMenu 增加“词语接龙”。
8. WordChain 进行中拦截普通 conversation。
9. “换个游戏”返回 GameMenu。
10. “先聊别的”退出 languageGame 并恢复普通聊天。
11. strangeDoorDemo != null 时不触发语言游戏。
```

---

## 2. 关键行为

### 2.1 GameMenu

LG2 后菜单显示：

```text
脑筋急转弯
词语接龙
先聊别的
```

继续不显示：

```text
猜谜语
```

### 2.2 关键词路由

```text
1. 孩子说“玩游戏”：进入 GameMenu。
2. 孩子说“脑筋急转弯”：直接进入 BrainTeaser。
3. 孩子说“词语接龙 / 接龙”：直接进入 WordChain。
4. 孩子说“猜谜语 / 谜语”：进入 GameMenu，不进入未实现内容。
5. 奇怪小门进行中：不触发语言游戏。
```

### 2.3 词语接龙规则

```text
1. 默认起始词固定为“苹果”。
2. “再玩一次”按固定顺序轮换：苹果 -> 月亮 -> 小猫 -> 大树 -> 水杯 -> 苹果。
3. 取 previousWord 的最后一个有效汉字。
4. 取孩子 transcript 的第一个有效汉字。
5. 两者相同即接上。
6. 不校验真实词语。
7. 不查词典。
8. 不做拼音、近音、同义词扩展。
9. 不纠错、不评分。
```

### 2.4 词库

只写入主控确认的 5 条链：

```text
苹果 -> 果汁 -> 汁水 -> 水池 -> 池塘 -> 塘边
月亮 -> 亮光 -> 光点 -> 点心 -> 心愿 -> 愿望
小猫 -> 猫毛 -> 毛笔 -> 笔盒 -> 盒饭 -> 饭团
大树 -> 树枝 -> 枝条 -> 条纹 -> 纹路 -> 路灯
水杯 -> 杯口 -> 口琴 -> 琴声 -> 声音 -> 音乐
```

未写入：

```text
云朵
猜谜语题库
成语接龙词库
```

### 2.5 防卡住

```text
1. 第一次没接上：进入温柔提示。
2. 连续 2 次没接上：小白狐自动帮接，并推进 1 轮。
3. 如果孩子接上的词尾字没有安全接词，内部切回固定安全链。
4. 不现场编词。
5. 不调用模型。
6. 不查后端词典。
```

### 2.6 结束态

最多 5 轮按有效推进轮计数。

第 5 轮后显示：

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

---

## 3. 修改文件

新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/WordChainWordBank.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/WordChainEvaluator.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/WordChainWordBankTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/WordChainEvaluatorTest.kt
docs/session_process/handoffs/20260609_LG2_word_chain_handoff.md
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
1. 未实现猜谜语。
2. 未改 LG1 脑筋急转弯题库。
3. 未改后端。
4. 未新增 endpoint。
5. 未新增 GrowthEvent。
6. 未接小展台。
7. 未改奇怪小门。
8. 未新增家长端功能。
9. 未新增分数、等级、奖励、连续答对、排行榜、通关、任务或学习入口。
10. 未提交真实儿童测试材料。
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
2. LG2 相关 testDebugUnitTest：通过。
3. Android test：通过。
4. assembleDebug：通过。
5. git diff --check：通过。
```

测试覆盖：

```text
1. GameMenu 显示“脑筋急转弯 / 词语接龙 / 先聊别的”。
2. GameMenu 不显示“猜谜语”。
3. 点击“词语接龙”进入 WordChain 起始状态。
4. “词语接龙 / 接龙”关键词直接进入 WordChain。
5. “猜谜语 / 谜语”关键词进入 GameMenu。
6. WordChain 起始说明使用主控文案。
7. “我来接”复用语音优先回答流程。
8. WordChain 下 ASR transcript 不发送普通 conversation。
9. 第一个有效汉字等于 previousWord 最后一个字时进入接上反馈。
10. 第一个有效汉字不匹配时进入温柔提示。
11. 不校验真实词语。
12. 小白狐只从确认词库接词。
13. 难接尾字不现场编词。
14. 连续 2 次没接上后降低难度。
15. 最多 5 轮后进入 Finished。
16. Finished 显示主控结束文案。
17. “再玩一次”只重置 WordChain，并按固定顺序轮换起始词。
18. “换个游戏”回 GameMenu。
19. “先聊别的”退出 languageGame 并恢复普通 conversation。
20. strangeDoorDemo != null 时不触发语言游戏。
21. BrainTeaser 现有题库和循环逻辑不变。
22. 禁止词测试覆盖词语接龙入口、反馈、结束、按钮和确认词库。
```

---

## 6. 风险与后续验收

```text
1. 当前未做真机语音按钮体感验收。
2. 词语接龙依赖 ASR transcript，真机需验证“我来接”按钮录音、停止、回填后的本地判断是否顺畅。
3. 词库是固定 5 条链，孩子说出未覆盖尾字时会内部切回安全链，可能需要真机观察是否自然。
4. 继续不显示“猜谜语”，后续 LG3 实现后再加入菜单。
```

结论：

```text
需要合并真机验收。
```
