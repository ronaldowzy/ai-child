# D1：奇怪小门 Demo 本地状态与合同交接

日期：2026-06-04

执行角色：开发执行会话

任务范围：只做本地状态、合同、mapper、测试和进度板同步；不做正式 UI、不接素材、不改后端。

---

## 1. 本轮结论

D1 已完成。

本轮按主控确认后的边界落地：

```text
1. Demo 状态以 Android 本地状态为主。
2. 图片上传仍复用现有 attachment 链路，D1 只定义识别结果到奇怪道具的 mapper。
3. 怪问题首版固定题目和答案，D1 只定义 evaluator。
4. 素材未完成前只定义资源合同，不引用真实 R.drawable。
5. 已同步 CODEX_PROGRESS_BOARD，把当前阶段切到“奇怪小门 Demo”。
```

---

## 2. 修改文件

新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapper.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorRiddleEvaluator.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorAssetContract.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorStateContractTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapperTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorRiddleEvaluatorTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorAssetContractTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorForbiddenWordsTest.kt
docs/session_process/handoffs/20260604_D1_strange_door_state_contract_handoff.md
```

修改：

```text
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

未修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt
android/app/src/main/res/drawable-nodpi/
backend/
android/app/src/main/java/com/childai/companion/ui/parent/
docs/PRODUCT_DECISIONS_V0_1.md
```

---

## 3. 行为变化

本轮没有儿童端可见 UI 变化。

新增的内部合同：

```text
1. StrangeDoorDemoState：
   NotStarted / ChoosingMethod / PhotoPrompt / PhotoUploading / PhotoResult / RiddlePrompt / RiddleHint / Completed。

2. StrangeDoorState：
   Closed / Cracked / AlmostOpen / Open，并保留 wireName：closed / cracked / almost_open / open。

3. StrangeDoorDoorStateReducer：
   None 不推进；
   AdvanceOneStep 按 closed -> cracked -> almost_open -> open 推进；
   Open 直接打开。

4. StrangeDoorPhotoTransformMapper：
   把 recognizedType / recognizedText / confidence 转成 objectName、shapeHint、transformedName、doorEffect、canSaveToShowcase、advanceSignal。

5. StrangeDoorRiddleEvaluator：
   固定题目“什么东西越洗越脏？”；
   答案“水”打开小门；
   非水答案进入提示。

6. StrangeDoorAssetContract：
   定义 S1 计划中的 10 个素材文件名、尺寸和 readiness mapper；
   当前不引用真实资源，避免占位 UI 冒充正式素材。
```

所有儿童端可见文本只来自主控文档已有词句，未自行扩写词池。

---

## 4. 安全和边界

已覆盖：

```text
1. homework_problem 不转成开门道具。
2. privacy_sensitive / unsafe_unknown 不转成开门道具。
3. blocked 图片不推进门状态，不允许保存到小展台。
4. low_confidence / unclear 不允许保存到小展台。
5. 禁止词测试覆盖任务、奖励、积分、等级、排行榜、抽卡等表达。
6. 不新增 GrowthEvent 类型。
7. 不新增后端 endpoint。
8. 不新增 image_purpose。
9. 不修改 M1/M2。
```

---

## 5. 进度板同步

已更新：

```text
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

主要变化：

```text
1. 版本从 v0.6 更新到 v0.7。
2. 当前阶段从“小屋小客人”切换为“奇怪小门 Demo”。
3. 记录 D0 done，D1 done，D2 planned。
4. 当前口径同步主控确认：opening 延后、InputBar 弱化、image_purpose=share、素材未完成前不做正式 UI。
5. Q1 真机检查重点改为奇怪小门试玩验收。
```

---

## 6. 测试结果

已通过：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*'
```

结果：

```text
D1 新增 strangedoor 包单测通过。
doctor_local_env 通过；当前 adb devices WARN：没有连接真机。
```

完整 Android 单测：

```bash
bash scripts/android_gradle.sh test
```

结果：

```text
失败。
新增 D1 代码已编译通过，但完整套件有 2 个非 strangedoor 测试失败：
1. MascotManifestTest.runtimeAssetsUseWebpFramesOnly
2. ChatViewModelStreamTest.audioReadyUsesQueueWhenNotMuted
本轮未修改这两个测试相关模块；需要后续单独排查或由对应 owner 处理。
```

补充说明：

```text
第一次尝试 `bash scripts/android_gradle.sh test --tests 'com.childai.companion.ui.chat.strangedoor.*'` 失败，
原因是 Gradle 对 `test` 聚合任务不接受 `--tests` 参数。
已改用 `:app:testDebugUnitTest --tests ...` 复跑通过。
```

---

## 7. 后续建议

D2 启动前必须确认：

```text
1. S1 素材 manifest 已完成。
2. 10 个资源文件名与 StrangeDoorAssetContract 一致。
3. 素材不是占位图，且可用于正式 UI 编码。
```

D2 建议只接：

```text
1. ChildChatScreen 首屏事件切换。
2. 首屏延后普通 opening。
3. 奇怪小门事件层 UI。
4. 弱化普通 InputBar。
5. 不接拍照真实流程和怪问题真实交互，留给 D3/D4。
```

---

## 8. 需要主控确认的问题

本轮没有新增产品问题。

D2 前仍需主控或素材整理方给出：

```text
1. S1 素材 manifest。
2. 10 个素材是否全部可用。
3. 若素材文件名或尺寸变更，是否同步调整 StrangeDoorAssetContract。
```

---

## 9. 未完成事项

```text
1. 未做正式 UI。
2. 未接入真实素材。
3. 未接入拍照真实流程。
4. 未接入怪问题真实交互。
5. 未接入小展台保存。
6. 未做真机 QA。
```

这些都符合 D1 禁止范围。
