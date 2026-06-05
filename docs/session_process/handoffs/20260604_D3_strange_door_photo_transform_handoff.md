# D3：奇怪小门拍照变身路径交接

日期：2026-06-05

执行角色：开发执行会话

任务范围：接通“找东西帮忙 -> 拍给小白狐看 -> 图片上传识别 -> 现实物品变成奇怪道具 -> 小门状态变化”；不改后端、不新增 endpoint、不新增 image purpose、不接怪问题真实回答、不完成小展台保存。

---

## 1. 本轮结论

D3 已完成。

已按主控确认后的边界落地：

```text
1. “拍给小白狐看”启动现有拍照 / 相册图片入口。
2. 图片上传继续复用现有 attachment 链路。
3. image_purpose 继续使用 share。
4. 上传成功后读取 AttachmentCreateResponse.recognizedContent。
5. recognizedContent 接入 StrangeDoorPhotoTransformMapper。
6. 展示“现实物品 -> 奇怪道具 -> 小门反馈”固定模板。
7. 根据 advanceSignal 推进 Android 本地 StrangeDoorState。
8. 门状态变化时切换对应门素材。
9. blocked 图片显示主控确认的不适合文案，不推进门状态，不允许保存到小展台。
10. “放进小展台”在 D3 只记录本地保存意图，不创建小展台对象。
```

---

## 2. 修改文件

修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapper.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChildCompanionPageRulesTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapperTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

新增：

```text
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorPhotoTransformTest.kt
docs/session_process/handoffs/20260604_D3_strange_door_photo_transform_handoff.md
```

未修改：

```text
backend/
android/app/src/main/java/com/childai/companion/ui/parent/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/data/showcase/
M1 / M2 相关逻辑
```

---

## 3. 行为变化

儿童端可见变化：

```text
1. 点击“找东西帮忙”后，“拍给小白狐看”会打开现有拍照 / 相册入口。
2. 图片上传成功后，奇怪小门事件页显示：

我看见了：{现实物品}

在小白狐的世界里
它变成了：{怪道具名}

小白狐用它{动作}
{小门反应}

3. 圆形物品可直接让门打开。
4. partial / unknown 物品推进一小步。
5. 不适合内容不推进门状态，显示：

这张图不太适合变成开门道具
我们换一个小东西试试

6. 拍照变身结果后显示：
再找一个
放进小展台
动脑试试
```

---

## 4. 安全和边界

已落实：

```text
1. 不改后端。
2. 不新增 endpoint。
3. 不新增 strange_door image purpose。
4. 不调用模型生成变身道具文案。
5. 继续使用 D1 主控词池和 mapper。
6. homework_problem / privacy_sensitive / unsafe_unknown 不转成道具。
7. 识别文本命中人脸、学校、地址、证件、隐私、医疗、暴力、惊吓、作业、题目、学习时不转成道具。
8. blocked 图片不推进门状态，不允许保存到小展台。
9. D3 不完成小展台保存，只记录本地保存意图。
10. 不做奖励、积分、等级、地图、签到。
11. 不接怪问题真实回答。
```

---

## 5. 测试结果

已通过：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorDemoTest' --tests 'com.childai.companion.ui.chat.ChildCompanionPageRulesTest' --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*'
```

覆盖：

```text
1. “拍给小白狐看”使用现有图片入口和 image_purpose=share。
2. 上传成功后 recognizedContent 进入 StrangeDoorPhotoTransformMapper。
3. round 物品直接打开门。
4. partial / unknown 物品推进一小步。
5. blocked 类型不推进、不允许保存。
6. 作业 / 学习 / 学校地址 / 人脸证件文本不转成道具。
7. 图片失败时不假装看到了。
8. D3 不触发普通 conversation 后端请求。
9. 禁止词测试继续通过。
10. Android debug 构建通过。
```

---

## 6. 截图 / 录屏

本轮未产出截图或录屏。

原因：

```text
当前 doctor_local_env 显示 adb devices WARN：没有连接真机。
```

---

## 7. 风险点

```text
1. 尚未做真机拍照 / 相册路径视觉 QA。
2. D3 的“放进小展台”只记录本地意图，不创建小展台对象；D5 需要完成真实承接。
3. mapper 依赖 attachment 的 recognizedContent.type / text，若后端识别文本过泛，可能更多进入 unknown 半成功路径。
4. 当前不新增后端分类，隐私 / 作业等安全边界由现有 type 加 Android 本地文本拦截共同兜底。
```

---

## 8. 是否可进入 D4

结论：

```text
可以进入 D4：怪问题路径。
```

D4 建议只做：

```text
1. 语音回答入口。
2. 复用 StrangeDoorRiddleEvaluator。
3. 答对打开门，答错进入提示。
4. 不接拍照改动，不改后端，不新增奖励积分等级。
```
