# M3：小白狐轻记忆 Android 展示实现交接

日期：2026-06-13

状态：CODE PASS / 待合并真机验收

提交：待提交后补充

---

## 1. 本轮目标

把 M1 的 `LightMemorySnapshot` 本地状态合同和 M2 的 master-copy 文案接入儿童端 opening 展示。

M3 首版只做：

```text
1. opening 轻记忆展示；
2. 多候选优先级选择；
3. opening 展示后 mark recalled；
4. 不自动 TTS 播报；
5. 禁止文案扫描测试；
6. CODEX_PROGRESS_BOARD 更新。
```

---

## 2. 已实现内容

新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/LightMemoryCopyMapper.kt
android/app/src/test/java/com/childai/companion/ui/chat/lightmemory/LightMemoryCopyMapperTest.kt
```

更新：

```text
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/LightMemoryReducer.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/lightmemory/LightMemoryReducerTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelLightMemoryTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/handoffs/20260613_M3_light_memory_android_display_handoff.md
```

---

## 3. 行为变化

opening 成功后：

```text
1. 先正常渲染原 opening；
2. 再检查 lightMemory.openingRecallCandidate；
3. 如存在可展示候选，追加一条本地 Agent 消息；
4. 追加后调用 markLightMemoryOpeningRecalled；
5. 本次 opening 不再自动弹语言游戏 EntryPrompt；
6. 不自动 TTS 播报轻记忆文案。
```

未改变：

```text
1. 不替代原 opening；
2. 不拼接进后端 opening response；
3. 不调用后端重新生成；
4. 不新增按钮；
5. 不修改 ChildChatScreen；
6. 孩子主动说“玩游戏 / 脑筋急转弯 / 词语接龙 / 猜谜语”仍走现有语言游戏路由。
```

---

## 4. 文案映射

`LightMemoryCopyMapper` 只使用 M2 master-copy。

已接入：

```text
1. ShowcaseAssist / ShowcaseItem：使用小展台更轻版本；
2. StrangeDoorCompleted 有 displayName：使用 displayName 小门文案；
3. StrangeDoorCompleted 无 displayName：使用无名小门文案；
4. StrangeDoorTool：复用 displayName 小门文案；
5. StrangeDoorMechanism：按 Round / Soft / Shiny 使用三套机关文案。
```

未新增：

```text
1. 不新增 StrangeDoorTool 独立文案；
2. 不新增普通聊天文案；
3. 不新增按钮文案。
```

---

## 5. 多候选优先级

已按主控确认顺序实现：

```text
1. ShowcaseAssist；
2. ShowcaseItem；
3. StrangeDoorCompleted 且有 displayName；
4. StrangeDoorTool；
5. StrangeDoorCompleted 无 displayName；
6. StrangeDoorMechanism。
```

同一优先级：

```text
选择 lastTouchedAtMillis 最新的一条。
```

`LightMemoryReducer.withOpeningRecallEligibility` 已同步改为使用该优先级选择 openingRecallCandidateId。

---

## 6. 边界确认

本轮未做：

```text
1. 不新增后端；
2. 不新增数据表；
3. 不新增 GrowthEvent；
4. 不新增 image_purpose；
5. 不做跨天持久化；
6. 不改家长端；
7. 不改小展台数据模型；
8. 不改小展台列表 / 详情 UI；
9. 不改奇怪小门玩法节奏；
10. 不改奇怪小门素材；
11. 不改奇怪小门门状态 reducer；
12. 不改语言游戏题库；
13. 不改语言游戏词库；
14. 不改语言游戏状态机；
15. 不改 attachment 后端链路；
16. 不改 conversation / opening 后端接口；
17. 不保存原始语音、原始照片、原始聊天全文或孩子原始回答；
18. 不保存分数、等级、排名；
19. 不做学习画像；
20. 不做任务、奖励、打卡、排行榜。
```

说明：

```text
ChildChatScreen.kt 当前工作区存在本轮前遗留未提交改动；M3 未修改该文件，也不会暂存该文件。
```

---

## 7. 测试结果

已执行定向测试：

```bash
bash scripts/android_gradle.sh testDebugUnitTest --tests 'com.childai.companion.ui.chat.lightmemory.LightMemoryCopyMapperTest' --tests 'com.childai.companion.ui.chat.lightmemory.LightMemoryReducerTest' --tests 'com.childai.companion.ui.chat.ChatViewModelLightMemoryTest'
```

结果：

```text
BUILD SUCCESSFUL
```

已执行全量 Android 单元测试：

```bash
bash scripts/android_gradle.sh testDebugUnitTest
```

结果：

```text
BUILD SUCCESSFUL
```

已执行 Android 构建：

```bash
bash scripts/android_gradle.sh assembleDebug
```

结果：

```text
BUILD SUCCESSFUL
```

提交前还需执行：

```bash
git diff --check
git diff --cached --check
```

---

## 8. 测试覆盖

新增 / 更新覆盖：

```text
1. opening 成功后追加轻记忆消息；
2. opening 失败时不追加轻记忆；
3. child input 先发生时不追加轻记忆；
4. 展示后 markLightMemoryOpeningRecalled；
5. 每生命周期最多一次；
6. mutedForCurrentLifecycle 时不展示；
7. strangeDoorDemo != null 时不展示；
8. languageGame != null 时不展示；
9. 多候选按主控优先级选择；
10. 同优先级按 lastTouchedAtMillis 最新选择；
11. StrangeDoorTool 复用 displayName 小门文案；
12. 不自动 TTS 播报轻记忆；
13. 不新增按钮；
14. 禁止文案扫描覆盖主控指定词；
15. LG1 / LG2 / LG3 回归不破；
16. 奇怪小门 / 小展台回归不破。
```

禁止文案扫描覆盖：

```text
我一直记得你
我一直在等你
只有我记得
这是我们的秘密
通关
奖励
任务
等级
分数
排名
打卡
rawTranscript
rawPhotoBytes
recognizedText
childAnswer
```

---

## 9. public repo 注意

本轮未新增真实测试材料。

提交时只应暂存 M3 相关文件，不暂存工作区已有：

```text
backend/storage/danger_zone_warning.wav
docs/session_process/handoffs/q1_device_screenshots/
docs/session_process/handoffs/xiaozhantai_device_screenshots/
scripts/gen_danger_zone_tts.py
storage/
```

---

## 10. 是否需要合并真机验收

需要。

真机验收重点：

```text
1. opening 后轻记忆是否像小白狐轻轻想起，而不是系统复盘；
2. 是否只出现一次，不重复刷屏；
3. 是否不打断奇怪小门首屏事件；
4. 是否不在语言游戏进行中出现；
5. 是否不新增按钮或入口；
6. 是否不催孩子继续旧流程；
7. 是否不出现任务、奖励、通关、等级、打卡、排名感；
8. 孩子先聊别的后，本生命周期不再自动提；
9. 本次 opening 已展示轻记忆时，不自动弹语言游戏 EntryPrompt；
10. 文案是否短、轻、可放下。
```

---

## 11. 后续建议

```text
1. M3 通过主控审核后进入合并真机验收。
2. 普通聊天 relatedChatCandidate 接入留到 M4 再评估。
3. 是否对轻记忆文案启用自动 TTS，应单独由主控确认。
4. 是否在后续清理工作区已有音频、截图、storage 材料，由主控单独确认。
```
