# D3 交接：Android 儿童端小屋小客人呈现

状态：done，待主控审核

更新时间：2026-05-30

---

## Summary

在 Android 儿童端小白狐小屋页面中渲染"小屋小客人"的轻连续体验。根据后端 `companion_object` 字段，在小屋窗边/地毯边/小白狐旁边/窗外显示轻视觉点（小星点/小光影/小云影）。

---

## Files

### 修改

| 文件 | 说明 |
|---|---|
| `android/app/src/main/java/com/childai/companion/data/conversation/ConversationDtos.kt` | 新增 `CompanionObjectMeta` 数据类，在 `ConversationSessionState` 中添加 `companionObject` 字段和解析 |
| `android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt` | 新增 `CompanionLightPoint` Composable，根据 `light_location` 和 `object_type` 渲染轻视觉点 |
| `android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt` | 在 `AgentPanel` 调用处传递 `companionObject` 参数 |

### 新建

| 文件 | 说明 |
|---|---|
| `android/app/src/test/java/com/childai/companion/ui/chat/CompanionObjectVisualTest.kt` | 小客人视觉状态映射测试（13 个用例） |

### 测试修改

| 文件 | 说明 |
|---|---|
| `android/app/src/test/java/com/childai/companion/data/ConversationDtosTest.kt` | 新增 5 个 companion_object 解析测试 |

---

## Child-visible change

1. **首次打开（seed 状态）**：窗边出现一颗很淡的小星点，轻微呼吸式闪烁（周期 3 秒），低饱和暖黄色。
2. **有小客人召回（active+recall 状态）**：根据 `light_location` 在对应位置显示小光点/小光影/小云影，轻微浮动式动画（周期 4 秒）。
3. **无小客人或 action=none**：保持原小屋状态，不显示额外视觉点。
4. **暂放状态（paused）**：不显示视觉点，避免宠物化和亏欠感。

视觉特点：
- 小白狐仍是第一主视觉
- 小客人只是小星点/小光影/小云影，不抢小白狐位置
- 低饱和、柔和、半透明，不使用奖励闪光或游戏化光效
- 尺寸 16-24dp，alpha 0.5-0.8，使用 blur 柔化边缘

---

## Tests

```
bash scripts/android_gradle.sh test
```

结果：241 tests completed, 1 failed

失败的测试：`ChatViewModelStreamTest > audioReadyUsesQueueWhenNotMuted`（非 D3 引入，已有失败）

新增测试：
- `ConversationDtosTest`：5 个 companion_object 解析测试（全部通过）
- `CompanionObjectVisualTest`：13 个视觉状态映射测试（全部通过）

---

## Safety

- 不涉及儿童数据保存
- 不涉及安全策略变更
- 不涉及新增记忆、召回或家长端展示风险
- 暂放状态不显示视觉点，避免宠物化和亏欠感

---

## Docs

- 已更新 `docs/session_process/handoffs/20260530_D3_android_companion_object_handoff.md`

---

## Product boundary

- 严格遵守主控文档，未自行设计产品方向
- 未新增任何儿童端文案或小白狐话术
- 未扩展为小客人列表、收藏、宠物、任务或奖励系统
- 按钮文案完全来自后端 `quick_actions`，未自行修改
- 暂放状态不显示视觉点，避免宠物化

---

## Known issues

1. 横屏/平板的视觉点位置需要真机截图确认，当前使用相对锚点可能需要微调。
2. 低端设备上 blur 效果可能有性能问题，可降级为静态轻光点。
3. `ChatViewModelStreamTest > audioReadyUsesQueueWhenNotMuted` 已有失败，非 D3 引入。

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是（`bash scripts/android_gradle.sh test`、`bash scripts/android_gradle.sh assembleDebug`）

---

## 主控确认事项

1. 视觉点样式：使用 Compose Canvas 绘制，seed=窗边小星点，recall=对应位置小光点/小光影/小云影。
2. 位置精度：使用相对锚点，需要真机截图确认。
3. 动画节奏：呼吸式 3 秒、浮动式 4 秒，幅度很小。
4. action="none"：首版不显示视觉点。
5. state="paused"：不显示视觉点。

---

## 截图/录屏说明

D3 实现完成，但需要真机截图确认视觉点位置和效果。建议主控在真机验证时关注：

```text
1. 首次打开：窗边小星点是否合适
2. 有小客人召回：light_location 对应位置的视觉点是否合适
3. 横屏/平板：视觉点位置是否合适
4. 暂放状态：是否确实不显示视觉点
```

截图路径待真机验证后补充。
