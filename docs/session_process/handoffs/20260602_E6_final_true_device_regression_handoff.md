# E6 最终真机回归交接

状态：CONDITIONAL

更新时间：2026-06-03

---

## Summary

本轮只处理 E6 阻塞修复后的最终真机回归，没有新增玩法、没有新增儿童文案、没有改家长端边界。核心结果有两点：第一，本机图片上传能力没有被全局删掉，而是按设备降级，Honor Pad 5 继续隐藏相册入口，其他普通 Android 设备仍保留 `从相册选`；第二，`起个名字 -> 说名字 -> 小物件落到小屋` 这条链路已在 Honor Pad 5 上打通，当前界面能肉眼看到小物件影子。

这轮补出的真实根因不是后端没创建，而是 Android 的 `起个名字` 之前会立刻把按钮标签当普通文本送出去，导致 seed 起名上下文在设备端被提前打散；后端随后收到的“叫小棉花”就落成普通开放对话，页面自然看不到 `co_create` 的视觉变化。现在 Android 已改成把 `companion_name` / `companion_friend_name` 延迟到孩子真正说出名字时再一并上报，后端也补了同轮消费逻辑，确保 `session_state.companion_object` 和 `state=active, action=co_create` 能在同一轮落地。

Honor Pad 5 真机当前能确认 4 个事实：一，seed 小星点可见；二，Honor 设备只保留 `拍一张照片`，不会再跳异常系统页；三，点击 `起个名字` 后不会再误发普通文本；四，说出名字后当前界面能看到落到窗边的小星星影子。还保留一个验收缺口：本轮没有接入 Redmi K60 做同一版真机复拍，因此虽然代码规则和单测已确认普通手机仍显示 `从相册选`，但 Redmi K60 的补图证据仍缺，结论保持 `CONDITIONAL`，不直接写成 `PASS`。

---

## 1. 本机图片上传入口回归

### 1.1 当前设备降级规则

Android 端现在不是全局删除相册入口，而是设备级降级：

```text
文件：
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt

规则：
1. 设备指纹包含 jdn2 -> 隐藏相册入口
2. 设备指纹同时包含 honor 和 pad -> 隐藏相册入口
3. 其他设备 -> 保留相册入口
```

也就是：

```text
Honor Pad 5：隐藏“从相册选”，只保留拍照
Redmi K60：应保留“从相册选”
普通 Android 手机：应保留“从相册选”
```

### 1.2 代码与测试确认

相关测试：

```text
android/app/src/test/java/com/childai/companion/ui/chat/InputBarVoiceFirstTest.kt
```

本轮确认了：

```text
1. Honor Pad 5 指纹 -> false
2. Redmi K60 指纹 -> true
3. 普通 Pixel 手机指纹 -> true
```

### 1.3 Honor Pad 5 真机现状

Honor Pad 5 当前真机入口截图：

```text
docs/session_process/handoffs/e6_screenshots/20260602_honor_image_entry_camera_only_live.png
```

可见：

```text
1. 只显示“拍一张照片”
2. 显示“先不看”
3. 不再显示“从相册选”
4. 不会跳到异常系统页面
```

### 1.4 Redmi K60 当前状态

本轮未接入 Redmi K60 真机，所以没有新增截图。当前只能确认：

```text
1. 代码规则未对 Redmi K60 做降级
2. Android 单测明确覆盖 Redmi K60 仍显示 gallery picker
3. Redmi K60 真机补图仍待下一轮现场接入
```

---

## 2. 起名后小物件不出现的真实根因

### 2.1 之前为什么看不到

真实根因有两层：

```text
1. Android 之前点“起个名字”时，会立刻发送按钮标签，打散 seed 起名上下文。
2. XiaobaohuCompanionStage 的小物件虽然有渲染逻辑，但窗边位置偏上、偏淡，和 opening 气泡区挤在一起，真机上很容易“存在但感知不到”。
```

第一层导致：

```text
后端收到的是普通开放对话，而不是“pending seed naming + 真正名字输入”
```

第二层导致：

```text
即使 companionObject 已存在，视觉也不够显眼
```

### 2.2 本轮修复内容

Android：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt
```

后端：

```text
backend/app/services/conversation_service.py
```

具体修复：

```text
1. companion_name / give_name / image_naming / companion_friend_name 改为延迟 quick action
2. 孩子真正说出名字时，再把 quick_action_id 一并发给后端
3. 后端支持同轮 quick_action_id + 名字文本直接完成创建
4. 小物件视觉拆成后景光晕 + 前景形体两层
5. co_create 提升 alpha、glow、shape scale
6. 窗边位置从顶部挪到更靠中部的可见区域
```

---

## 3. 起名成功链路复核

### 3.1 后端是否真实创建了 active 小客人

是。当前联调库里，Honor Pad 5 新建测试孩子 `child_498ee226bf584095` 已真实创建：

```text
name = 小棉花
status = active
object_type = star
visual_kind = star
light_location = 窗边
created_at = 2026-06-02 23:42:24+08
```

说明：

```text
不是 mock
不是只回了文案
不是只存在进程内存
```

### 3.2 起名成功后是否返回了 co_create 语义

是。真实会话里已经出现：

```text
小棉花，软软的名字
它轻轻落到窗边啦
```

本轮还补了同轮创建测试，锁住：

```text
quick_action_id = companion_name
child_text = 名字
=> 直接进入创建链路
=> companion_object.state = active
=> companion_object.action = co_create
```

后端测试：

```text
backend/app/tests/test_companion_object_runtime.py::TestCompanionSeedNaming::test_quick_action_name_with_name_text_creates_in_same_turn
```

### 3.3 Android 是否把 sessionState 真正写入并渲染

是。当前链路已经覆盖：

```text
1. ChatViewModel.sendText() 会把延迟 quick action 带到真实名字输入
2. response.session_state 会写回 uiState.sessionState
3. XiaobaohuCompanionStage 会真实收到 companionObject
4. CompanionObjectMeta.shouldShowVisual() 对 active + co_create 返回 true
5. Compose 中会进入 CompanionLightPointBackdrop / Foreground
```

相关测试：

```text
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelOpeningTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/CompanionObjectVisualTest.kt
```

---

## 4. Honor Pad 5 真机证据

### 4.1 seed 小星点可见

截图：

```text
docs/session_process/handoffs/e6_screenshots/20260602_honor_seed_opening_after_wait.png
```

结论：

```text
首次 opening 时，窗边小星点在真机上可见
```

### 4.2 “起个名字”不再误发普通文本

截图：

```text
docs/session_process/handoffs/e6_screenshots/20260602_honor_name_action_deferred.png
```

配合 logcat 可确认：

```text
点击“起个名字”后，没有立刻发送普通 child text
```

### 4.3 起名后小物件真机可见

截图：

```text
docs/session_process/handoffs/e6_screenshots/20260602_honor_name_success_visual_visible.png
```

结论：

```text
说出名字后，窗边星形影子在当前界面可肉眼看到
```

说明：

```text
这张截图截到的是“起名完成后小物件仍留在小屋里”的状态。
回复气泡在这张图里已淡出，但视觉点仍稳定可见。
```

### 4.4 当前设备已恢复原登录态

截图：

```text
docs/session_process/handoffs/e6_screenshots/20260602_honor_restore_wzy.png
```

说明：

```text
用于验证后，我已把 Honor Pad 5 从临时测试孩子恢复回原来的 wzy 登录态
```

---

## 5. 自动化测试

后端：

```text
conda run -n child-ai pytest \
  backend/app/tests/test_companion_object_runtime.py::TestCompanionSeedNaming::test_quick_action_name_with_name_text_creates_in_same_turn \
  backend/app/tests/test_add_friend_extension.py::TestExtensionImmediateNaming::test_quick_action_friend_name_with_name_text_completes_extension -q

结果：2 passed
```

Android：

```text
bash scripts/android_gradle.sh testDebugUnitTest \
  --tests com.childai.companion.ui.chat.ChatViewModelOpeningTest \
  --tests com.childai.companion.ui.chat.CompanionObjectVisualTest \
  --tests com.childai.companion.ui.chat.InputBarVoiceFirstTest

结果：BUILD SUCCESSFUL
```

构建：

```text
bash scripts/android_gradle.sh assembleDebug

结果：BUILD SUCCESSFUL
```

---

## 6. 修改文件

本轮实际新增或修改：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelOpeningTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/CompanionObjectVisualTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/InputBarVoiceFirstTest.kt
backend/app/services/conversation_service.py
backend/app/tests/test_add_friend_extension.py
backend/app/tests/test_companion_object_runtime.py
docs/session_process/handoffs/20260602_E6_final_true_device_regression_handoff.md
docs/session_process/handoffs/e6_screenshots/20260602_honor_image_entry_camera_only_live.png
docs/session_process/handoffs/e6_screenshots/20260602_honor_seed_opening_after_wait.png
docs/session_process/handoffs/e6_screenshots/20260602_honor_name_action_deferred.png
docs/session_process/handoffs/e6_screenshots/20260602_honor_name_success_visual_visible.png
docs/session_process/handoffs/e6_screenshots/20260602_honor_restore_wzy.png
```

---

## 7. 当前结论

### 已确认通过

```text
1. Honor Pad 5 设备级隐藏相册入口，而不是全局删除
2. 普通 Android 手机代码路径仍保留“从相册选”
3. “起个名字”不会再误发普通开放对话
4. 起名成功后，Honor Pad 5 当前界面能看到小物件影子
```

### 仍未补齐

```text
1. Redmi K60 本轮未接入，缺少“从相册选仍保留”的真机截图
2. Redmi K60 本轮未补拍“起名后小物件可见”截图
```

因此本轮状态保持：

```text
CONDITIONAL
```

