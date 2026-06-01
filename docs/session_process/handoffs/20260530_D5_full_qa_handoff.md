# D5 交接：小白狐关系与轻连续体验版完整验收

状态：CONDITIONAL — companion_object 真链路已返修，待真机复测

更新时间：2026-06-01

---

## Summary

D5 自动化阶段已通过；2026-06-01 追加完成 companion_object 真链路返修。当前仍缺最终真机复测截图/录屏，因此状态为 CONDITIONAL，不可直接判定 PASS。

---

## 2026-06-01 companion_object 链路返修补记

### 复核结论

按主控要求逐项复核后，确认此前至少存在 4 处真实断链：

1. **Android quick action 上报不是真 id**
   - `起个名字` 按钮点击后，Android 实际发送的是文案 `"起个名字"`，不是 `quick_action id=companion_name`。
   - 结果：后端无法把这一轮识别成“小客人起名链路”的开始。

2. **后端没有把 seed 起名后续接到 `CompanionObjectService.create()`**
   - D1 的 `CompanionObjectService.create()` 已存在，但生产代码中没有真实调用点。
   - 结果：孩子说“叫小棉花”后，之前只是普通聊天，不会真实落库 active 小客人。

3. **流式 route payload 会丢 `companion_object`**
   - 文本对话默认走 stream，后端 `route_decision` 事件此前不携带 `companion_object`。
   - Android `applyStreamRoute()` 也没有解析 `companion_object`。
   - 结果：即使后端本轮带了 companion 信息，流式链路里也会被 UI 自己丢掉。

4. **Android 视觉点映射和坐标都有问题**
   - 后端 opening seed 返回 `object_type=star`，而 Android 视觉类型测试只覆盖了 `"小星星"`。
   - `CompanionLightPoint` 之前直接从左上角 `offset`，不少 `window/carpet` 坐标实际上会跑出可见区域。
   - 结果：后端 opening 文案到了，轻视觉点仍可能完全看不见。

### 本轮已完成返修

1. **补齐 quick action 真上报**
   - Android `ConversationInput` 新增 `quick_action_id`。
   - `ChatViewModel.onQuickAction()` 现在会把 `companion_name / companion_skip / companion_continue` 真 id 带回后端。

2. **补齐 seed 起名 -> create 真链路**
   - `ConversationService` 新增 seed naming pending 处理。
   - 点击 `companion_name` 后，后端会为当前 session 建立待起名状态。
   - 下一轮孩子说出名字（如“叫小棉花”）后，会真实调用 `CompanionObjectService.create()`。

3. **create 成功后本轮就回传 active companion**
   - 创建成功后，`session_state.companion_object` 会带 `state=active`、`action=co_create`、`light_location=窗边`。
   - 这样 Android 本轮即可显示小客人轻视觉，而不是等到下次 opening recall 才有机会看到。

4. **stream 链路补回 `companion_object`**
   - 后端 `conversation_stream_service._route_payload()` 已补充 `companion_object`。
   - Android `applyStreamRoute()` 已解析并合并 `companion_object`，避免流式对话把 companion 状态冲掉。

5. **Android 视觉点修正到可见**
   - `star` / `cloud` 英文枚举值已映射到正确视觉类型。
   - `shouldShowVisual()` 已支持 `active + co_create`。
   - 视觉点位置改为带锚点的 placement，不再直接从左上角错误偏移。
   - 星点/光点 alpha、size、blur 略增强，保证 seed/recall 有可见变化。

### 本轮代码级验证

| 检查项 | 结果 |
|---|---|
| opening seed metadata | PASS：`{'id': 'star_seed', 'name': '小星星', 'object_type': 'star', 'light_location': '窗边', 'state': 'seed', 'action': 'name_seed'}` |
| Android DTO 解析 companion_object | PASS |
| ViewModel 写入/合并 sessionState | PASS |
| Stage 收到并渲染 companionObject | PASS（代码和单测） |
| `shouldShowVisual()` 对 seed/name_seed | PASS |
| `co_create` 可见链路 | PASS |
| `companion_name` quick action 真上报 | PASS |
| “叫小棉花” 触发 `create()` | PASS |
| active companion 可读回 | PASS |
| stream route 保留 companion_object | PASS |

### 自动化验证增量

新增通过：

```text
bash scripts/test_backend.sh -k "test_companion_object_runtime or test_conversation_opening_api" -q
45 passed, 800 deselected

bash scripts/android_gradle.sh testDebugUnitTest --tests com.childai.companion.data.ConversationDtosTest --tests com.childai.companion.ui.chat.CompanionObjectVisualTest --tests com.childai.companion.ui.chat.ChatViewModelOpeningTest --tests com.childai.companion.ui.ChatViewModelStreamTest.routeDecisionCarriesCompanionObjectIntoUiState
PASS

bash scripts/android_gradle.sh assembleDebug
PASS
```

说明：

```text
已知失败 audioReadyUsesQueueWhenNotMuted 仍存在，但本轮未修，且与 companion_object 链路无关。
```

### 真机复测仍待完成

当前没有连接 Redmi K60 / Honor Pad 5，因此本轮没有新增真机截图或录屏。

截图/录屏路径：

```text
docs/session_process/handoffs/d5_screenshots/   （本轮未新增文件）
```

---

## 自动化阶段结论

| 检查域 | 结果 |
|---|---|
| 后端全量单测 | PASS（840 passed, 0 failed） |
| 后端 lint | PASS（39 errors 为 D1 前已有） |
| Android 全量单测 | PASS（241 completed, 1 failed — 已知非引入） |
| Android assembleDebug | PASS |
| Android lintDebug | PASS |
| companion_object 专项（59 个） | PASS |
| companion_object_runtime 专项（18 个） | PASS |
| parent_report_companion 专项（19 个） | PASS |
| bedtime_opening（2 个） | PASS |
| 禁止话术扫描 | PASS（无违规） |
| 代码审查（opening/conversation/parent_report） | PASS |
| 日志和数据安全 | PASS |
| Android 端无 API key | PASS |

---

## 真机复测待完成原因

```text
adb devices 无设备连接。
Redmi K60 和 Honor Pad 5 均未连接到开发机。
无法执行真机功能验证、截图和录屏。
```

---

## 真机阶段待验证清单

设备连接后需覆盖：

| 序号 | 检查项 | 设备 | 截图文件 |
|---|---|---|---|
| 1 | 首次打开 seed：窗边小星点 + 起名种子气泡 | Redmi K60 | 01_first_open_seed.png |
| 2 | 小星星窗边轻视觉点特写 | Redmi K60 | 02_seed_light_point.png |
| 3 | 有小客人 recall 气泡 | Redmi K60 | 03_companion_recall.png |
| 4 | recall 对应 light_location 轻视觉点 | Redmi K60 | 04_recall_light_location.png |
| 5 | 点击"先聊别的"后不再拉回（录屏） | Redmi K60 | 05_skip_no_recall.png |
| 6 | 拍图成功只显示"起个名字" | Redmi K60 | 06_image_success_name_action.png |
| 7 | 拍图失败无共创入口 | Redmi K60 | 07_image_failure_no_action.png |
| 8 | 睡前 opening 不召回 | Redmi K60 | 08_bedtime_opening.png |
| 9 | 家长端"轻共创"区块 | Redmi K60 | 09_parent_companion_summary.png |
| 10 | 横屏/平板小客人位置 | Honor Pad 5 | 10_landscape_position.png |
| 11 | 平板竖屏小客人位置 | Honor Pad 5 | 11_tablet_position.png |
| 12 | 语音主链路验证 | Redmi K60 | 录屏 |

---

## 已知问题跟踪

### audioReadyUsesQueueWhenNotMuted

- **首次出现**：commit `27d9936`（远早于 D1）
- **影响小屋小客人路径**：否
- **影响语音播放**：需真机验证
- **当前状态**：不阻塞自动化阶段，真机阶段需验证语音分段播放是否正常

### 同会话召回抑制进程内存（K05）

- **状态**：v0.1 可接受
- **影响**：服务重启后同会话抑制丢失
- **风险**：不影响家庭测试核心路径

### 横屏/平板视觉点位置

- **状态**：待真机确认
- **微调权限**：offset/size/alpha/blur/动画幅度可调

---

## 真机阶段执行步骤（设备连接后）

```text
1. 连接 Redmi K60，确认 adb devices 可见。
2. 启动后端：bash scripts/start_backend_services.sh --agent main --host 0.0.0.0 --port 8000
3. 构建 APK：bash scripts/build_device_debug_apk.sh --base-url http://192.168.0.118:8000/
4. 安装：bash scripts/install_android_debug.sh
5. 执行清单 1-9 和 12（Redmi K60）。
6. 连接 Honor Pad 5，执行清单 10-11。
7. 截图保存到 docs/session_process/handoffs/d5_screenshots/。
8. 如需微调视觉点坐标，仅限 offset/size/alpha/blur/动画幅度。
9. 汇总最终 QA 结论。
```

---

## 边界遵守

```text
1. 不用 mock 冒充真实路径 — 已遵守
2. 不改产品设计 — 已遵守
3. 不新增文案 — 已遵守
4. 不扩大功能 — 已遵守
5. 发现阻塞 bug 先记录，经主控确认后才修 — 已遵守
```

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是
