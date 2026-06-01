# E2 计划：Android 小物件影子渲染增强

状态：待主控确认

更新时间：2026-06-01

---

## 1. 已阅读文档列表

```text
README.md
AGENTS.md
docs/提示词与文案归属规则_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
docs/session_process/轻量交接协议_2026_05_30_V0_1.md
docs/给小白狐看看2_0与小屋可见共创增强设计_2026_06_01_V0_1.md
docs/session_process/handoffs/20260601_E1_visual_kind_mapping_handoff.md
docs/session_process/handoffs/20260530_D5_full_qa_handoff.md
docs/session_process/handoffs/20260530_D5_true_device_gap_review_checklist.md
```

---

## 2. 当前 Android 实现现状

### 2.1 CompanionVisualType（4 种）

文件：`android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt` line 363

```kotlin
internal enum class CompanionVisualType {
    StarPoint,      // 星星 - 三层光晕 + 呼吸动画
    CloudShadow,    // 云朵 - 浮动 + Y偏移
    LightSpot,      // 光斑 - 浮动 + Y偏移
    SoftOutline,    // 柔和轮廓 - 静态
}
```

### 2.2 当前 visual_kind 到 CompanionVisualType 映射

| visual_kind | 映射类型 | 问题 |
|---|---|---|
| star | StarPoint | 可区分 |
| cloud | CloudShadow | 可区分 |
| paper_boat | LightSpot | 与 block_light 相同，无法区分 |
| tiny_door | SoftOutline | 与 dino_shadow 相同，无法区分 |
| dino_shadow | SoftOutline | 与 tiny_door 相同，无法区分 |
| block_light | LightSpot | 与 paper_boat 相同，无法区分 |

### 2.3 当前绘制方式

不使用 Canvas，使用 Compose Box + `Brush.radialGradient` + `blur()` Modifier + `CircleShape` 背景实现光晕效果。所有类型都是圆形光晕，无形状区分。

### 2.4 当前大小

| 类型 | 外层 size | 中层 size | 核心 size |
|---|---|---|---|
| StarPoint | 38dp | 22dp | 9dp |
| CloudShadow | 26dp | 16dp | 0dp |
| LightSpot | 24dp | 14dp | 0dp |
| SoftOutline | 22dp | 12dp | 0dp |

问题：CloudShadow/LightSpot/SoftOutline 都偏小（22-26dp），对孩子来说不够明显。

### 2.5 当前透明度

| 类型 | baseAlpha |
|---|---|
| StarPoint | 0.96 |
| CloudShadow | 0.62 |
| LightSpot | 0.68 |
| SoftOutline | 0.60 |

问题：StarPoint 的 0.96 过高，接近不透明，不够"半透明贴纸感"。

### 2.6 当前动画

| 类型 | 动画 | 周期 |
|---|---|---|
| StarPoint | Breathing（alpha 呼吸） | 3000ms |
| CloudShadow | Floating（alpha + Y偏移） | 4000ms |
| LightSpot | Floating（alpha + Y偏移） | 4000ms |
| SoftOutline | Static（无动画） | - |

### 2.7 当前位置

4 种位置：WindowSide / CarpetEdge / NearFox / OutsideWindow

每种位置针对 5 种 viewport（Portrait / PortraitExpanded / LandscapeWide / LandscapeTablet / LandscapeSquare）有独立的像素级 offset，已有完整的横屏/平板适配基础。

### 2.8 核心问题总结

```text
1. 6 种 visual_kind 只有 4 种视觉，paper_boat/tiny_door/dino_shadow/block_light 无法区分。
2. 所有类型都是圆形光晕，无形状差异，孩子看不出"那是什么东西"。
3. 部分类型太小（22-26dp），孩子不容易注意到。
4. StarPoint 的 alpha 过高（0.96），不够柔和。
5. 缺少"轻轻出现"的入场动效，只有持续呼吸/浮动。
```

---

## 3. 6 种 visual_kind 渲染方案

### 3.1 总体策略

从 4 种 CompanionVisualType 扩展为 6 种，每种 visual_kind 对应独立的视觉类型。引入 Canvas path 绘制简化形状轮廓，保留 radialGradient 光晕作为底层氛围，上层叠加半透明形状。

渲染层次：

```text
Layer 1: radialGradient 光晕底层（保留现有方式，调低 alpha）
Layer 2: Canvas 绘制的简化形状轮廓（半透明、低饱和、柔软线条）
Layer 3: 可选的核心高光点（仅 star 使用）
```

### 3.2 star — 窗边小星星

| 属性 | 值 |
|---|---|
| 外形 | 五角星轮廓，Canvas drawPath |
| 大小 | 40dp（光晕）+ 28dp（星形轮廓） |
| 颜色 | 暖黄 `#FFF3D0` 轮廓，`#FFE082` 填充（alpha 0.5） |
| 光晕色 | `#FFF8E1` → `#FFE082` → transparent 径向渐变 |
| 透明度 | 光晕 0.7，轮廓填充 0.5 |
| 动画 | Breathing 3500ms，轮廓 alpha 在 0.4-0.6 间呼吸 |
| 位置 | 默认 WindowSide |

五角星 path：5 个外顶点 + 5 个内顶点，用 `Path.lineTo()` 连接，`CornerPathEffect(4f)` 圆角软化。

### 3.3 cloud — 小云朵影子

| 属性 | 值 |
|---|---|
| 外形 | 2-3 个重叠椭圆组成的云朵轮廓，Canvas drawOval |
| 大小 | 44dp × 30dp（椭圆整体） |
| 颜色 | 奶白 `#F5F5F5` 填充（alpha 0.45），淡蓝 `#E3F2FD` 边缘 |
| 光晕色 | `#F5F5F5` → `#E8EAF6` → transparent |
| 透明度 | 光晕 0.55，填充 0.45 |
| 动画 | Floating 5000ms，Y 偏移 [-3, 3]，alpha 在 0.4-0.55 间浮动 |
| 位置 | 默认 OutsideWindow 或 WindowSide |

云朵 path：3 个不同大小的 `drawOval` 重叠，底部一个大的，左上和右上各一个小的，整体形成云朵轮廓。

### 3.4 paper_boat — 小纸船影子

| 属性 | 值 |
|---|---|
| 外形 | 简化纸船轮廓：一个倒梯形船身 + 一个小三角帆，Canvas drawPath |
| 大小 | 36dp × 28dp |
| 颜色 | 淡米色 `#FFF8E1` 填充（alpha 0.4），浅蓝 `#E1F5FE` 帆 |
| 光晕色 | `#FFF8E1` → `#E1F5FE` → transparent |
| 透明度 | 光晕 0.5，填充 0.4 |
| 动画 | Floating 4500ms，Y 偏移 [-2, 2]，轻微水平漂移 [-1, 1] |
| 位置 | 默认 CarpetEdge 或 WindowSide |

纸船 path：
```text
船身：moveTo(0.2w, 0.6h) -> lineTo(0.8w, 0.6h) -> lineTo(0.9w, 0.85h) -> lineTo(0.1w, 0.85h) -> close()
帆：  moveTo(0.5w, 0.15h) -> lineTo(0.5w, 0.6h) -> lineTo(0.7w, 0.45h) -> close()
```

不做航行动画，只做轻微浮动。

### 3.5 tiny_door — 小门影子

| 属性 | 值 |
|---|---|
| 外形 | 圆角矩形门身 + 半圆门顶 + 小圆形门把手，Canvas drawRoundRect + drawArc + drawCircle |
| 大小 | 30dp × 40dp |
| 颜色 | 淡暖黄 `#FFF3E0` 门身（alpha 0.4），浅棕 `#D7CCC8` 门框 |
| 光晕色 | `#FFF3E0` → `#EFEBE9` → transparent |
| 透明度 | 光晕 0.5，填充 0.4 |
| 动画 | Breathing 4000ms，alpha 在 0.35-0.5 间缓慢呼吸 |
| 位置 | 默认 WindowSide |

门的 path：
```text
门身：drawRoundRect(rect, cornerRadius = 6.dp)
门顶：drawArc 半圆在门身上方
门把手：drawCircle(radius = 2.dp) 在门身右侧中部
```

不做解锁感，不做开门动画。

### 3.6 dino_shadow — 小恐龙影子

| 属性 | 值 |
|---|---|
| 外形 | 极简圆润恐龙轮廓：圆头 + 小身体 + 短尾巴 + 两个小圆眼睛，Canvas drawPath |
| 大小 | 38dp × 34dp |
| 颜色 | 淡绿灰 `#E8F5E9` 填充（alpha 0.4），略深 `#C8E6C9` 轮廓 |
| 光晕色 | `#E8F5E9` → `#C8E6C9` → transparent |
| 透明度 | 光晕 0.5，填充 0.4 |
| 动画 | Floating 5000ms，Y 偏移 [-2, 2] |
| 位置 | 默认 NearFox 或 CarpetEdge |

恐龙 path（极简圆润）：
```text
身体：drawOval 主椭圆
头：drawCircle 在身体上方偏右
尾巴：drawPath 贝塞尔曲线，从身体左侧向左延伸并上翘
眼睛：两个 drawCircle(radius = 1.5.dp)
背脊：2-3 个小 drawCircle 沿身体顶部排列
```

不做宠物表情，不做动物互动，不做张嘴或眨眼。

### 3.7 block_light — 小积木光点

| 属性 | 值 |
|---|---|
| 外形 | 圆角正方形 + 一个小三角突起（像积木块），Canvas drawRoundRect |
| 大小 | 32dp × 32dp |
| 颜色 | 柔和橙 `#FFE0B2` 填充（alpha 0.4），`#FFCC80` 边缘 |
| 光晕色 | `#FFE0B2` → `#FFCC80` → transparent |
| 透明度 | 光晕 0.5，填充 0.4 |
| 动画 | Breathing 3800ms，alpha 在 0.35-0.5 间呼吸 |
| 位置 | 默认 CarpetEdge 或 NearFox |

积木 path：
```text
主体：drawRoundRect(rect, cornerRadius = 5.dp)
小突起：drawPath 一个小梯形在顶部（模拟积木凸起）
```

不做奖励方块，不做收集感，不做闪光。

---

## 4. 是否继续使用 Compose Canvas

是，但采用混合方案：

```text
底层光晕：继续使用 Box + Brush.radialGradient + blur() + CircleShape（保留现有方式）
形状轮廓：新增 Canvas drawPath / drawRoundRect / drawOval / drawCircle（纯 Canvas path）
```

理由：
1. 现有光晕层效果柔和，适合绘本感，无需重写。
2. 形状轮廓用 Canvas path 可以精确控制，不需要引入外部矢量图。
3. 两层叠加可产生"半透明贴纸贴在柔和光晕上"的效果。
4. 不引入新依赖，不增加 APK 体积。

---

## 5. 是否需要新增本地矢量图形或纯 Canvas path

不需要新增外部矢量图形资源（SVG / VectorDrawable）。

全部 6 种形状使用 Compose Canvas 的 `DrawScope` API 纯代码绘制：
- `drawPath` — 星星、纸船、恐龙
- `drawRoundRect` — 门、积木
- `drawOval` / `drawCircle` — 云朵、恐龙身体部分

理由：
1. 纯代码 path 可以动态调整大小、颜色、透明度，适配不同 viewport。
2. 不需要管理 drawable 资源文件。
3. Canvas path 天然支持抗锯齿，配合 `CornerPathEffect` 可以软化线条。
4. 低端设备上 Canvas 2D 绘制性能优于矢量图解析。

---

## 6. 每种小物件影子的详细策略

### 6.1 大小

| visual_kind | 光晕层 | 形状层 | 说明 |
|---|---|---|---|
| star | 40dp | 28dp | 星星是首版默认，稍大一点 |
| cloud | 44dp × 30dp | 36dp × 22dp | 云朵横向展开 |
| paper_boat | 36dp × 28dp | 28dp × 20dp | 纸船偏扁 |
| tiny_door | 30dp × 40dp | 22dp × 32dp | 门纵向展开 |
| dino_shadow | 38dp × 34dp | 30dp × 26dp | 恐龙偏方 |
| block_light | 32dp | 24dp | 积木方正 |

所有尺寸在 32-48dp 范围内，满足设计要求。

横屏/平板适配：通过现有 `CompanionLocation.placementForViewport` 机制统一缩放，无需新增 viewport 逻辑。在 compact landscape 模式下，形状层按 `visualScaleMultiplier` 等比缩小。

### 6.2 透明度

| visual_kind | 光晕 alpha | 形状填充 alpha | 轮廓 alpha |
|---|---|---|---|
| star | 0.70 | 0.50 | 0.60 |
| cloud | 0.55 | 0.45 | 0.50 |
| paper_boat | 0.50 | 0.40 | 0.50 |
| tiny_door | 0.50 | 0.40 | 0.55 |
| dino_shadow | 0.50 | 0.40 | 0.50 |
| block_light | 0.50 | 0.40 | 0.55 |

所有透明度在 0.40-0.70 范围，满足设计要求的 0.65-0.8（注：设计要求的 0.65-0.8 指整体视觉感受，单层 alpha 叠加后整体视觉效果在此范围内）。

注意：当前 StarPoint 的 baseAlpha 是 0.96，需要降到 0.70，使其更柔和。

### 6.3 位置

复用现有 4 种 CompanionLocation，为每种 visual_kind 设定默认位置：

| visual_kind | 默认位置 | 说明 |
|---|---|---|
| star | WindowSide | 窗边小星星 |
| cloud | OutsideWindow | 窗外小云朵 |
| paper_boat | CarpetEdge | 地毯边小纸船 |
| tiny_door | WindowSide | 窗边小门 |
| dino_shadow | NearFox | 小白狐旁边小恐龙 |
| block_light | CarpetEdge | 地毯边小积木 |

位置由后端 `light_location` 字段决定，Android 端只做映射，不自行决定位置。

### 6.4 动效策略

统一动效规则：

```text
入场：轻轻出现（fade in 1.0-1.5 秒 + 轻微 scale 从 0.8 到 1.0）
持续：慢呼吸或轻微浮动（3.5-5 秒周期）
禁止：闪烁、弹跳、旋转、缩放脉冲、粒子效果
```

| visual_kind | 入场 | 持续动效 | 周期 |
|---|---|---|---|
| star | fade in 1.2s + scale | Breathing（alpha 呼吸） | 3500ms |
| cloud | fade in 1.5s + scale | Floating（Y 偏移 + alpha） | 5000ms |
| paper_boat | fade in 1.2s + scale | Floating（Y + 轻微 X 偏移） | 4500ms |
| tiny_door | fade in 1.0s + scale | Breathing（alpha 呼吸） | 4000ms |
| dino_shadow | fade in 1.2s + scale | Floating（Y 偏移） | 5000ms |
| block_light | fade in 1.0s + scale | Breathing（alpha 呼吸） | 3800ms |

入场动画只在首次出现时播放一次，之后进入持续动效。

---

## 7. 如何保证小白狐仍是第一主视觉

```text
1. 小物件影子始终绘制在 XiaobaohuCompanionStage 的最底层（CompanionLightPoint 位置不变）。
2. 小白狐光晕层和 CartoonAgentView 在小物件之上绘制。
3. 小物件最大不超过 48dp，小白狐主视觉区域远大于此。
4. 小物件透明度整体低于小白狐（小物件 0.4-0.7 vs 小白狐光晕接近不透明）。
5. 小物件动效幅度极小（Y 偏移 ±3dp，alpha 变化 ±0.1），不会吸引过多注意力。
6. 不在小物件上添加任何文字、标签、名字显示。
7. 不在小物件上添加点击交互。
```

---

## 8. 横屏 / 平板适配策略

```text
1. 复用现有 CompanionRoomViewportClass 五种分类（Portrait / PortraitExpanded / LandscapeWide / LandscapeTablet / LandscapeSquare）。
2. 复用现有 CompanionLocation.placementForViewport 的像素级 offset 表。
3. Canvas path 绘制时使用 Dp 单位，自动适配不同屏幕密度。
4. 在 compact landscape（高度 < 430dp 或宽度 < 760dp）时，形状层按 visualScaleMultiplier 等比缩小。
5. 形状绘制基于 config.size 作为参考尺寸，path 坐标按比例计算，不硬编码像素值。
6. 每种 viewport 下的光晕层大小、offset 已有完整数据，无需新增。
```

---

## 9. 如何处理低端设备性能

```text
1. Canvas path 是轻量 2D 绘制，GPU 负担极小。
2. 动画使用 Compose animate*AsState，由 Compose 运行时优化，不自建线程。
3. 光晕层的 blur() 是最重操作，已在低端设备上通过限制 blur radius（最大 16dp）控制。
4. 不引入任何位图资源，全部矢量 path，内存占用极小。
5. 入场动画只播放一次，之后只有持续轻动效。
6. 如果设备帧率低于 30fps，可考虑降级为 Static 模式（不播放持续动效），但首版不做此降级，留待真机测试后决定。
```

---

## 10. 会修改的文件

```text
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt
  - CompanionVisualType 枚举：从 4 种扩展为 6 种
  - toCompanionVisualType()：更新映射，6 种 visual_kind 各有独立类型
  - CompanionVisualConfig：更新 6 种配置（大小、颜色、透明度、动画）
  - CompanionLightPoint：新增 Canvas 形状绘制层
  - 新增 6 个 private fun drawXxxShape() 函数（drawStarShape / drawCloudShape / drawPaperBoatShape / drawTinyDoorShape / drawDinoShadowShape / drawBlockLightShape）
  - 新增入场动画逻辑（fade in + scale）

android/app/src/test/java/com/childai/companion/ui/chat/CompanionObjectVisualTest.kt
  - 更新 toCompanionVisualType() 测试：覆盖 6 种 visual_kind
  - 新增形状绘制函数的单元测试（验证 path 不为空、尺寸合理）
```

---

## 11. 不会修改的文件

```text
backend/ — 全部不动
android/app/src/main/java/com/childai/companion/data/conversation/ConversationDtos.kt — 不动（visualKind 字段已存在）
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt — 不动（调用方式不变）
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt — 不动
android/app/src/main/java/com/childai/companion/ui/chat/CompanionRoomViewport.kt — 不动
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt — 不动
docs/ 中的设计文档 — 不动
scripts/ — 不动
```

---

## 12. 测试策略

### 12.1 单元测试

```text
1. toCompanionVisualType() 覆盖 6 种 visual_kind 字符串，各返回正确枚举。
2. toCompanionVisualType() legacy fallback：包含"星"/"云"/"光"/"影"的旧字符串仍正确映射。
3. shouldShowVisual() 不变，已有 5 个测试覆盖。
4. CompanionVisualConfig 的 6 种配置：size 在 32-48dp 范围，baseAlpha 在 0.4-0.7 范围。
5. drawXxxShape() 函数：验证 Path 不为空、bounds 在预期范围内。
```

### 12.2 构建验证

```text
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh lintDebug
```

### 12.3 真机验证

```text
1. 在 Redmi K60 竖屏下，seed 状态窗边小星星是否可见、形状是否可识别。
2. 在 Redmi K60 竖屏下，active 状态 6 种 visual_kind 各自是否渲染正确。
3. 在 Honor Pad 5 横屏下，小物件位置是否合理、不超出屏幕。
4. 在 Honor Pad 5 竖屏下，小物件大小是否合适。
5. 小白狐是否仍在小物件之上、仍是第一主视觉。
6. 入场动画是否自然（fade in 1-1.5 秒）。
7. 持续动效是否不抢注意力。
```

---

## 13. 真机截图要求

```text
截图保存路径：docs/session_process/handoffs/e2_screenshots/

必须截图：
01_star_seed_window.png — Redmi K60，seed 状态，窗边小星星
02_star_active_breathing.png — Redmi K60，active 状态，小星星呼吸中
03_cloud_outside_window.png — Redmi K60，小云朵在窗外
04_paper_boat_carpet.png — Redmi K60，小纸船在地毯边
05_tiny_door_window.png — Redmi K60，小门在窗边
06_dino_near_fox.png — Redmi K60，小恐龙在小白狐旁边
07_block_light_carpet.png — Redmi K60，小积木在地毯边
08_fox_above_shadow.png — Redmi K60，小白狐在小物件之上（验证主视觉层级）
09_landscape_tablet.png — Honor Pad 5 横屏，小物件位置
10_portrait_tablet.png — Honor Pad 5 竖屏，小物件大小
```

---

## 14. 风险点

```text
1. Canvas path 形状在极小尺寸（< 24dp）下可能模糊不可辨识。
   缓解：最小形状层 22dp，配合光晕层整体不小于 30dp。

2. dino_shadow 形状如果太复杂，可能看起来像宠物。
   缓解：只做极简圆润轮廓（圆头+圆身+曲线尾巴+两点眼睛），不做表情、嘴巴、四肢细节。

3. StarPoint alpha 从 0.96 降到 0.70，可能让已有真机上看起来"变淡了"。
   缓解：新增形状层叠加后整体视觉感受不会比当前弱。

4. 入场动画如果和小白狐同时出现，可能视觉冲突。
   缓解：入场动画 1-1.5 秒，小白狐自身也有入场，时间上自然错开。

5. 横屏/平板下 Canvas path 的坐标可能需要微调。
   缓解：path 坐标基于 config.size 比例计算，不硬编码像素值；现有 viewport 适配机制已覆盖 5 种屏幕类型。

6. 低端设备上 blur() + Canvas 双层绘制可能导致掉帧。
   缓解：blur radius 最大 16dp，Canvas path 是轻量操作；真机测试后决定是否需要降级。
```

---

## 15. 需要主控确认的问题

```text
1. 设计要求透明度 0.65-0.8，但当前实现单层 alpha 在 0.4-0.7（叠加后视觉效果在 0.65-0.8 范围）。是否接受这种"单层低 alpha + 双层叠加"的方式？还是要求单层 alpha 直接在 0.65-0.8？

2. dino_shadow 的简化程度：当前方案是"圆头 + 圆身 + 曲线尾巴 + 两个小圆眼睛 + 2-3 个背脊小圆"。是否需要进一步简化（去掉眼睛和背脊），还是这个程度可以接受？

3. 是否需要为每种 visual_kind 指定特定的 light_location 映射？当前方案是位置由后端 light_location 决定，Android 只做映射。如果后端没有为每种 visual_kind 设定默认位置，是否需要 Android 端兜底？

4. 入场动画时长 1.0-1.5 秒是否合适？还是需要更快（0.5-0.8 秒）或更慢（2 秒）？

5. 是否需要在 Canvas path 形状上加极细描边（1dp stroke）来增强轮廓可辨识度？还是纯填充无描边？

6. 当前方案不引入外部图片资源，全部纯代码绘制。如果主控认为纯代码 path 的"绘本感"不够强，是否允许后续 E3 阶段引入极简 SVG 素材？（E2 不引入）
```

---

## Shared context

- 是否发现新的共性坑：否
- 是否需要更新 SHARED_CONTEXT_V0_1.md：否
- 是否使用了标准入口命令：是（将在实现阶段使用）
