# D2：奇怪小门首页事件 UI 交接

日期：2026-06-05

执行角色：开发执行会话

任务范围：只做 Android 首页事件 UI、本地入口状态切换、资源接入校验和测试；不接真实拍照流程、不接怪问题真实回答、不接小展台保存、不改后端。

---

## 1. 本轮结论

D2 已完成。

已按主控确认后的边界落地：

```text
1. 进入 ChildChatScreen 后默认激活奇怪小门 Demo。
2. Demo 激活时普通 opening greeting 延后，不请求后端 opening。
3. 首屏使用 S1 正式 WebP 素材，显示 closed 小门、圆锁和地面阴影。
4. 首屏显示主控确认的标题、小白狐气泡和两个入口按钮。
5. 普通 InputBar 在 Demo 激活时不显示，首屏不再像普通聊天页。
6. 小展台入口和家长入口保留在弱入口位置。
7. 点击“找东西帮忙”“动脑试试”只切换 Android 本地 Demo 状态，不接真实流程。
```

---

## 2. 修改文件

新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorAndroidResources.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorDemoTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
docs/session_process/handoffs/20260604_D2_strange_door_home_event_ui_handoff.md
```

修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChildCompanionPageRulesTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorForbiddenWordsTest.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
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
1. 打开儿童聊天页后，首屏先看到“奇怪小门挡住了小白狐”事件。
2. 普通 opening 不抢首屏。
3. 页面主视觉显示小白狐、奇怪小门、圆锁和地面阴影。
4. 首屏只突出“找东西帮忙”“动脑试试”。
5. 点击“找东西帮忙”进入 PhotoPrompt 本地状态，展示主控确认的拍照提示文案和按钮。
6. 点击“动脑试试”进入 RiddlePrompt 本地状态，展示固定怪问题。
```

D2 未做真实流程：

```text
1. “拍给小白狐看”按钮在 D2 不启动相机或相册。
2. 怪问题不接语音回答、不判断答案。
3. 不上传图片，不调用后端，不保存小展台。
```

---

## 4. 文案边界

本轮儿童端可见文本只使用主控文档已确认文本：

```text
奇怪小门挡住了小白狐
你来得正好
我被这扇奇怪小门挡住了
它说：
找一个圆圆的东西
或者答对一个怪问题
找东西帮忙
动脑试试
找一个有点圆的东西就行
瓶盖、杯子、球、纽扣都可以
奇怪一点也可以
拍给小白狐看
先换个办法
什么东西越洗越脏？
```

未新增第二关、第三关、奖励、积分、等级、地图、排行榜、签到或任务表达。

---

## 5. 资源接入

已接入：

```text
strange_door_closed.webp
strange_door_round_lock.webp
strange_door_ground_shadow.webp
strange_door_riddle_panel.webp
strange_door_tool_card_panel.webp
```

同时为 D3-D5 保持 10 个 S1 资源的 Android drawable 映射。

资源缺失处理：

```text
StrangeDoorAndroidResources 直接映射 R.drawable。
若资源文件缺失，构建会失败；运行期也保留开发期错误提示分支，不能把资源缺失标记为 PASS。
```

---

## 6. 测试结果

已通过：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorDemoTest' --tests 'com.childai.companion.ui.chat.ChildCompanionPageRulesTest' --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*'
```

覆盖：

```text
1. Demo 激活时普通 opening 延后。
2. 退出 Demo 后普通 opening 可恢复请求。
3. 首屏 UI 模型显示两个入口按钮。
4. S1 资源 key 能解析到 Android drawable。
5. Demo 激活时普通 InputBar 不显示。
6. 点击两个入口能进入 PhotoPrompt / RiddlePrompt 本地状态。
7. 禁止词测试继续覆盖 D2 新增可见文案。
8. Android debug 构建通过。
```

---

## 7. 截图

本轮未产出真机截图。

原因：

```text
当前 doctor_local_env 显示 adb devices WARN：没有连接真机。
```

---

## 8. 风险点

```text
1. D2 未做真机视觉 QA，横屏和平板布局仍需 Q1 或 D2 后真机截图确认。
2. “拍给小白狐看”在 D2 不启动真实流程，D3 必须接入现有 attachment 链路后才能验收拍照路径。
3. 怪问题 D2 只做静态展示，D4 需要接 voice-first 回答和 evaluator。
4. 资源缺失在构建期会直接失败，不能用 fallback 冒充正式素材可用。
```

---

## 9. 是否可进入 D3

结论：

```text
可以进入 D3：拍照变身路径。
```

D3 建议只做：

```text
1. 复用现有 attachment 链路。
2. 继续使用 image_purpose=share。
3. 将识别结果接入 StrangeDoorPhotoTransformMapper。
4. 展示“现实物品 -> 奇怪道具 -> 小门反馈”。
5. 推进本地 door state。
```

D3 仍不得新增后端 endpoint、strange_door image purpose、奖励积分等级或复杂道具系统。
