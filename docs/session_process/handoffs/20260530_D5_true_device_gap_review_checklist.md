# D5 真机缺口复核清单：小屋小客人链路

项目：`ai-child`

用途：根据真机初测反馈，复核“小屋小客人”从 opening、Android 渲染、起名创建、再次召回到家长端摘要的实际落地情况。本文用于开发端快速 review 程序，不新增产品设计。

更新时间：2026-05-30

---

## 0. 真机反馈

监理方真机初测反馈：

```text
1. 刚打开时，小白狐确实使用了“小星星起名”的开场白。
2. 但界面上没有出现小星点、小光影或其他小屋轻变化。
3. 后续“起名后生成小客人 / 再次打开轻召回”等链路没有明显出现。
```

主控判断：

```text
这说明后端 opening 文案可能已触发，但 Android companion_object 渲染链路、起名创建链路、二次召回链路至少有一处没有真实接通。
```

当前状态：

```text
D5 真机阶段不能判 PASS。
必须先完成本清单复核和必要返修。
```

---

## 1. 首次打开 seed 的预期实现

### 1.1 后端预期

首次打开且无小客人历史、非睡前、非学习、非安全/隐私场景时，后端 opening 应返回：

```text
reply.text:
窗边这颗小星星还没有名字
要不要给它起一个？

quick_actions:
- id: companion_name, label: 起个名字
- id: companion_skip, label: 先看看

session_state.companion_object:
{
  id: "star_seed",
  name: "小星星",
  object_type: "star",
  light_location: "窗边",
  state: "seed",
  action: "name_seed"
}
```

注意：

```text
1. 此时不得调用 CompanionObjectService.create()。
2. 只有孩子真正起名后，才创建 active 小客人。
3. 如果后端只返回了文案，没有返回 session_state.companion_object，Android 不会显示视觉点。
```

### 1.2 Android 预期

Android 应完成：

```text
1. 解析 opening response 中的 session_state.companion_object。
2. 写入 ChatUiState / 当前会话 UI state。
3. 传给 XiaobaohuCompanionStage。
4. XiaobaohuCompanionStage 根据 state="seed" 且 action="name_seed" 渲染窗边小星点。
```

视觉预期：

```text
1. 窗边出现很淡的小星点。
2. 低饱和、柔和、半透明。
3. 小白狐仍是第一主视觉。
4. 不出现奖励闪光、领取、解锁、宠物感。
```

### 1.3 开发端重点排查

请优先确认：

```text
1. opening endpoint 的真实 JSON 是否包含 session_state.companion_object。
2. Android 的 opening response DTO 是否解析了 companion_object。
3. opening 返回后，ViewModel 是否把 session_state 写入 uiState.sessionState。
4. ChildChatScreen 是否把 uiState.sessionState?.companionObject 传入 AgentPanel。
5. AgentPanel 是否继续传入 XiaobaohuCompanionStage。
6. CompanionLightPoint 是否因 state/action 判断返回了 false。
7. 小星点是否被绘制在小屋外、被遮挡、alpha 太低或位置偏离。
```

---

## 2. 起名后创建小客人的预期实现

### 2.1 用户路径预期

从 seed 状态开始：

```text
1. 孩子点击“起个名字”。
2. 孩子输入或语音说：叫小棉花 / 名字是小棉花。
3. 后端识别为 seed 起名完成。
4. 调用 CompanionObjectService.create()。
5. 创建 active 小客人。
```

创建字段预期：

```text
name: 小棉花
object_type: star
source_type: first_open
safe_summary: 孩子给窗边的小星星起名小棉花
light_location: 窗边
status: active
```

小白狐回应应使用 master-copy 方向：

```text
小棉花，软软的名字
那它今天就在窗边待一会儿
```

如果暂未实现精确回应，也必须满足：

```text
1. 不出现“保存成功”。
2. 不出现“任务完成”。
3. 不出现“明天一定要来看”。
4. 不出现“它会等你”。
```

### 2.2 当前重点怀疑点

请开发端重点排查：

```text
1. 点击“起个名字”后，Android 是否把 quick_action id=companion_name 发回后端。
2. 后端是否知道当前处于 star_seed / name_seed 上下文。
3. 用户说“叫小棉花”时，ConversationService 是否调用 create()，而不是仅普通回复。
4. create() 后是否返回新的 session_state.companion_object 或至少后续可查询到 active 小客人。
5. 数据库 companion_objects 是否真的插入 active 记录。
6. 如果 child_id 不存在，SQL 仓储是否抛错导致 create 失败。
7. 错误是否被吞掉，导致 UI 看起来无变化。
```

### 2.3 必须补测试

如果当前没有覆盖，开发端应补：

```text
1. star_seed + 点击 companion_name + “叫小棉花” -> create active companion。
2. child_id 存在时 create 成功。
3. child_id 不存在时返回可诊断错误，不静默失败。
4. 创建成功后 get_active_by_child(child_id) 可查到小棉花。
```

---

## 3. 第二次打开轻召回的预期实现

### 3.1 后端预期

当 child_id 下存在 active 小客人，并且非睡前、非安全、非学习、非隐私场景时，opening 应返回：

```text
reply.text:
小棉花今天在窗边呢
要不要给它加一个朋友？

quick_actions:
- id: companion_continue, label: 加一个朋友
- id: companion_skip, label: 先聊别的

session_state.companion_object:
{
  id: 小客人真实 id,
  name: 小棉花,
  object_type: star,
  light_location: 窗边,
  state: active,
  action: recall
}
```

同时调用：

```text
CompanionObjectService.mark_recalled(companion_id, session_id=当前会话)
```

### 3.2 Android 预期

```text
1. 渲染对应 light_location 的轻视觉点。
2. 显示后端 quick_actions。
3. 不自行新增或修改按钮文案。
```

### 3.3 重点排查

```text
1. active 小客人是否已创建。
2. can_recall(child_id, session_id, is_bedtime=false) 是否返回对象。
3. session_id 是否每次打开合理变化。
4. mark_recalled 是否过早调用导致首次可见前就被抑制。
5. opening response 是否被缓存，导致看不到新状态。
6. Android 是否复用旧 sessionState，导致 companion_object 丢失。
```

---

## 4. 点击“先聊别的”后的预期实现

### 4.1 预期

孩子点击“先聊别的”或说“不想 / 不要 / 不知道 / 换个话题”后：

```text
1. 后端调用 mark_skipped(companion_id, session_id=当前会话)。
2. 本会话内不再主动召回。
3. 小白狐接新话题。
4. 不说它会等你、会难过。
```

### 4.2 重点排查

```text
1. Android 点击 companion_skip 是否把 action id 发给后端。
2. ConversationService 是否能识别 quick action，而不只是识别文本。
3. 如果按钮只在 UI 层处理，没有请求后端，则 mark_skipped 不会发生。
```

---

## 5. 图片成功后的共创入口预期实现

### 5.1 预期

图片成功且安全时：

```text
1. 小白狐只给一个共创入口。
2. quick action 只出现：起个名字。
3. 不出现“编个小故事”。
4. 不出现“上传成功 / 识别成功 / 图片分析”。
```

### 5.2 重点排查

```text
1. image_context 是否真实传到 ConversationService。
2. recognized_type 是否落在安全类型集合内。
3. quick_actions 是否被后续默认 actions 覆盖。
4. 图片失败时 image_context 是否为 None 或失败态，不能输出 companion_name。
```

---

## 6. 家长端轻共创摘要预期实现

### 6.1 预期

当当天有 active 小客人并且 source_type 符合规则时，家长日报可展示：

```text
轻共创
今天孩子和小白狐有一次轻松共创。
```

或：

```text
轻共创
孩子主动分享了一张作品。
```

不得展示：

```text
1. 小客人名字。
2. 小客人位置。
3. 召回次数。
4. 跳过次数。
5. 完整聊天。
6. 图片细节。
7. 孩子拒绝继续。
```

### 6.2 重点排查

```text
1. active 小客人没有创建时，家长端当然不会有轻共创。
2. parent_report_service 是否能按 target_date 查到当天 active 小客人。
3. updated_at / created_at 时区是否导致日期不匹配。
```

---

## 7. 真机阻塞判断

以下任一项不成立，本轮不能进入家庭测试：

```text
1. opening 文案出现，但 Android 没有 seed 小星点。
2. 点击“起个名字”后，无法创建 active 小客人。
3. 第二次打开无法轻召回。
4. 点击“先聊别的”后仍反复拉回，或根本没有 mark_skipped。
5. 图片成功后没有“起个名字”，或图片失败后仍出现共创入口。
6. 家长端无法在真实轻共创后显示“轻共创”区块。
```

---

## 8. 建议开发端立即执行的最小复核顺序

请按顺序排查，不要先做大改：

```text
1. 打印 / 保存首次 opening 的真实后端 JSON。
2. 确认 JSON 是否包含 session_state.companion_object seed。
3. 确认 Android DTO 是否解析到 companionObject。
4. 确认 ViewModel 是否把 opening response 的 session_state 写入 uiState。
5. 确认 XiaobaohuCompanionStage 是否收到 companionObject。
6. 确认 CompanionLightPoint.shouldShowVisual() 返回 true。
7. 确认 Canvas 实际绘制在可见区域。
8. 点击“起个名字”，确认 action 是否发给后端。
9. 输入“叫小棉花”，确认 create() 是否调用并写入 companion_objects。
10. 重新打开，确认 can_recall() 是否返回小客人。
11. 确认 Android 能渲染 recall 视觉点。
12. 确认家长端轻共创区块。
```

---

## 9. 开发端返修边界

允许返修：

```text
1. DTO 解析。
2. ViewModel 状态传递。
3. opening response session_state 合并。
4. quick action id 上报。
5. seed 起名后 create() 调用。
6. 视觉点坐标 / alpha / size / blur 小范围调整。
7. 测试补齐。
```

禁止返修：

```text
1. 新增儿童端文案。
2. 新增小客人玩法。
3. 新增列表、收藏、宠物、奖励。
4. 改家长端边界。
5. 重写全局 prompt。
6. 用 mock 冒充真机通过。
```

---

## 10. 返修交接要求

开发端完成复核 / 返修后，请更新：

```text
docs/session_process/handoffs/20260530_D5_full_qa_handoff.md
```

回传给主控时只给：

```text
1. 提交号。
2. 文档路径。
3. 5 行摘要。
4. 真机截图/录屏路径。
5. 当前状态：PASS / CONDITIONAL / BLOCKED。
```
