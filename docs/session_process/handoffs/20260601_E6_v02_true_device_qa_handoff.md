# E6 交接：V0.2 真机 QA

状态：BLOCKED

更新时间：2026-06-02

---

## Summary

E6 已完成首轮真机验收，当前不能进入家庭测试。真机与真实后端链路确认了 3 件事：第一，首次 seed 小星点与 recall opening 在 Android 上都能出现；第二，拍照入口可真实拉起相机并成功上传；第三，当前核心阻塞不在“有没有接通”，而在“接通后走错了链路”。主要阻塞有 4 个：图片成功后的真实文案与按钮集合不符合 V0.2 设计；Android 点击 `起个名字` 实际上发的是 `give_name`，后端 seed 创建逻辑吃的是 `companion_name`，导致真机起名后不会进入小客人创建链路；`companion_objects` 表缺少 `visual_kind` 列，真实持久化失败，只能回退到进程内存；`加一个朋友` 也没有走到 E5 设计要求的三按钮确定性引导，而是落回普通开放对话。

---

## 1. 环境与设备

```text
仓库分支：main（已同步最新 origin/main）
doctor_local_env.sh：通过
后端服务：bash scripts/status_backend_services.sh -> running, port=8000, health=ok
真机设备：Honor Pad 5（adb 可用）
Redmi K60：本轮未接入 adb，未完成手机真机补测
```

---

## 2. 真机执行范围

本轮实际执行了：

```text
1. 平板真机首次 opening / seed 小星点可见性检查
2. 平板真机“给小白狐看看”入口检查
3. 平板真机拍照成功后返回结果检查
4. 后端真实 attachments/images 返回内容核对
5. Android 点击“起个名字”后的真实请求链路核对
6. 受控测试孩子下的 recall 开场真机呈现核对
7. “加一个朋友”真机点击后的真实后续链路核对
```

本轮未完成或仅部分完成：

```text
1. 图片失败路径真机复现
2. 6 种 visual_kind 全量真机区分
3. 家长端轻共创区块完整真机复核
4. Redmi K60 手机补测
```

---

## 3. 关键结论

### 3.1 已确认正常的部分

#### A. 首次 seed 小星点真实可见

新建全新测试孩子后，平板真机能看到 seed 小光点，opening 也真实触发。

证据：

```text
docs/session_process/handoffs/e6_screenshots/e6_after_image_tap_01.png
docs/session_process/handoffs/e6_screenshots/e6_after_image_tap_01.xml
docs/session_process/handoffs/e6_screenshots/e6_after_capture_live.png
```

#### B. 拍照入口真实可用

`给小白狐看看 -> 拍一张照片` 可真实拉起华为相机；拍照后后端收到真实图片上传。

证据：

```text
docs/session_process/handoffs/e6_screenshots/e6_camera_attempt_01.png
backend.log 中 192.168.0.144 的 /api/v1/attachments/images 200 OK
```

#### C. recall opening 在 Android 上可真实出现

对一个受控“已有 active 小客人”的测试孩子，Android 真机 opening 可收到：

```text
小棉花今天在窗边呢 要不要给它加一个朋友？
按钮：加一个朋友 / 先聊别的
```

证据：

```text
docs/session_process/handoffs/e6_screenshots/e6_recall_newchild_8s.xml
```

说明：同时间点的 PNG 截图没有稳定截到气泡与按钮，但 XML 已明确记录真机 UI 结构，且后端 opening 返回与 XML 一致。

---

### 3.2 明确阻塞项

#### 阻塞 1：图片成功后的真实文案与按钮集合不符合 V0.2 设计

V0.2 设计要求：

```text
我看到{细节}啦
像{温柔想象}
要不要给它起个名字？
只出现一个按钮：起个名字
不出现“编个小故事”
```

真实后端返回不是这样，而是泛化说明文案，且返回了 3 个按钮：

```json
{
  "reply": {
    "text": "我看到像是图片显示一个书桌的角落。你可以给它起个名字，或者告诉我发生了什么。"
  },
  "ui_actions": [
    {
      "actions": [
        {"id": "give_name", "label": "起个名字"},
        {"id": "tell_story", "label": "讲个故事"},
        {"id": "say_what_happened", "label": "说说看"}
      ]
    }
  ]
}
```

证据：

```text
docs/session_process/handoffs/e6_screenshots/e6_current.xml
  - 真机气泡文字：我看到像是图片展示了一个家具内部（如抽屉或柜子）的视角。你可以给它起个名字，或者告诉我发生了什么。

本地真实接口复跑：
  /api/v1/attachments/images
  返回 give_name / tell_story / say_what_happened
```

结论：

```text
后端 attachments/images 成功路径没有收口到 E3 / V0.2 的确定性模板。
Android 虽然部分过滤掉了额外按钮，但后端真实合同仍不符合设计。
```

#### 阻塞 2：Android 点击“起个名字”发错 quick_action_id，真机不会创建小客人

Android 真机点击 `起个名字` 后，日志显示：

```text
ChatViewModel: continuePendingImageConversation: action=give_name, hasContext=true
```

也就是设备发出的动作标识是：

```text
quick_action_id = give_name
```

而后端 seed 创建逻辑识别的是：

```text
quick_action_id = companion_name
```

用真实后端复跑两条对比链路：

1. 设备当前实际链路：

```text
give_name -> “你想叫它什么呀？”
再说“叫小棉花” -> 普通开放回复
没有返回 companion_object
没有创建真 recall 能力
```

2. 受控正确链路：

```text
companion_name -> pending seed naming
再说“叫小棉花” -> 返回 session_state.companion_object(state=active, action=co_create)
随后 reopening -> recall opening 成立
```

证据：

```text
adb logcat:
  continuePendingImageConversation: action=give_name, hasContext=true

本地真实接口复跑：
  give_name 路径没有创建 companion_object
  companion_name 路径可以创建 companion_object，并能在 reopening 返回 recall
```

结论：

```text
这不是感知问题，而是 Android / backend action contract 不一致。
当前真机路径下，“起个名字 -> 小物件落到小屋”主链路实际断裂。
```

#### 阻塞 3：companion_objects 真实持久化不可用

本地直接访问真实仓库时，SQL 报错：

```text
column companion_objects.visual_kind does not exist
```

说明当前真实数据库 schema 落后于代码，`CompanionObjectService` 会在 save/list/get_active 时回退到进程内内存仓库。

影响：

```text
1. active 小客人不是可靠持久化
2. 后端重启后 recall 可能丢失
3. “第二天再打开”当前不能视为真实可验
4. 家长端轻共创区块若依赖真实 active 记录，也不能判定为真实通过
```

证据：

```text
conda run -n child-ai python ...
  CompanionObjectRepositoryUnavailable:
  column companion_objects.visual_kind does not exist
```

结论：

```text
这是 E6 的基础设施级阻塞。
即使 Android action id 修正，若不补 migration，active companion 仍不可作为真实持久能力验收通过。
```

#### 阻塞 4：“加一个朋友”没有进入 E5 设计要求的三按钮确定性引导

设计要求：

```text
那我们给它找一个小伙伴
你可以说一个名字，也可以给我看看

按钮：
说个名字
给小白狐看看
先聊别的
```

真实情况：

1. 真机点击 `加一个朋友`，确实发出了后续请求
2. 但没有进入三按钮引导，而是停在普通后续状态
3. 本地真实接口复跑 `quick_action_id=companion_continue` 也返回普通开放对话：

```text
加朋友呀！是在游戏里加的，还是学校里交了新朋友？
```

且返回的是普通 topic_choice_* quick actions，不是 E5 指定的 3 个 extension quick actions。

证据：

```text
adb logcat:
  sendText: textLength=5
  stage=request_send textLen=5
  stage=stream_done

本地真实接口复跑：
  companion_continue -> 普通开放回复
  ui_actions -> topic_choice_1 / topic_choice_2 / topic_choice_3
```

结论：

```text
E5 代码设计没有真实落到当前运行链路，或者当前链路被普通对话分支盖掉了。
```

#### 阻塞 5：相册入口异常

`给小白狐看看 -> 从相册选` 在 Honor Pad 5 上没有进入正常相册 / 图片选择器，而是跳到了：

```text
com.huawei.systemmanager/.mainscreen.MainScreenActivity
```

证据：

```text
docs/session_process/handoffs/e6_screenshots/e6_album_attempt_02.png
docs/session_process/handoffs/e6_screenshots/e6_album_picker_01.xml
```

结论：

```text
拍照路径可用，但相册路径当前不能算 PASS。
这会直接影响 E6 第 8 条“加朋友图片路径”验收。
```

---

## 4. 验收项逐条结果

### 4.1 图片成功后

```text
模板三句：FAIL
只出现一个按钮：后端 FAIL，设备表面上部分收口
不出现“上传成功/识别成功/图片分析结果”：PASS
不出现“编个小故事”：设备侧 PASS，后端合同 FAIL（仍返回 tell_story）
```

### 4.2 图片失败后

```text
本轮未完成真机稳定复现：UNVERIFIED
```

### 4.3 起名成功后

```text
真机主链路：FAIL
原因：设备发 give_name，后端不进入 seed 创建

受控正确动作标识路径：
  companion_name -> 可进入 co_create
  但回复文本仍未完全满足“它轻轻落到窗边啦 / 无 quick_actions”设计
```

### 4.4 Android 小物件影子

```text
seed 小星点：PASS（真机可见）
recall 位置小物件：PARTIAL（XML 已到达 companion_object / recall opening，但视觉强度仍偏弱）
6 种 visual_kind 全量区分：UNVERIFIED
```

### 4.5 第二天 / reopen recall

```text
同后端进程内受控 active companion：PASS（真实 opening 返回 recall）
Android 真机 reopen：PASS（XML 抓到）
第二天真实持久化：BLOCKED（数据库 schema 不完整，不能视为真实可持续）
```

### 4.6 加一个朋友

```text
FAIL
未进入三按钮确定性引导
```

### 4.7 加朋友说名字路径

```text
未进入 extension 引导，无法继续真机验收：BLOCKED
```

### 4.8 加朋友图片路径

```text
拍照入口：PASS
相册入口：FAIL
extension 入口本身未成立：BLOCKED
```

### 4.9 跳过

```text
“先聊别的”本轮未完成稳定真机复核：UNVERIFIED
```

### 4.10 家长端

```text
未完成真实轻共创摘要复核：BLOCKED
根因：active companion 当前不具备真实持久化保障
```

---

## 5. 真机证据文件

```text
docs/session_process/handoffs/e6_screenshots/e6_after_image_tap_01.png
docs/session_process/handoffs/e6_screenshots/e6_after_image_tap_01.xml
docs/session_process/handoffs/e6_screenshots/e6_camera_attempt_01.png
docs/session_process/handoffs/e6_screenshots/e6_after_capture_live.png
docs/session_process/handoffs/e6_screenshots/e6_current.xml
docs/session_process/handoffs/e6_screenshots/e6_image_success_actual.xml
docs/session_process/handoffs/e6_screenshots/e6_recall_newchild_8s.xml
docs/session_process/handoffs/e6_screenshots/e6_add_friend_after_tap2.xml
docs/session_process/handoffs/e6_screenshots/e6_album_attempt_02.png
```

说明：

```text
部分 PNG 未稳定截到 opening 气泡的瞬时状态，但对应 XML 已保留 UI 结构证据。
本轮 XML 比 PNG 更可靠。
```

---

## 6. 建议的小修项（等待主控确认后再修）

### 小修 1：收口图片成功确定性模板

目标：

```text
attachments/images 成功路径统一为：
我看到{细节}啦
像{温柔想象}
要不要给它起个名字？
只返回一个 quick_action：companion_name
```

预估文件：

```text
backend/app/services/modality_manager.py
backend/app/services/attachment_service.py
backend/app/tests/test_attachment_api.py
```

### 小修 2：统一 Android -> backend quick_action_id

目标：

```text
设备点击“起个名字”时，发 companion_name，不再发 give_name
并检查 recall / add-friend 相关动作 id 是否也都用主控批准的合同值
```

预估文件：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/test/...
```

### 小修 3：补 companion_objects migration

目标：

```text
给真实数据库补 visual_kind 列，恢复真实持久化
```

预估文件：

```text
backend/app/db/models.py
backend/migrations/...（以当前仓库实际迁移方案为准）
```

### 小修 4：收口 companion_continue 到 E5 extension

目标：

```text
companion_continue 必须稳定进入：
那我们给它找一个小伙伴
你可以说一个名字，也可以给我看看

按钮：
说个名字
给小白狐看看
先聊别的
```

预估文件：

```text
backend/app/services/conversation_service.py
backend/app/tests/test_add_friend_extension.py
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt（如需动作映射收口）
```

### 小修 5：修复 Honor Pad 5 相册入口

目标：

```text
“从相册选”必须拉起标准图片选择器，而不是华为平板管家
```

预估文件：

```text
android/app/src/main/java/com/childai/companion/ui/chat/...
AndroidManifest.xml（如需 intent/filter/permission 校正）
```

---

## 7. 结论

当前 E6 不能判 PASS，也不适合进入家庭测试。

最关键的判断：

```text
1. 可见共创的“显示层”已经部分接通：seed 小星点、拍照、recall opening 都能在真机上出现。
2. 但“核心交互合同”没有收口：图片成功模板不对、起名动作 id 不对、加朋友延续不对。
3. companion_objects 真实持久化也还没打通，导致“第二天召回 / 家长端摘要”不能算真实通过。
```

因此本轮状态维持：

```text
BLOCKED
```
