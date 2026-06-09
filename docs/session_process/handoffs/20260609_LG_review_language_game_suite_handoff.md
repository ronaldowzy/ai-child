# LG-Review：语言游戏第一组收口与验收交接

日期：2026-06-09

执行角色：开发执行会话

状态：DOC PASS / 待合并真机验收

---

## 1. 本轮结论

本轮只整理语言游戏第一组收口文档，未修改 Android 代码、后端代码、小展台、奇怪小门或家长端。

语言游戏第一组已形成当前闭环：

```text
LG1：脑筋急转弯
LG2：词语接龙
LG3：猜谜语
```

三项均来自已完成交接，状态均为：

```text
CODE PASS / 待合并真机验收
```

当前最终 GameMenu：

```text
脑筋急转弯
词语接龙
猜谜语
先聊别的
```

---

## 2. 入口与菜单

语言游戏入口是普通聊天中的轻选择，不是首页大功能区，也不是学习入口。

EntryPrompt：

```text
我们随便聊聊天
还是玩一个小游戏？
```

按钮：

```text
随便聊聊
玩个小游戏
```

行为边界：

```text
1. EntryPrompt 每个 ChatViewModel 生命周期最多自动出现一次。
2. 孩子点击“随便聊聊”后，本生命周期不再自动弹出语言游戏入口。
3. 孩子点击“玩个小游戏”后进入 GameMenu。
4. 孩子说“玩游戏”后进入 GameMenu。
5. 孩子说“脑筋急转弯”后直接进入 BrainTeaser。
6. 孩子说“词语接龙 / 接龙”后直接进入 WordChain。
7. 孩子说“猜谜语 / 谜语”后直接进入 Riddle。
8. 奇怪小门进行中不触发语言游戏。
```

---

## 3. LG1 脑筋急转弯边界

LG1 只使用主控确认的 5 题本地题库。

行为边界：

```text
1. 点击“脑筋急转弯”进入第 1 题。
2. 小白狐出题，孩子语音回答。
3. Question / Hint 状态下，ASR transcript 只交给本地 BrainTeaserEvaluator，不发送普通 conversation。
4. 判断只做答案原词包含，不做同义词、拼音、近音或模糊语义扩展。
5. 答对进入 Correct。
6. 未命中答案进入 Hint。
7. “告诉我答案”进入 Revealed。
8. Correct / Revealed 点击“下一题”进入下一题。
9. 第 5 题后点击“下一题”循环回第 1 题。
10. “换个游戏”返回 GameMenu。
11. “先聊别的”退出 languageGame 并恢复普通 conversation。
```

文案边界：

```text
1. 只使用 LG1 主控确认的题库、提示、反馈和按钮。
2. 不新增题目。
3. 不新增提示。
4. 不新增反馈。
5. 不使用“答错了 / 不对 / 正确答案”等表达。
6. 不做分数、等级、奖励、连续答对、排行榜、通关、任务或学习入口。
```

---

## 4. LG2 词语接龙边界

LG2 只使用主控确认的 5 条固定词链：

```text
苹果 -> 果汁 -> 汁水 -> 水池 -> 池塘 -> 塘边
月亮 -> 亮光 -> 光点 -> 点心 -> 心愿 -> 愿望
小猫 -> 猫毛 -> 毛笔 -> 笔盒 -> 盒饭 -> 饭团
大树 -> 树枝 -> 枝条 -> 条纹 -> 纹路 -> 路灯
水杯 -> 杯口 -> 口琴 -> 琴声 -> 声音 -> 音乐
```

行为边界：

```text
1. 点击“词语接龙”进入 WordChain。
2. 默认起始词固定为“苹果”。
3. “再玩一次”按固定顺序轮换：苹果 -> 月亮 -> 小猫 -> 大树 -> 水杯 -> 苹果。
4. WordChain 进行中，ASR transcript 不发送普通 conversation。
5. 判断只比较 previousWord 最后一个有效汉字和 transcript 第一个有效汉字。
6. 不校验孩子说的是不是真实词语。
7. 不查词典。
8. 不调用模型。
9. 不现场编词。
10. 连续 2 次没接上后，小白狐自动帮接并切到更容易词。
11. 最多 5 轮后进入 Finished。
12. Finished 后可以“再玩一次 / 换个游戏 / 先聊别的”。
```

文案边界：

```text
1. 只使用 LG2 主控确认的规则说明、接上反馈、提示反馈、小白狐帮接、结束文案和按钮。
2. 不新增词链。
3. 不新增词库。
4. 不做成语接龙。
5. 不说孩子错了。
6. 不做分数、等级、奖励、连续答对、排行榜、通关、任务或学习入口。
```

---

## 5. LG3 猜谜语边界

LG3 只使用主控确认的 5 题本地谜题库。

行为边界：

```text
1. 点击“猜谜语”进入 Riddle 第 1 题。
2. 第一题固定从题 1 开始，不随机。
3. 谜面按多行展示。
4. Question / Hint 状态下，ASR transcript 只交给本地 RiddleEvaluator，不发送普通 conversation。
5. 判断只做答案原词包含。
6. 不做同义词、拼音、近音、模糊语义。
7. 不查词典。
8. 不调用模型。
9. 不让后端判断。
10. transcript 只用于当前本地判断，不保存孩子原始回答。
11. Correct / Revealed 点击“下一题”进入下一题。
12. 第 5 题后点击“下一题”循环回第 1 题。
13. “换个游戏”返回 GameMenu。
14. “先聊别的”退出 languageGame 并恢复普通 conversation。
```

状态按钮边界：

```text
1. Question：我来猜 / 给我提示 / 换个游戏 / 先聊别的。
2. Hint：我来猜 / 告诉我答案 / 换个游戏 / 先聊别的。
3. Correct：下一题 / 换个游戏 / 先聊别的。
4. Revealed：下一题 / 换个游戏 / 先聊别的。
```

与奇怪小门边界：

```text
1. LG3 不复用 StrangeDoorRiddleEvaluator。
2. LG3 不修改 StrangeDoorRiddleEvaluator。
3. LG3 不修改奇怪小门“动脑试试”路径。
4. LG3 不修改 StrangeDoorDemoState、门状态节奏、拍照路径或小展台回到小门路径。
```

---

## 6. 系统边界

### 6.1 与奇怪小门

```text
1. strangeDoorDemo != null 时，不触发语言游戏。
2. 奇怪小门进行中，语音 transcript 优先交给奇怪小门。
3. 奇怪小门“动脑试试”与 LG3 猜谜语完全隔离。
4. 不修改门状态节奏。
5. 不修改拍照变身路径。
6. 不修改小展台旧物回到小门路径。
```

### 6.2 与普通聊天

```text
1. 语言游戏进行中拦截对应 ASR transcript，不误发普通 conversation。
2. 点击“先聊别的”后清空 languageGame，恢复普通 conversation。
3. 不清空普通聊天历史。
4. 不向后端写入语言游戏状态。
```

### 6.3 与小展台

```text
1. 语言游戏不接小展台。
2. 语言游戏不创建小展台 item。
3. 语言游戏不修改 XiaozhantaiItem。
4. 语言游戏不新增小展台入口或详情能力。
```

### 6.4 与后端和数据

```text
1. 不改后端。
2. 不新增 endpoint。
3. 不新增 image_purpose。
4. 不新增数据表。
5. 不新增 GrowthEvent。
6. 不保存孩子原始回答。
7. 不保存猜测历史。
8. 不保存语音 transcript。
9. 不提交真实儿童语音、照片、聊天转录或其他测试材料。
```

### 6.5 与家长端

```text
1. 不新增家长端功能。
2. 不新增家长端报告项。
3. 不新增语言游戏统计。
4. 不新增学习评价或排名表达。
```

---

## 7. 统一真机验收清单

后续合并真机验收建议按以下顺序执行：

```text
1. 普通 opening 后，EntryPrompt 出现自然，不抢奇怪小门。
2. 点击“随便聊聊”后，本 ChatViewModel 生命周期不再自动弹出 EntryPrompt。
3. 点击“玩个小游戏”进入 GameMenu。
4. GameMenu 显示“脑筋急转弯 / 词语接龙 / 猜谜语 / 先聊别的”。
5. 点击“脑筋急转弯”进入第 1 题，语音回答后只走本地 BrainTeaser 判断。
6. 点击“词语接龙”进入固定起始词“苹果”，语音回答后只走本地 WordChain 判断。
7. 点击“猜谜语”进入第 1 题，语音回答后只走本地 Riddle 判断。
8. 三个游戏中的“我来答 / 我来接 / 我来猜”均能自然触发语音输入。
9. 录音权限、录音开始、停止、ASR 回填链路顺畅。
10. 游戏进行中 ASR transcript 不误发普通 conversation。
11. 每个游戏的“换个游戏”能回到 GameMenu。
12. 每个游戏的“先聊别的”能恢复普通聊天。
13. 关键词“玩游戏 / 脑筋急转弯 / 词语接龙 / 接龙 / 猜谜语 / 谜语”路由正确。
14. 奇怪小门进行中不会被语言游戏打断。
15. 奇怪小门“动脑试试”不受 LG3 影响。
16. public repo 下不提交真实儿童语音、照片、聊天转录或测试材料。
```

---

## 8. 回归测试清单

代码侧回归应覆盖：

```text
1. LG1 / LG2 / LG3 languagegame 单测。
2. ChatViewModelLanguageGameTest。
3. BrainTeaserQuestionBank / BrainTeaserEvaluator 测试。
4. WordChainWordBank / WordChainEvaluator 测试。
5. RiddleQuestionBank / RiddleEvaluator 测试。
6. 禁止词测试覆盖全部语言游戏文案、题库、词库、反馈和按钮。
7. EntryPrompt 单生命周期触发测试。
8. “随便聊聊”后不再自动弹出测试。
9. GameMenu 三项游戏菜单测试。
10. 游戏中 ASR transcript 不发送普通 conversation 测试。
11. “换个游戏 / 先聊别的”状态恢复测试。
12. strangeDoorDemo != null 时不触发语言游戏测试。
13. 奇怪小门 D3 / D4 / D5 / S2 / S3 / S4 / S5 回归不破。
14. assembleDebug 通过。
15. git diff --check 通过。
```

本轮只整理文档，未重新运行 Android 构建或单测。

---

## 9. 暂缓玩法

以下方向暂缓，不进入当前实现：

```text
1. 四字接龙。
2. 成语接龙。
3. 乱词造句。
4. 反着说。
5. 谁最像。
6. 小白狐听错了。
7. 接一句故事。
8. 三个怪答案。
9. 语言游戏接小展台。
10. 语言游戏家长端报告。
11. 语言游戏后端题库。
12. 模型生成谜题或题目。
```

---

## 10. 禁止扩展方向

后续语言游戏第一组收口阶段仍需保持：

```text
1. 不新增玩法。
2. 不新增儿童端文案。
3. 不新增题库。
4. 不新增词库。
5. 不改后端。
6. 不新增 endpoint。
7. 不新增 GrowthEvent。
8. 不接小展台。
9. 不改奇怪小门。
10. 不改家长端。
11. 不做课程、练习、挑战、闯关。
12. 不做分数、等级、奖励、金币、排行榜、PK、连续答对或打卡。
13. 不保存孩子原始回答、语音 transcript 或猜测历史。
14. 不提交真实儿童测试材料。
```

---

## 11. 本轮修改

修改文件：

```text
docs/session_process/handoffs/20260609_LG_review_language_game_suite_handoff.md
```

未修改文件：

```text
android/
backend/
docs/session_process/handoffs/20260609_LG1_brain_teaser_handoff.md
docs/session_process/handoffs/20260609_LG2_word_chain_handoff.md
docs/session_process/handoffs/20260609_LG3_riddle_handoff.md
docs/PRODUCT_DECISIONS_V0_1.md
```

是否改代码：

```text
否
```

是否需要合并真机验收：

```text
是。LG1 / LG2 / LG3 均为 CODE PASS / 待合并真机验收，本轮文档整理不替代真机语音与路由验收。
```
