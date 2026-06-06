# R1-C：奇怪小门首屏视觉层级交接

日期：2026-06-06

执行角色：开发执行会话

任务范围：只优化奇怪小门首屏视觉层级，让孩子打开 App 后 3 秒内看懂“小白狐被奇怪小门挡住了，我可以帮它”；不新增功能。

---

## 1. 本轮结论

R1-C 已完成代码侧优化，状态为：

```text
CODE PASS / 待真机视觉验收
```

已按主控确认后的边界落地：

```text
1. 首屏 ChoosingMethod 使用专用视觉布局。
2. closed 状态小门在首屏中更大。
3. 圆锁在首屏中加大。
4. 地面阴影在首屏中加宽加厚，让门更像站在小屋里。
5. 小白狐相对门向侧后方靠近，门仍在前景遮挡小白狐。
6. 小白狐、门、气泡和两个按钮在首屏形成更集中的事件画面。
7. 小展台入口和家长入口在首屏弱化。
8. “找东西帮忙”首屏按钮高度和字重强于“动脑试试”。
```

---

## 2. 修改文件

修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChildCompanionPageRulesTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
```

新增：

```text
docs/session_process/handoffs/20260605_R1C_strange_door_home_visual_handoff.md
```

未修改：

```text
backend/
android/app/src/main/res/drawable-nodpi/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/ui/parent/
StrangeDoorPhotoTransformMapper 词池
StrangeDoorDoorStateReducer 门状态节奏
R1-B 拍照结果视觉合同
M1 / M2 相关逻辑
```

---

## 3. 行为变化

儿童端首屏可见变化：

```text
1. 首屏横屏 / 竖屏都有专用布局，不再完全沿用后续流程页结构。
2. 门和小白狐的距离更近，视觉上更像一个事件。
3. 竖屏中气泡贴近门和小白狐画面上方，不再像普通聊天卡片。
4. 横屏中门和小白狐占左侧更大区域，气泡和按钮贴近右侧，不让平板横向空间把事件拆散。
5. 小展台入口和家长入口透明度降低，保持弱入口。
6. “找东西帮忙”首屏按钮更高、更突出。
```

未改变：

```text
1. 不新增儿童端文案。
2. 不新增素材。
3. 不改拍照链路。
4. 不改怪问题链路。
5. 不改小展台保存。
6. 不改后端。
7. 不新增奖励、积分、任务、通关或地图。
8. 不提交真实儿童截图或私有测试材料。
```

---

## 4. 视觉合同

新增展示标记：

```text
showHomeIntroVisual
```

处理方式：

```text
1. ChoosingMethod / NotStarted 首屏 showHomeIntroVisual=true。
2. PhotoPrompt / PhotoResult / Riddle / ShowcaseSaved 不使用首屏专用布局。
3. 首屏专用布局只影响视觉层级，不改变状态机和按钮行为。
```

首屏参数：

```text
1. 首屏门宽占比高于后续流程页。
2. 首屏圆锁比例高于后续流程页。
3. 首屏地面阴影比例高于后续流程页。
4. 首屏小白狐与门的中心距离保持较近。
5. 首屏第一按钮高度高于第二按钮。
```

---

## 5. 安全和 public repo 边界

已落实：

```text
1. 不提交 .env、API key、token 或生产凭据。
2. 不提交真实儿童姓名、真实家庭信息、原始儿童音频、原始儿童照片。
3. 不提交私有截图、原始聊天转录、prompt trace、本地数据库、模型权重或 TTS cache。
4. 本轮未新增截图 / 录屏入库。
```

---

## 6. 测试结果

已通过：

```bash
git diff --check
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*' --tests 'com.childai.companion.ui.chat.ChildCompanionPageRulesTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest'
bash scripts/android_gradle.sh assembleDebug
```

覆盖：

```text
1. 首屏模型启用 showHomeIntroVisual。
2. PhotoPrompt 等后续状态不启用首屏视觉布局。
3. 首屏门、圆锁、地面阴影参数更突出。
4. 小白狐与门保持视觉关联。
5. 首屏小展台 / 家长入口弱化。
6. 首屏“找东西帮忙”按钮强于“动脑试试”。
7. strangedoor 相关测试通过。
8. D3 拍照路径回归通过。
9. D4 怪问题路径回归通过。
10. D5 小展台承接回归通过。
11. R1-A 门状态节奏不变。
12. R1-B 拍照结果视觉合同不破。
```

---

## 7. 截图 / 录屏

本轮未产出截图或录屏。

原因：

```text
当前按 public repo 标准，不提交私有测试材料；本轮先完成代码侧布局说明与构建验证。
```

---

## 8. 风险点

```text
1. 首屏是否 3 秒内看懂“小白狐被门挡住”，仍需要 Redmi K60 和 Honor Pad 5 真机视觉确认。
2. 竖屏气泡靠近画面上方，真机上需确认不会遮挡小门主体。
3. 横屏平板上右侧气泡和按钮与左侧小门的距离已收紧，但事件整体感仍需主观验收。
4. 家长入口和小展台入口已弱化，需确认仍能被成人找到。
```

---

## 9. 是否需要真机视觉确认

结论：

```text
需要。
```

建议重点确认：

```text
1. Redmi K60 首屏是否不拥挤，门是否足够大。
2. Redmi K60 按钮是否不被系统栏挤压。
3. Honor Pad 5 横屏下门和小白狐是否没有分散。
4. 小白狐是否明显像被门挡住。
5. “找东西帮忙”是否明显强于“动脑试试”。
```
