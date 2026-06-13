# M1：小白狐轻记忆本地状态与数据合同交接

日期：2026-06-13

状态：CODE PASS / 待合并真机验收

提交：待提交后补充

---

## 1. 本轮目标

实现“小白狐轻记忆”的 Android 本地最小状态与数据合同。

本轮只做：

```text
1. Android 本地轻状态。
2. 奇怪小门完成摘要。
3. 最近安全机关类型。
4. 最近安全道具名。
5. 既有小展台 item 安全字段读取。
6. 小展台小发现是否回来帮过门。
7. opening 低频召回状态条件。
8. 普通聊天主动相关时的本地使用条件。
9. public repo 数据扫描清单和结果记录。
10. 真机验收清单。
```

---

## 2. 已实现内容

新增本地包：

```text
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/
```

新增本地合同和纯函数：

```text
LightMemorySnapshot
LightMemorySource
LightMemoryCandidate
LightMemoryStatus
LightMemoryReducer
LightMemorySafetyGate
```

`ChatUiState` 已增加：

```text
lightMemory: LightMemorySnapshot
```

`ChatViewModel` 已接入：

```text
1. 奇怪小门拍照安全推进后，记录最近安全机关类型和安全道具名。
2. 奇怪小门 Completed 后，生成 StrangeDoorCompleted 低敏候选。
3. 小展台保存成功后，读取既有 item 的 id / name / createdAt / foxQuote。
4. 小展台小发现回来帮门后，生成 ShowcaseAssist 候选并标记 assistedDoorInCurrentLifecycle。
5. blocked / privacy / homework / unsafe 不进入 Active candidate。
6. opening 只输出 openingRecallCandidateId 状态条件，不新增儿童端最终文案。
7. 普通聊天只在孩子主动提到小门 / 奇怪小门 / 小展台 / 小发现 / 刚才那个 / 我放进去的 / 帮小白狐时，设置 relatedChatCandidateId。
8. 语言游戏不写入 LightMemorySnapshot。
```

---

## 3. 数据边界

允许进入轻记忆的字段：

```text
1. mechanismType：Round / Soft / Shiny。
2. toolName：来自 StrangeDoorPhotoTransformMapper 的安全道具名。
3. showcaseItemId：既有小展台 item id。
4. showcaseItemName：既有小展台 item name。
5. showcaseCreatedAtMillis：既有小展台 item createdAt。
6. showcaseFoxQuote：既有小展台 item foxQuote，必须经过 LightMemorySafetyGate。
```

禁止进入轻记忆的字段：

```text
rawTranscript
rawPhotoBytes
recognizedText
childAnswer
score
rank
school
address
phone
realName
promptTrace
```

实现说明：

```text
1. 不复制图片。
2. 不读取 image bytes。
3. 不读取 recognizedContent 原文。
4. 不读取 privacySignals。
5. 不保存原始语音。
6. 不保存原始照片。
7. 不保存原始聊天全文。
8. 不保存孩子原始回答。
9. 不写后端。
10. 不写本地文件。
11. 不做跨天持久化。
```

---

## 4. 安全过滤

`LightMemorySafetyGate` 会过滤：

```text
blocked
privacy
homework
unsafe
隐私
学习
作业
题目
考试
学校
班级
老师
地址
住址
电话
手机号
真实姓名
身份证
证件
人脸
医疗
病历
医院
```

小展台 `foxQuote` 命中以上风险内容时，整条 item 不进入 Active 轻记忆候选。

---

## 5. 未做内容

本轮未做：

```text
1. 不新增 repository。
2. 不新增 service。
3. 不新增 database。
4. 不新增 network client。
5. 不新增后端接口。
6. 不新增数据表。
7. 不新增 GrowthEvent。
8. 不新增 image_purpose。
9. 不改 attachment 链路。
10. 不改 conversation / opening 后端接口。
11. 不新增儿童端最终文案。
12. 不接语言游戏偏好。
13. 不做普通聊天自由抽取。
14. 不做跨天持久化。
15. 不写本地文件。
16. 不改家长端。
17. 不扩小展台数据模型。
```

---

## 6. 修改文件

本轮新增 / 修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/LightMemorySnapshot.kt
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/LightMemoryReducer.kt
android/app/src/main/java/com/childai/companion/ui/chat/lightmemory/LightMemorySafetyGate.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/lightmemory/LightMemoryReducerTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelLightMemoryTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/handoffs/20260612_M1_light_memory_local_state_contract_handoff.md
```

未修改：

```text
backend/
家长端
小展台数据模型
语言游戏题库 / 词库
奇怪小门文案 / 词池 / 素材
attachment 后端链路
conversation / opening 后端接口
```

说明：工作区在本轮开始前已有其他未提交改动和未跟踪文件，本轮只计划暂存上述 M1 相关文件。

---

## 7. 测试结果

已执行：

```bash
bash scripts/android_gradle.sh testDebugUnitTest --tests 'com.childai.companion.ui.chat.lightmemory.LightMemoryReducerTest' --tests 'com.childai.companion.ui.chat.ChatViewModelLightMemoryTest'
```

结果：

```text
BUILD SUCCESSFUL
20 tests completed
```

已执行：

```bash
bash scripts/android_gradle.sh testDebugUnitTest
```

结果：

```text
BUILD SUCCESSFUL
```

已执行：

```bash
bash scripts/android_gradle.sh assembleDebug
```

结果：

```text
BUILD SUCCESSFUL
```

已执行：

```bash
git diff --check
git diff --cached --check
```

结果：

```text
通过
```

---

## 8. 测试覆盖

新增测试覆盖：

```text
1. reset 后 LightMemorySnapshot 为空或默认安全态。
2. 奇怪小门 Completed 生成 StrangeDoorCompleted candidate。
3. Round / Soft / Shiny 只记录为最近安全机关类型。
4. 安全道具名只来自 mapper 批准结果。
5. blocked / privacy / homework 不生成 Active candidate。
6. 小展台只读取 id / name / createdAt / foxQuote。
7. foxQuote 命中隐私 / 学习 / 地址 / 学校 / 真实姓名 / 电话 / 人脸 / 证件时过滤。
8. 小展台小发现回来帮门后 assistedDoorInCurrentLifecycle == true。
9. opening 召回每生命周期最多一次。
10. 先聊别的后 mutedForCurrentLifecycle == true。
11. 普通聊天未主动提相关内容时不使用轻记忆。
12. 语言游戏不写入 LightMemorySnapshot。
13. 禁止字段测试覆盖 rawTranscript / rawPhotoBytes / recognizedText / score / rank / school / address / phone / realName / promptTrace。
```

全量 Android 单测覆盖现有 D3 / D4 / D5 / S2 / S3 / S4 / S5 / LG1 / LG2 / LG3 回归。

---

## 9. public repo 数据扫描结果

已执行：

```bash
git status --short
git diff --cached --name-only
git diff --cached --check
rg -n "api[_-]?key|token|secret|BEGIN PRIVATE KEY|prompt trace|真实姓名|学校|住址|电话|证件|身份证" .
find . -path "./.git" -prune -o \( -name "*.wav" -o -name "*.mp3" -o -name "*.m4a" -o -name "*.sqlite" -o -name "*.db" -o -name "*.pt" -o -name "*.onnx" \) -print
```

结果摘要：

```text
1. git status --short 显示本轮 M1 文件，以及本轮开始前已存在的未提交 Android / release / storage / 截图 / 音频相关改动。
2. git diff --cached --name-only 已复跑，暂存区只包含 M1 相关代码、测试和文档。
3. git diff --check 和 git diff --cached --check 均通过。
4. rg 命中大量公开文档和代码中的安全说明、示例 env、token_hash、api_key_present 等非真实凭据文本。
5. rg 命中 scripts/gen_danger_zone_tts.py、backend/storage/danger_zone_warning.wav、storage/、backend/storage/tts_cache 等本轮前已有未跟踪或生成材料；这些不会纳入本次提交。
6. find 命中 backend/storage/tts_cache 下大量 .wav、backend/assets/voices 下既有小白狐 voice sample、backend/.venv 下第三方 scipy 测试音频；本轮不会暂存这些文件。
7. 本轮新增 M1 代码和文档未包含真实儿童姓名、真实家庭信息、原始儿童音频、原始儿童照片、原始聊天转录、prompt trace、本地数据库、模型权重或 TTS cache。
```

提交前要求：

```text
只暂存 M1 相关代码、测试和文档；
不暂存 backend/storage/danger_zone_warning.wav；
不暂存 storage/；
不暂存 docs/session_process/handoffs/q1_device_screenshots/；
不暂存 docs/session_process/handoffs/xiaozhantai_device_screenshots/；
不暂存生成的 TTS cache；
不暂存本地数据库或模型权重。
```

---

## 10. 真机验收清单

后续合并真机验收建议覆盖：

```text
1. 完成奇怪小门后，本地轻状态存在完成摘要，但儿童端没有新增未经主控确认的文案。
2. 拍照 blocked / privacy / homework 不进入轻状态。
3. 小展台保存成功后，轻状态只读取 id / name / createdAt / foxQuote。
4. 用小展台小发现帮门后，轻状态只记录本生命周期 assistedDoorInCurrentLifecycle。
5. opening 轻召回每个 ChatViewModel 生命周期最多一次。
6. 孩子选择先聊别的后，本生命周期不再提轻记忆。
7. 普通聊天只有孩子主动提小门 / 小展台 / 小发现时才允许使用已有候选。
8. 语言游戏过程不写入轻记忆。
9. 家长端没有新增轻记忆入口或报告项。
10. 日志和仓库不包含真实儿童照片、音频、聊天转录或家庭测试材料。
```

---

## 11. 风险与注意

```text
1. M1 当前只提供状态条件，不提供最终儿童端文案；后续如果要展示，需要主控先给 master-copy。
2. LightMemorySnapshot 当前随 ChatViewModel 生命周期存在；App 重启后为空。
3. 既有小展台 repository 本身会持久化小展台 item；M1 没有扩展它，也没有复制图片。
4. 工作区存在本轮前遗留未提交材料，提交时必须继续只暂存 M1 范围。
5. 是否需要在后续任务中清理 backend/storage、storage/、截图目录和 TTS cache，由主控单独确认。
```

---

## 12. 是否需要合并真机验收

需要。

M1 本轮是 CODE PASS，但轻记忆属于体验连续性能力，建议与奇怪小门、小展台、语言游戏第一组合并做真机验收，重点看：

```text
1. 小白狐是否像轻轻想起一点点，而不是系统复盘。
2. 轻记忆是否没有抢奇怪小门和语言游戏主线。
3. 退出 / 先聊别的后是否能自然回普通聊天。
4. 是否没有出现学习评价、奖励、积分、等级或任务感。
```
