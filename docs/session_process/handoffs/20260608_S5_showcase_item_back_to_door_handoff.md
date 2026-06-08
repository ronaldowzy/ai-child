# S5：用小展台的小发现帮忙交接

日期：2026-06-08

执行角色：开发执行会话

状态：CODE PASS / 待合并真机验收

---

## 1. 本轮结论

S5 已按主控确认范围完成 Android 本地实现：

```text
1. PhotoPrompt 按钮顺序调整为：拍给小白狐看 / 用小展台里的 / 先换个办法。
2. 新增“选一个小发现”选择模式页面，复用 S2 卡片视觉，但不改变普通小展台列表与详情。
3. 选择已有展品后回到奇怪小门，进入 ShowcaseItemResult，本地展示旧物帮忙反馈。
4. 旧物帮忙按 Closed -> Cracked、Cracked -> AlmostOpen、AlmostOpen -> Open 推进；Open 后收束到 S3 Completed。
5. 本轮未改后端、数据表、GrowthEvent、小展台 item、怪问题路径或小展台保存路径。
```

---

## 2. 修改文件

```text
android/app/src/main/java/com/childai/companion/ui/AppNavHost.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorShowcaseAssistMapper.kt
android/app/src/main/java/com/childai/companion/ui/showcase/XiaozhantaiScreens.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelStrangeDoorShowcaseTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorForbiddenWordsTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorHomeEventUiModelTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorStateContractTest.kt
android/app/src/test/java/com/childai/companion/ui/showcase/XiaozhantaiGalleryContractTest.kt
docs/session_process/handoffs/20260608_S5_showcase_item_back_to_door_handoff.md
```

未修改：

```text
backend/
android/app/src/main/java/com/childai/companion/data/showcase/XiaozhantaiModels.kt
android/app/src/main/java/com/childai/companion/data/showcase/XiaozhantaiRepository.kt
android/app/src/main/java/com/childai/companion/data/growth/
android/app/src/main/res/drawable-nodpi/
docs/assets/
```

---

## 3. 行为变化

### 3.1 PhotoPrompt

按钮顺序为：

```text
拍给小白狐看
用小展台里的
先换个办法
```

首屏仍只保留：

```text
找东西帮忙
动脑试试
```

### 3.2 选择模式

新增 AppNavHost 本地目的地：

```text
XiaozhantaiPickForStrangeDoor
```

选择页标题：

```text
选一个小发现
```

空小展台显示：

```text
小展台还空空的
我们先找一个东西拍给小白狐看
```

空态只显示两行文案和顶栏“关上”，不额外提供拍照按钮。

### 3.3 旧物帮忙结果

新增本地状态：

```text
StrangeDoorDemoState.ShowcaseItemResult
StrangeDoorDemoMethod.Showcase
StrangeDoorShowcaseAssistResult
```

选择展品后显示：

```text
{name} 又来帮忙啦

小白狐把它轻轻放到门前
{小门反应}
```

小门反应只从 R1-A 已批准轻推进词池中确定性选择。

旧物帮忙结果页按钮只显示：

```text
再找一个
动脑试试
```

不显示“放进小展台”。

### 3.4 门状态推进

```text
Closed -> Cracked：显示 ShowcaseItemResult。
Cracked -> AlmostOpen：显示 ShowcaseItemResult。
AlmostOpen -> Open：进入 S3 Completed。
Open：不暴露“用小展台里的”入口。
```

旧物帮忙不强匹配 Round / Soft / Shiny。

---

## 4. 范围与安全

本轮保持：

```text
1. 不新增后端接口。
2. 不新增数据表。
3. 不新增 GrowthEvent。
4. 不修改 XiaozhantaiItem。
5. 不新增小展台 item 副本。
6. 不写入历史。
7. 不改怪问题路径。
8. 不改小展台保存路径。
9. 不改 S2 普通小展台列表与详情行为。
10. 不新增背包、道具属性、等级、稀有度、装备、奖励、积分、地图、任务、连续打卡或图鉴。
11. 不提交真实儿童测试材料。
```

---

## 5. 测试结果

已运行：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest' --tests 'com.childai.companion.ui.showcase.XiaozhantaiGalleryContractTest'
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
```

结果：

```text
PASS，均为 BUILD SUCCESSFUL。
```

`doctor_local_env.sh` 结果：

```text
JDK OK
Android SDK OK
adb OK
adb devices WARN：no connected physical Android device
```

---

## 6. 覆盖项

已覆盖：

```text
1. PhotoPrompt 按钮顺序为：拍给小白狐看 / 用小展台里的 / 先换个办法。
2. Completed 状态不显示“用小展台里的”。
3. S5 选择模式标题为“选一个小发现”。
4. S5 空状态显示两行主控文本。
5. 普通小展台入口仍显示“我的小展台”。
6. 普通小展台点击 item 的详情路径未改。
7. 选择模式点击 item 由 AppNavHost 回到 ChatScreen，并调用 ChatViewModel 本地旧物帮忙入口。
8. 选择 item 后进入 ShowcaseItemResult。
9. ShowcaseItemResult 显示旧物帮忙反馈。
10. 旧物帮忙 Closed -> Cracked。
11. 旧物帮忙 Cracked -> AlmostOpen。
12. 旧物帮忙 AlmostOpen -> Open 后进入 S3 Completed。
13. 旧物帮忙不新增 GrowthEvent。
14. 旧物帮忙不调用小展台保存用例，不修改 XiaozhantaiItem，不新增副本。
15. 怪问题路径不变。
16. 小展台保存路径不变。
17. 新增文案进入禁止词测试。
18. D3 / D4 / D5 / S2 / S3 / S4 相关回归未破。
19. assembleDebug 通过。
```

---

## 7. 风险点

```text
1. 本轮没有真机验收，选择页返回奇怪小门后的实际动画与语音节奏仍需合并真机测试。
2. 旧物帮忙的门反应为确定性本地选择，不写历史；同一展品重复使用会得到相同门反应。
3. 选择页复用 S2 卡片视觉，但空态按主控要求隐藏插画；需真机确认空态是否过于轻。
4. ChatViewModel 已上提到 AppNavHost 的 when 外，范围仅用于 ChatScreen 与选择页共享同一 Demo 状态。
```

---

## 8. 是否需要合并真机验收

需要。

建议随 D1-D5 + R1-A/R1-B/R1-C + S2 + S3 + S4 合并真机验收一起验证：

```text
1. PhotoPrompt 中“用小展台里的”是否清楚但不抢拍照主玩法。
2. 空小展台时点击“关上”是否自然回到 PhotoPrompt。
3. 选择已有展品后是否能理解“以前的小发现又回来帮忙”。
4. 旧物帮忙推进门状态是否明显。
5. 普通小展台列表和详情是否仍保持 S2 行为。
```
