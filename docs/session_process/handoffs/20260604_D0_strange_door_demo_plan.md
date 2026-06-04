# D0：奇怪小门 Demo 开发计划评审

日期：2026-06-04

执行角色：开发执行会话

任务边界：本轮只输出计划，不编码、不接素材、不改 UI、不改后端。

---

## 0. 已同步和已读依据

已执行：

```bash
git fetch origin main
git pull --ff-only origin main
bash scripts/doctor_local_env.sh
```

环境检查结果：

```text
conda child-ai OK
JDK 17 OK
Android SDK OK
adb OK
db migration OK
adb devices WARN：当前没有连接真机
LAN IP：192.168.0.101
```

已阅读：

```text
README.md
AGENTS.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
docs/PRODUCT_DECISIONS_V0_1.md
docs/项目现状与后续路线图_V0_2.md
docs/提示词与文案归属规则_V0_1.md
docs/child_engagement_strange_door_demo.md
docs/奇怪小门儿童吸引力试玩原型深化设计_2026_06_04_V0_1.md
docs/奇怪小门Demo实施总计划_2026_06_04_V0_1.md
```

发现的文档口径差异：

```text
docs/CODEX_PROGRESS_BOARD_V0_1.md 当前仍写下一步启动“小屋小客人”D1。
2026-06-04 新增的三份奇怪小门文档和本次主控提示已明确切到“奇怪小门 Demo”。
本 D0 计划按本次主控提示和 2026-06-04 三份新文档执行；本轮不更新进度板。
```

---

## 1. 当前首页 / 小屋 UI 如何接入“奇怪小门”今日事件

当前 Android 儿童端没有独立首页，孩子登录后进入 `ChildChatScreen`。当前首屏由以下部分组成：

```text
ChildChatScreen
-> ParentEntryHintBar：小展台入口、家长入口
-> AgentPanel
   -> XiaobaohuCompanionStage：小屋背景、小白狐、轻小物件
   -> CompanionFloatingConversationBubbles：近一轮对话气泡
   -> XiaozhantaiSavePromptBubble：小展台保存提示
-> QuickActionsRow
-> InputBar：语音、停止朗读、静音、图片入口
```

接入建议：

```text
1. 不新建第二个“首页”页面。
2. 在现有 ChildChatScreen 的 AgentPanel / XiaobaohuCompanionStage 上接入“今日事件层”。
3. 今日事件层在 Demo 激活时拥有首屏优先级，压过普通 opening 气泡和普通 quick actions。
4. 小展台入口、家长入口保留在弱入口位置，不改家长端。
5. 首屏底部使用奇怪小门的两个主控按钮，不展示一排普通功能按钮。
```

首屏展示文本只能使用主控文档中已给出的文本：

```text
标题：
奇怪小门挡住了小白狐

小白狐气泡：
你来得正好
我被这扇奇怪小门挡住了

它说：
找一个圆圆的东西
或者答对一个怪问题

按钮：
找东西帮忙
动脑试试
```

实现位置建议：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt
新增 android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoPanel.kt
```

关键取舍：

```text
普通 opening greeting 不能在首屏抢走“奇怪小门”事件。
建议 D1/D2 由主控确认：Demo 激活时是延后 requestOpeningGreeting，还是仍请求但不渲染为首屏主气泡。
```

---

## 2. Demo 状态放 Android 本地、后端还是混合

建议采用混合，但 Demo 进度状态以 Android 本地为主：

```text
Android 本地：
- StrangeDoorDemoState
- StrangeDoorState
- attempts_count
- last_method
- last_object_name
- last_transformed_name
- last_photo_message_id
- riddle_attempts

后端：
- 只继续负责现有图片 attachment 上传和 vision 识别。
- 不保存奇怪小门关卡进度。
- 不新增 Demo session 表。
- 不新增成长系统。

小展台：
- 只在孩子明确选择“放进小展台”后，复用现有小展台本地保存链路。
```

原因：

```text
1. 首版验收是儿童试玩吸引力，不是长期进度。
2. App 重启后可重置，符合主控“不新增多关卡持久化”。
3. 本地状态能减少后端改动和等待时间。
4. 图片识别仍依赖后端，避免 Android 直接接触模型 key。
```

---

## 3. 首版是否可以先用 Android 本地状态

可以，且建议首版就这么做。

建议状态：

```kotlin
enum class StrangeDoorDemoState {
    NotStarted,
    ChoosingMethod,
    PhotoPrompt,
    PhotoUploading,
    PhotoResult,
    RiddlePrompt,
    RiddleHint,
    Completed,
}

enum class StrangeDoorState {
    Closed,
    Cracked,
    AlmostOpen,
    Open,
}
```

持久化建议：

```text
1. 首版只放在 ChatViewModel 的 StateFlow / ViewModel 内存态。
2. 横竖屏切换可由 ViewModel 保持。
3. 进程被系统杀掉或 App 重启后允许重置。
4. 暂不写 SharedPreferences，避免把 Demo 误扩展成长期关卡进度。
```

如主控要求“今日事件”必须当天只出现一次，再考虑只保存一个轻量日期标记；不建议 D1 首版加入。

---

## 4. 图片上传是否继续走现有 attachment 链路

继续走现有链路。

当前链路：

```text
CameraPhotoCaptureLauncher / image picker
-> PhotoUploadPreparer
-> ChatViewModel.submitCapturedPhoto
-> AttachmentRepository.createCapturedImage
-> AttachmentApiClient.uploadImage
-> POST /api/v1/attachments/images
-> AttachmentCreateResponse.recognizedContent
```

首版建议：

```text
1. image_purpose 继续使用 share。
2. 不新增 Android 端模型调用。
3. 不新增后端新 endpoint。
4. 不新增 ImagePurpose.STRANGE_DOOR，除非主控明确要求后端区分统计。
5. attachment_id 只作为本轮图片上下文和已有图片链路凭据，不作为 Demo 进度持久化。
```

注意：

```text
后端真实图片上传当前会把图片写入 backend/storage/attachments/images 供 attachment 链路处理。
本 Demo 不额外保存儿童图片、不保存额外敏感图片信息。
```

---

## 5. 图片识别结果如何转成“现实物品 -> 奇怪道具 -> 小门反馈”

输入来源：

```text
AttachmentCreateResponse.recognizedContent.text
AttachmentCreateResponse.recognizedContent.type
AttachmentCreateResponse.recognizedContent.confidence
AttachmentCreateResponse.attachmentId
```

建议新增一个 Android 本地确定性 mapper：

```text
StrangeDoorPhotoTransformMapper
```

输出结构：

```kotlin
data class StrangeDoorPhotoTransform(
    val objectName: String,
    val shapeHint: ShapeHint,
    val canAdvanceDoor: Boolean,
    val canSaveToShowcase: Boolean,
    val transformedName: String,
    val transformedAction: String,
    val doorEffect: String,
)
```

转换规则：

```text
1. recognized_type 是 privacy_sensitive / unsafe_unknown：不生成道具，不推进门，不允许保存。
2. recognized_type 是 homework_problem：不生成道具，不推进门，不允许保存，不能把学习 / 作业转成道具。
3. text 为空：objectName 使用主控文档给出的“这个小东西”。
4. text 中能提取物品名时，只取一个安全、短的现实物品名。
5. 形状只做少量确定性判断：round / partial / unknown / blocked。
6. 道具名、动作、小门反馈只能从主控文档已给出的素材池选择，不自行新增儿童端文案。
```

首版映射池只使用主控文档中已经出现过的表达：

```text
可用道具名：
小月亮盾牌
半圆冲撞器
咕噜圆盘
蓝盖盖转轮
软软开门垫
星星小钥匙
眨眼门铃
圆滚滚按钮
直直敲门棒

可用动作 / 反馈片段：
把它轻轻一转
门上的圆锁咔哒一下松开了
小门被敲得愣了一下
露出了一条小缝
门没有完全打开
但是它打了个喷嚏，露出一条小缝
```

对外展示按主控模板拼接：

```text
我看见了：{现实物品}

在小白狐的世界里
它变成了：{怪道具名}

小白狐用它{动作}
{小门反应}
```

不适合内容只使用主控文档给出的文本：

```text
这张图不太适合变成开门道具
我们换一个小东西试试
```

---

## 6. 拍照变身反馈用本地模板、后端模板还是模型

首版建议：Android 本地确定性模板 + 少量映射。

具体边界：

```text
1. 模型只用于现有后端 vision 识别。
2. “变身道具名 / 小门反馈”不走模型生成。
3. 后端不新增 Prompt、不新增 ModelTaskType、不新增奇怪小门服务。
4. Android 只把 recognizedContent.text 转成主控已批准模板。
5. 如果需要小白狐语音，可复用现有后端小白狐音频生成链路，但音频文本仍来自确定性模板。
```

原因：

```text
1. 避免模型自由发挥新增儿童端文案。
2. 避免输出奖励、通关、装备等禁用表达。
3. 降低 D3 开发和真机验证复杂度。
4. 符合主控“不要先做复杂模型生成”倾向。
```

---

## 7. 怪问题路径如何实现

首版怪问题路径建议完全 Android 本地实现，不进后端 conversation，不改 M1/M2。

固定题目、答案和反馈均使用主控文档：

```text
题目：
什么东西越洗越脏？

答案：
水

答对：
对，是水

小门被你说得愣住了
它低头想了三秒
然后咔哒一下打开了

答错：
这个答案有点勇敢
小门差点相信了

我给你一个提示
它常常在杯子里、河里、盆里

按钮：
再答一次
找东西帮忙
```

实现建议：

```text
1. 孩子点击“动脑试试”后进入 RiddlePrompt。
2. 页面显示怪问题气泡底板和题目。
3. 答案输入优先复用现有 voice-first 语音输入。
4. ChatViewModel 增加 Demo answer capture 分支：处于 RiddlePrompt / RiddleHint 时，ASR transcript 不自动发送 conversation，而是在本地判断。
5. transcript 归一化后包含“水”则答对，否则答错并进入 RiddleHint。
6. 答错后只显示“再答一次 / 找东西帮忙”，不说“错了”“正确答案是”“这个很简单”。
```

需要主控确认：

```text
怪问题首版是否只允许语音回答；
是否保留 DevSettings 下的文字调试入口。
```

---

## 8. 小门状态如何变化

首版只做 4 个门状态：

```text
closed：关着
cracked：开了一条缝
almost_open：快开了
open：打开
```

状态推进规则使用主控文档：

```text
1. 第一次有效输入 -> cracked
2. 第二次有效输入 -> almost_open
3. 答对怪问题或高匹配圆形物品 -> open
4. 不合适内容 -> 不推进，但给温柔反馈
```

实现规则：

```text
1. 不做进度条。
2. 不做关卡数。
3. 不做任务状态。
4. 不做奖励状态。
5. “再玩一次”只重置 Android 本地状态。
```

完成收束文本只使用主控文档：

```text
开啦
你真的帮到我了

门后面有一点暖暖的风
我们先看到这里

按钮：
再玩一次
放进小展台
先聊别的
```

---

## 9. 小门素材未完成前如何做占位，但不得替代正式素材

原则：

```text
素材未确认前不开始正式 UI 编码。
占位只能服务布局计划、资源尺寸校验和自动化测试，不能进入真机试玩验收。
```

建议做法：

```text
1. D1 可以先定义资源清单和 ResourceMapper，不接真实 UI。
2. D2 正式 UI 编码必须等 S1 输出素材 manifest 和 Android 资源路径。
3. 如必须让代码先编译，可使用 Debug / Preview 专用 Canvas 占位。
4. 占位层必须通过开关标明 assets_ready=false。
5. release / 家庭内测包不得把占位当正式素材。
6. QA 报告必须把占位标记为 BLOCKED，而不是 PASS。
```

正式素材路径以主控总计划为准：

```text
android/app/src/main/res/drawable-nodpi/strange_door_closed.webp
android/app/src/main/res/drawable-nodpi/strange_door_cracked.webp
android/app/src/main/res/drawable-nodpi/strange_door_almost_open.webp
android/app/src/main/res/drawable-nodpi/strange_door_open.webp
android/app/src/main/res/drawable-nodpi/strange_door_round_lock.webp
android/app/src/main/res/drawable-nodpi/strange_door_transform_glow.webp
android/app/src/main/res/drawable-nodpi/strange_door_success_glow.webp
android/app/src/main/res/drawable-nodpi/strange_door_riddle_panel.webp
android/app/src/main/res/drawable-nodpi/strange_door_tool_card_panel.webp
android/app/src/main/res/drawable-nodpi/strange_door_ground_shadow.webp
```

---

## 10. 小展台如何承接拍照产生的小发现

小展台只做结果承接，不做主玩法。

当前已有链路：

```text
ChatViewModel.requestSavePhotoToXiaozhantai
ChatViewModel.confirmXiaozhantaiSave
SaveXiaozhantaiItemUseCase
LocalXiaozhantaiRepository
XiaozhantaiListScreen / XiaozhantaiDetailScreen
```

首版建议：

```text
1. 只有拍照变身产生了可保存结果，才显示“放进小展台”。
2. 图片上传成功不等于放进小展台。
3. 拍照变身成功不等于放进小展台。
4. 只有孩子确认并起名后才创建 showcase item。
5. 保存内容仍是现实物品图 + 道具名 / 孩子起名 + 小白狐当时一句话。
6. 不新增小展台详情玩法。
7. 不新增小展台历史分类、图鉴、背包或成就。
```

保存流程文案使用主控文档：

```text
放进小展台
要不要把这个小发现放进小展台？
给它起个名字吧
{name}，放好啦
以后可以在小展台里看到它
```

需要注意：

```text
现有 SaveXiaozhantaiItemUseCase 会记录既有 showcase_item_saved 类型的本地 GrowthEvent。
本计划不新增 GrowthEvent 类型，不新增后端成长系统。
是否在奇怪小门路径中保留这个既有本地事件，需主控确认。
```

---

## 11. 如何避免任务、奖励、积分、通关等表达

执行规则：

```text
1. 所有儿童端可见文本只复制主控文档。
2. Android 常量中增加 forbidden words 单元测试。
3. 拍照变身 mapper 只能从批准词池选择文案片段。
4. 怪问题路径固定题目和固定反馈，不调用模型生成。
5. 小门状态只叫状态，不叫关卡进度。
6. 小展台只叫承接，不叫奖励、收藏册、背包。
```

禁止词扫描至少覆盖：

```text
任务
今日任务
通关奖励
获得道具
装备
战斗力
稀有
史诗
S级
抽卡
宝箱
排行榜
积分
连续打卡
解锁奖励
```

安全边界：

```text
1. 不把作业 / 学习内容变成道具。
2. 不把人脸、学校、地址、证件、隐私文字、医疗 / 暴力 / 惊吓内容做成道具。
3. 不保存额外敏感图片信息。
4. 不引入第二关、第三关、地图、排行榜、签到。
```

---

## 12. 后续会修改哪些文件

D0 本轮实际只修改：

```text
docs/session_process/handoffs/20260604_D0_strange_door_demo_plan.md
```

主控确认后，D1-D5 预计会修改或新增：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoState.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorPhotoTransformMapper.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDemoPanel.kt
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorDoorAssets.kt
android/app/src/main/res/drawable-nodpi/strange_door_*.webp
android/app/src/test/java/com/childai/companion/ui/chat/StrangeDoorDemoStateTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/StrangeDoorPhotoTransformMapperTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/StrangeDoorRiddleTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/AgentReplyCarouselTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelImageAttachmentTest.kt
```

可能按实现情况少量修改：

```text
android/app/src/main/java/com/childai/companion/data/showcase/XiaozhantaiModels.kt
android/app/src/main/java/com/childai/companion/data/showcase/SaveXiaozhantaiItemUseCase.kt
android/README.md
```

后端默认不改。只有主控明确要求后端识别 strange door 语义或新增 image purpose 时，才可能进入：

```text
backend/app/domain/attachment.py
backend/app/services/attachment_service.py
backend/app/tests/test_attachment_api.py
```

不建议首版这么做。

---

## 13. 后续不会修改哪些文件

首版 Demo 不修改：

```text
backend/app/services/child_agent_runtime.py
backend/app/services/prompt_manager.py
backend/app/services/model_registry.py
backend/app/services/safety_engine.py
backend/app/services/scene_orchestrator.py
backend/app/services/intent_classifier.py
backend/app/services/memory*
backend/app/repositories/memory*
backend/app/repositories/conversation_persistence_repository.py
android/app/src/main/java/com/childai/companion/ui/parent/
android/app/src/main/java/com/childai/companion/data/parent/
android/app/src/main/java/com/childai/companion/ui/auth/
android/app/src/main/java/com/childai/companion/voice/
docs/PRODUCT_DECISIONS_V0_1.md
```

不做：

```text
1. 家长端改造。
2. 后端成长系统扩展。
3. 新 prompt 体系。
4. 新模型任务。
5. 新多关卡持久化。
6. 新奖励、积分、等级、地图、排行榜、签到。
7. M1/M2 逻辑修改。
```

---

## 14. 测试策略

D0 本轮测试：

```bash
bash scripts/doctor_local_env.sh
git diff --check
```

D1-D5 实现后的自动化测试建议：

```bash
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh lintDebug
```

若后端不改，后端测试只做回归抽查：

```bash
bash scripts/test_backend.sh
```

Android 单测覆盖：

```text
1. StrangeDoorDemoState 初始、选择、拍照、答题、完成、重置。
2. DoorState 推进规则：cracked / almost_open / open / blocked 不推进。
3. 图片 recognizedContent -> objectName / shapeHint / transformedName / doorEffect。
4. privacy_sensitive / unsafe_unknown / homework_problem 不生成道具、不允许保存。
5. 怪问题答案“水”答对，非水答错进入提示。
6. 怪问题 ASR transcript 在 Demo 状态下不发送 conversation。
7. 拍照路径继续调用 AttachmentRepository.createCapturedImage，image_purpose 为 share。
8. 小展台保存只在孩子确认后发生。
9. 禁止词不出现在 StrangeDoorDemo 的儿童端常量池。
10. 素材缺失时不能把占位标为验收通过。
```

真机试玩验收：

```text
设备：
Redmi K60
Honor Pad 5

重点：
1. 第一眼是否有事件感。
2. 小门是否明显但不吓人。
3. 孩子是否知道能拍东西帮忙。
4. 拍照后反馈是否有趣。
5. 拍错是否被接住。
6. 小门状态是否真的变化。
7. 怪问题是否像机关而不是考试。
8. 是否愿意再拍一个。
9. 小展台承接是否清楚。
```

唯一核心验收题：

```text
孩子玩完第一轮后，会不会主动说：我再找一个给它看看。
```

---

## 15. 风险点

```text
1. 素材未完成时，如果先编码正式 UI，容易用低质量占位替代正式体验。
2. 当前 ChildChatScreen 的 opening greeting 会自动请求，可能和“今日事件首屏优先级”冲突。
3. 当前 InputBar 永远存在，可能让首屏看起来仍像聊天页，而不是小门事件。
4. 怪问题如果复用现有 ASR 自动发送链路，必须拦截 transcript，避免误发后端 conversation。
5. 图片识别摘要不是结构化物品名，Android 本地提取可能不稳定。
6. 如果映射池太小，反馈会重复；如果映射池太大，又会滑向开发方自行写文案。
7. 现有小展台保存会关联本地 GrowthEvent，需要确认是否保留。
8. 后端真实 vision provider 失败时，拍照路径必须诚实失败，不能用本地模板假装看到了。
9. 如果把“不圆”处理成失败，会伤害试玩吸引力；如果任何内容都推进，又会突破安全边界。
10. 如果真机没有连接，D0 不受影响；D2-D5 完成后必须接 Redmi K60 / Honor Pad 5 复测。
```

---

## 16. 需要主控确认的问题

```text
1. 进度板仍写“小屋小客人 D1”，是否由主控另行更新为“奇怪小门 Demo”阶段？
2. Demo 激活时，普通 opening greeting 是延后请求，还是请求但不渲染为首屏主气泡？
3. 首屏 Demo 状态下，是否允许暂时隐藏或弱化普通 InputBar，只保留“找东西帮忙 / 动脑试试”？
4. 怪问题首版是否只使用语音回答？是否保留 DevSettings 下的文字调试入口？
5. 拍照变身反馈是否需要小白狐音频？如果需要，是否复用现有后端小白狐 TTS 音频生成链路？
6. 图片上传首版继续使用 image_purpose=share 是否确认？是否不新增 strange_door image purpose？
7. 道具名和反馈片段是否只允许使用本文列出的主控文档词池？是否需要主控补充更完整的词池？
8. 小展台保存时，是否保留现有 showcase_item_saved 本地 GrowthEvent，还是奇怪小门路径直接调用 repository 保存、不追加 growth event？
9. 素材 S1 未完成前，D1 是否只做状态 / 合同，不进入正式 UI 编码？
10. D2 首页事件是否以“今日事件”常驻首屏，还是只在首次进入 ChatScreen 时显示一次？
```

---

## 17. 建议拆分顺序

```text
D1：Android 本地状态、门状态 reducer、图片变身 mapper、怪问题 evaluator、禁止词测试。
D2：等待 S1 素材 manifest 后接入首页事件 UI。
D3：拍照变身路径，复用 attachment 链路。
D4：怪问题路径，拦截 ASR transcript 做本地判断。
D5：小展台承接，复用现有 LocalXiaozhantaiRepository。
Q1：Redmi K60 / Honor Pad 5 真机试玩。
```

每一轮都保持：

```text
不新增儿童端文案。
不新增第二关、第三关。
不新增奖励、积分、等级。
不改家长端。
不改 M1/M2。
不新增复杂后端成长系统。
```
