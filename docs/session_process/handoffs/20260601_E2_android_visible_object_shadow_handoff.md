# E2 交接：Android 小物件影子渲染增强

状态：DONE

更新时间：2026-06-01

---

## Summary

E2 已完成。将 Android 端 `CompanionVisualType` 从 4 种扩展为 6 种，每种 `visual_kind` 有独立的 Canvas 形状渲染。从"圆形光晕"升级为"孩子能看见的小物件影子"：星星、云朵、纸船、小门、恐龙轮廓、积木块。

---

## Files

### 修改

```text
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt
  - CompanionVisualType 枚举：4 种 → 6 种（Star / Cloud / PaperBoat / TinyDoor / DinoShadow / BlockLight）
  - toCompanionVisualType()：6 种 visual_kind 各有独立映射，legacy fallback 更新
  - 新增 defaultLocationForVisualKind()：light_location 为空时的兜底位置
  - CompanionVisualConfig：重写为双层配置（光晕层 + 形状层），alpha 调低
  - CompanionLightPoint：新增 Canvas 形状层 + 入场动画（fade in 1.2s + scale）
  - 新增 6 个 drawXxxShape() 函数：Canvas path 绘制星星/云朵/纸船/小门/恐龙/积木

android/app/src/test/java/com/childai/companion/ui/chat/CompanionObjectVisualTest.kt
  - 更新 toCompanionVisualType() 测试：覆盖 6 种 visual_kind + legacy fallback
```

### 不修改

```text
backend/ — 全部不动
android/app/src/main/java/com/childai/companion/data/conversation/ConversationDtos.kt — 不动
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt — 不动
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt — 不动
android/app/src/main/java/com/childai/companion/ui/chat/CompanionRoomViewport.kt — 不动
```

---

## visual_kind 渲染规格

| visual_kind | 形状 | 光晕 alpha | 形状填充 alpha | 光晕大小 | 形状大小 | 动画 |
|---|---|---|---|---|---|---|
| star | 五角星轮廓 | 0.45 | 0.50 | 42dp | 30dp | Breathing 3500ms |
| cloud | 3 椭圆云朵 | 0.40 | 0.45 | 46dp | 40×26dp | Floating 5000ms |
| paper_boat | 梯形船身+三角帆 | 0.38 | 0.42 | 38dp | 34×28dp | Floating 5000ms |
| tiny_door | 圆角矩形+半圆顶+把手 | 0.40 | 0.42 | 34dp | 26×36dp | Breathing 4000ms |
| dino_shadow | 圆身+圆头+曲线尾巴（无眼睛） | 0.38 | 0.40 | 40dp | 36×30dp | Floating 5000ms |
| block_light | 圆角正方形 | 0.40 | 0.42 | 36dp | 28dp | Breathing 3800ms |

叠加后整体视觉感约 0.65-0.8，满足设计要求。

---

## 位置兜底规则

后端 `light_location` 决定位置。当为空或未知时：

| visual_kind | 默认位置 |
|---|---|
| star / cloud / tiny_door | 窗边 |
| paper_boat / dino_shadow / block_light | 地毯边 |

---

## 入场动画

所有类型统一：fade in 1.2 秒 + scale 从 0.8 到 1.0，只播放一次。之后进入持续动效。

---

## Tests

```text
CompanionObjectVisualTest：PASS（10 个测试：6 种 visual_kind 映射 + 4 种 legacy fallback）
ConversationDtosTest：PASS
assembleDebug：BUILD SUCCESSFUL
已知失败 audioReadyUsesQueueWhenNotMuted：仍存在，与 E2 无关
```

---

## Safety

```text
1. 不新增儿童端文案 — 已遵守
2. 不改后端 — 已遵守
3. 不改 prompt — 已遵守
4. 不改家长端 — 已遵守
5. 不新增图片素材 — 已遵守（全部纯 Canvas path）
6. 不做宠物表情 — 已遵守（dino_shadow 无眼睛、无表情）
7. 不做任务/奖励/收藏/图鉴 — 已遵守
```

---

## Docs

```text
docs/session_process/handoffs/20260601_E2_android_visible_object_shadow_plan.md（计划）
docs/session_process/handoffs/20260601_E2_android_visible_object_shadow_handoff.md（本文）
```

---

## Product boundary

```text
1. 6 种 visual_kind 各有独立形状，可区分
2. 形状全部纯 Canvas path 绘制，无外部资源
3. dino_shadow 已去宠物化：无眼睛、无表情、无背脊装饰
4. 入场动画 1.2s fade in + scale，不抢小白狐主视觉
5. 描边 1dp、低饱和、alpha ≤ 0.32，边缘柔和
6. 横屏/平板复用现有 5 种 viewport 适配机制
```

---

## Known issues

```text
1. 真机截图/录屏未完成（需连接 Redmi K60 / Honor Pad 5）。
2. 纯 Canvas path 的形状辨识度需真机验证；如不够，E3 阶段可申请主控批准引入极简 SVG。
3. audioReadyUsesQueueWhenNotMuted 已知失败仍存在，与 E2 无关。
```

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是
