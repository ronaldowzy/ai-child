# LG1：脑筋急转弯 Demo 计划

日期：2026-06-09

执行角色：开发执行会话

状态：PLAN ONLY / 待主控确认

---

## 1. 本轮结论

LG1 直接实现第一个可玩的语言小游戏：脑筋急转弯，同时接入 LG0 已确认的聊天中游戏入口。

本轮不做：

```text
1. 词语接龙
2. 猜谜语
3. 后端改造
4. GrowthEvent
5. 小展台承接
6. 奇怪小门改造
```

LG0-A 中“只做 EntryPrompt + disabled GameMenu”的实现建议已被主控否定；LG1 计划按新确认执行：GameMenu 本轮只显示可玩的“脑筋急转弯”和“先聊别的”，不显示不可点的“词语接龙 / 猜谜语”。

---

## 2. 计划问题逐项回答

### 1. 是否基于 LG0-A 的 LanguageGameSnapshot

是。

建议沿用 LG0-A 的 Android 本地 snapshot 思路，但扩展为可承载脑筋急转弯回合：

```text
LanguageGameSnapshot(
  state,
  selectedType,
  brainTeaser,
  autoPromptShown,
  dismissedForLifecycle
)
```

其中 `autoPromptShown` 和 `dismissedForLifecycle` 只存在于 `ChatViewModel` 生命周期内，不写后端、不写本地文件、不进 GrowthEvent。

### 2. 是否新增 LanguageGameType.BrainTeaser

是。

首版 `LanguageGameType` 建议保留 LG0 确认的三个类型：

```text
BrainTeaser
WordChain
Riddle
```

但 LG1 只实现 `BrainTeaser`，其余类型不在 UI 暴露，不接点击行为。

### 3. 是否新增 BrainTeaserGameState

是。

建议新增脑筋急转弯本地状态：

```text
BrainTeaserGameState.Question
BrainTeaserGameState.Hint
BrainTeaserGameState.Correct
BrainTeaserGameState.Revealed
```

含义：

```text
Question：出题页，等待孩子回答。
Hint：未答对或点提示后显示提示，仍允许继续回答。
Correct：答对反馈页。
Revealed：点“告诉我答案”后的答案页。
```

### 4. 题库放在哪个本地文件

建议放在 Android 本地新包：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/BrainTeaserQuestionBank.kt
```

只包含主控确认的 5 题：

```text
1. 什么东西越洗越脏？ / 水 / 它常常在杯子里、河里、盆里
2. 什么门永远关不上？ / 球门 / 它常常在操场上
3. 什么东西越走越少？ / 路 / 你走过以后，它就被你走掉了一点点
4. 什么瓜不能吃？ / 傻瓜 / 它不是一种真的瓜
5. 什么布剪不断？ / 瀑布 / 它不是用来做衣服的布
```

不从后端拉题，不做模型生成，不扩展题库。

### 5. 如何处理语音 transcript

脑筋急转弯进行中，ASR transcript 先交给本地脑筋急转弯 evaluator。

规则：

```text
1. 如果当前 languageGame 是 BrainTeaser 且状态为 Question / Hint，则 transcript 不发送普通 conversation。
2. 对 transcript 做轻量本地归一化：trim、去常见标点、保留中文内容。
3. 判断是否包含当前题 answer 关键词。
4. 包含则进入 Correct。
5. 不包含则进入 Hint。
6. transcript 只用于本地即时判断，不写后端、不写 GrowthEvent、不保存额外历史。
```

### 6. 脑筋急转弯进行中是否拦截普通 conversation

是。

只在 BrainTeaser 的可回答状态拦截：

```text
Question
Hint
```

在这些状态下：

```text
1. 语音 transcript 不走普通 conversation。
2. DevSettings 下如果仍有文字调试输入，也按同样规则先交给本地 evaluator。
3. 点击“先聊别的”后清空 languageGame，下一句再恢复普通 conversation。
```

### 7. 如何退出到普通聊天

统一使用：

```text
先聊别的
```

行为：

```text
1. 清空 languageGame。
2. 设置本生命周期 dismissed 标记，避免 EntryPrompt 立即再次弹出。
3. 不清空普通聊天历史。
4. 不请求后端。
5. 后续孩子说话恢复普通 conversation。
```

### 8. 如何换回 GameMenu

统一使用：

```text
换个游戏
```

行为：

```text
1. languageGame.state 回到 GameMenu。
2. 不重置 EntryPrompt 的生命周期标记。
3. 不进入普通 conversation。
4. 本轮 GameMenu 只显示“脑筋急转弯 / 先聊别的”。
```

说明：虽然只有一个可玩游戏，仍保留“换个游戏”，因为主控给定了按钮文案；点击后返回菜单，不制造额外文案。

### 9. 如何保证奇怪小门优先

实现规则：

```text
1. strangeDoorDemo != null 时，不自动显示 EntryPrompt。
2. strangeDoorDemo != null 时，本地游戏关键词不触发 languageGame。
3. 奇怪小门进行中，语音 transcript 仍优先交给奇怪小门已有状态。
4. 奇怪小门点击“先聊别的”退出后，才允许 EntryPrompt 或关键词触发语言游戏。
5. 不改 StrangeDoorDemoState / reducer / mapper / UI model。
```

### 10. GameMenu 本轮是否只显示“脑筋急转弯 / 先聊别的”

是。

原因：

```text
1. 主控明确不做 disabled 菜单版本。
2. “词语接龙 / 猜谜语”本轮不能进入游戏，显示但不可点会造成挫败。
3. PD-060 的“首版菜单只允许三类游戏”理解为允许上限，不要求每一轮都展示未实现游戏。
```

### 11. 是否完全不显示词语接龙和猜谜语

是，本轮完全不显示。

后续 LG2 / LG3 确认实现后再加入菜单。

### 12. 会修改哪些文件

预计修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
```

预计新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameState.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/BrainTeaserQuestionBank.kt
android/app/src/main/java/com/childai/companion/ui/chat/languagegame/BrainTeaserEvaluator.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelLanguageGameTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/LanguageGameEntryUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/languagegame/BrainTeaserEvaluatorTest.kt
docs/session_process/handoffs/20260609_LG1_brain_teaser_handoff.md
```

如 `ChatUiState` 当前定义在其它文件，按实际代码结构做最小补丁。

### 13. 不会修改哪些文件

不会修改：

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

不新增：

```text
1. 后端 endpoint。
2. GrowthEvent 类型。
3. 数据表。
4. 小展台 item。
5. 家长端入口。
6. 素材资源。
```

### 14. 测试策略

计划阶段只运行：

```bash
bash scripts/doctor_local_env.sh
git diff --check
```

实现阶段建议新增 / 更新测试：

```text
1. EntryPrompt 显示“我们随便聊聊天 / 还是玩一个小游戏？”。
2. EntryPrompt 按钮为“随便聊聊 / 玩个小游戏”。
3. 每个 ChatViewModel 生命周期最多自动出现一次。
4. 点“随便聊聊”后，本生命周期不再自动弹出。
5. “玩个小游戏”进入 GameMenu。
6. GameMenu 本轮只显示“脑筋急转弯 / 先聊别的”。
7. GameMenu 不显示“词语接龙 / 猜谜语”。
8. 点“脑筋急转弯”进入第一题 Question。
9. 5 道题库内容与主控文本完全一致。
10. Question 状态下 ASR transcript 不发送普通 conversation。
11. transcript 包含答案关键词时进入 Correct。
12. transcript 不包含答案关键词时进入 Hint。
13. Hint 状态下再次回答，包含答案也能进入 Correct。
14. 点“给我提示”进入 Hint。
15. 点“告诉我答案”进入 Revealed。
16. Correct / Revealed 点“下一题”进入下一题。
17. 第 5 题后“下一题”循环到第 1 题，或按主控确认的方式处理。
18. 点“换个游戏”回 GameMenu。
19. 点“先聊别的”退出 languageGame 并恢复普通 conversation。
20. strangeDoorDemo != null 时不触发语言游戏。
21. 禁止词测试覆盖入口、菜单、题库、反馈、按钮。
22. D3 / D4 / D5 / S2 / S3 / S4 / S5 回归不破。
23. assembleDebug 通过。
```

### 15. 需要主控确认的问题

```text
1. 第 5 题后点击“下一题”是否循环回第 1 题？
2. 出题页按钮“我来答”在 voice-first 正式体验中是触发录音按钮，还是只是聚焦 / 展开语音控件？
3. EntryPrompt 是否只在普通 opening 后出现一次；“连续短句 / 不知道聊什么”触发是否暂缓？
4. 孩子主动说“词语接龙 / 猜谜语”时，本轮是否也先不触发任何入口，还是进入 GameMenu？
5. 答案关键词是否只做包含判断，还是允许同义词？本轮建议只做包含主控答案原词。
```

---

## 3. 允许文案清单

LG1 实现只能使用以下文案。

入口：

```text
我们随便聊聊天
还是玩一个小游戏？
随便聊聊
玩个小游戏
```

菜单：

```text
想玩哪一个？
脑筋急转弯
先聊别的
```

脑筋急转弯题库：

```text
什么东西越洗越脏？
什么门永远关不上？
什么东西越走越少？
什么瓜不能吃？
什么布剪不断？
```

答案：

```text
水
球门
路
傻瓜
瀑布
```

提示：

```text
它常常在杯子里、河里、盆里
它常常在操场上
你走过以后，它就被你走掉了一点点
它不是一种真的瓜
它不是用来做衣服的布
```

反馈：

```text
对，就是{answer}
这个答案有点绕
小白狐刚才也差点没绕出来

这个答案也有点意思
不过这题的小机关不是它
我给你一个提示
{hint}

我偷偷告诉你
答案是{answer}
是不是有点拐弯？
```

按钮：

```text
我来答
给我提示
换个游戏
先聊别的
下一题
我再猜
告诉我答案
```

---

## 4. 禁止边界

不得出现：

```text
答错了
不对
正确答案
分数
等级
奖励
连续答对
排行榜
通关
任务
学习入口
你不会
再认真一点
考试
错误
闯关
金币
排名
PK
背诵
默写
纠错
语法错误
我没听懂
```

不得做：

```text
1. 词语接龙。
2. 猜谜语。
3. 后端改造。
4. GrowthEvent。
5. 小展台承接。
6. 奇怪小门改造。
7. 家长端功能。
8. 真实儿童测试材料提交。
```

---

## 5. 状态

```text
PLAN ONLY。
等待主控确认后再进入 LG1 实现。
```
