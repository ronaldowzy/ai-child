# D3 计划：Android 儿童端小屋小客人呈现

状态：计划待主控审核

更新时间：2026-05-30

---

## 1. 已阅读文档

```text
README.md
AGENTS.md
docs/提示词与文案归属规则_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
docs/session_process/轻量交接协议_2026_05_30_V0_1.md
docs/session_process/handoffs/20260530_D1_companion_object_handoff.md
docs/session_process/handoffs/20260530_D2_runtime_companion_object_handoff.md
docs/小白狐关系与轻连续体验总设计_2026_05_30_V0_1.md
docs/小屋小客人共创延续机制设计_2026_05_30_V0_1.md
docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md
docs/小白狐首次与每日打开体验设计_2026_05_30_V0_1.md
docs/四个核心场景话术与状态库_2026_05_30_V0_1.md
docs/小白狐关系与轻连续体验开发任务清单_2026_05_30_V0_1.md
```

---

## 2. 任务范围理解

D3 负责在 Android 儿童端小白狐小屋页面中渲染"小屋小客人"的轻连续体验。

核心职责：

```text
1. 接收后端 SessionState 中的 companion_object 字段。
2. 根据 state/action 渲染轻视觉点。
3. 保持小白狐为第一主视觉。
4. 小客人只是小星点/小光影/小云影。
```

D3 不负责：

```text
1. 不新增儿童端文案（按钮文案来自后端 quick_actions）。
2. 不自行改按钮文案。
3. 不做小客人列表。
4. 不做收藏册。
5. 不做宠物、心情值、亲密度。
6. 不做装饰系统。
7. 不做任务、奖励、连续打卡。
8. 不改后端。
9. 不改 prompt。
10. 不做家长端。
```

---

## 3. 会修改的文件

| 文件 | 修改内容 |
|---|---|
| `android/app/src/main/java/com/childai/companion/data/conversation/ConversationDtos.kt` | 添加 `CompanionObjectMeta` 数据类，在 `ConversationSessionState` 中添加 `companion_object` 字段解析 |
| `android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt` | 在小屋区域添加小客人轻视觉点渲染逻辑 |
| `android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt` | 添加小客人视觉点 Composable，根据 `light_location` 定位 |
| `android/app/src/test/java/com/childai/companion/data/ConversationDtosTest.kt` | 添加 companion_object 解析测试 |
| `android/app/src/test/java/com/childai/companion/ui/chat/CompanionObjectVisualTest.kt` | 新建：小客人视觉状态映射测试 |

---

## 4. 不会修改的文件

```text
backend/  — 不改后端
docs/提示词与文案归属规则_V0_1.md  — 不改文案规则
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt  — 按钮文案来自后端 quick_actions，不自行修改
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt  — 不改 ViewModel 业务逻辑
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuVisualStateResolver.kt  — 不改小白狐状态解析
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuVisualStateRuntime.kt  — 不改状态防闪烁逻辑
android/app/src/main/java/com/childai/companion/ui/chat/CompanionRoomViewport.kt  — 不改视口分类逻辑
```

---

## 5. 如何接收并解析 companion_object

### 5.1 后端数据结构（来自 D2）

后端 `SessionState` 已包含：

```python
class CompanionObjectMeta(BaseModel):
    id: str
    name: str
    object_type: str      # 小星星 / 小云朵 / 画里的小角色 等
    light_location: str   # 窗边 / 地毯边 / 小白狐旁边 / 窗外
    state: str            # active / paused / seed
    action: str           # recall / co_create / name_seed / none
```

### 5.2 Android 端数据模型

在 `ConversationDtos.kt` 中新增：

```kotlin
data class CompanionObjectMeta(
    val id: String,
    val name: String,
    val objectType: String,
    val lightLocation: String,
    val state: String,
    val action: String,
) {
    companion object {
        fun fromJson(json: JSONObject): CompanionObjectMeta {
            return CompanionObjectMeta(
                id = json.getString("id"),
                name = json.getString("name"),
                objectType = json.getString("object_type"),
                lightLocation = json.getString("light_location"),
                state = json.getString("state"),
                action = json.getString("action"),
            )
        }
    }
}
```

在 `ConversationSessionState` 中添加字段：

```kotlin
data class ConversationSessionState(
    val baseScene: String,
    val activeScene: String,
    val needsInput: String?,
    val requiresParentAttention: Boolean,
    val companionObject: CompanionObjectMeta? = null,  // 新增
)
```

解析逻辑：

```kotlin
companionObject = json.optJSONObject("companion_object")?.let {
    CompanionObjectMeta.fromJson(it)
}
```

---

## 6. 如何渲染 seed 状态

### 6.1 触发条件

```text
companion_object.state == "seed" && companion_object.action == "name_seed"
```

### 6.2 视觉效果

在窗边位置显示一颗小星星光点：

```text
位置：小屋窗边区域（根据 viewportClass 适配）
形态：小星点，柔和光晕，轻微闪烁
颜色：暖黄/金色，alpha 0.6-0.8
尺寸：小，不抢小白狐视觉
动画：轻微呼吸式闪烁，周期约 3 秒
```

### 6.3 技术实现

在 `XiaobaohuCompanionStage.kt` 中新增 `CompanionObjectVisual` Composable：

```kotlin
@Composable
internal fun CompanionObjectVisual(
    companionObject: CompanionObjectMeta?,
    viewportClass: CompanionRoomViewportClass,
    modifier: Modifier = Modifier,
) {
    if (companionObject == null) return

    val location = companionObject.lightLocation.toCompanionLocation()
    val visualType = companionObject.objectType.toCompanionVisualType()

    // 根据 location 和 visualType 渲染对应轻视觉点
    CompanionLightPoint(
        location = location,
        visualType = visualType,
        viewportClass = viewportClass,
    )
}
```

位置映射：

```kotlin
enum class CompanionLocation {
    WindowSide,      // 窗边
    CarpetEdge,      // 地毯边
    NearFox,         // 小白狐旁边
    OutsideWindow,   // 窗外
}
```

视觉类型映射：

```kotlin
enum class CompanionVisualType {
    StarPoint,       // 小星点
    CloudShadow,     // 小云影
    LightSpot,       // 小光影
    SoftOutline,     // 柔和轮廓
}
```

---

## 7. 如何渲染 recall 状态

### 7.1 触发条件

```text
companion_object.state == "active" && companion_object.action == "recall"
```

### 7.2 视觉效果

在 `light_location` 对应位置显示小客人的轻影子：

```text
位置：由 light_location 字段决定（窗边/地毯边/小白狐旁边/窗外）
形态：小光影或小轮廓，比 seed 状态稍明显
颜色：柔和暖色，alpha 0.5-0.7
尺寸：小，不抢小白狐视觉
动画：轻微浮动，周期约 4 秒
```

### 7.3 与 seed 的区别

```text
seed：小星点，窗边固定位置，闪烁式
recall：小光影，根据 light_location 定位，浮动式
```

---

## 8. 如何展示一个轻视觉点

### 8.1 视觉点设计原则

```text
1. 小白狐仍是第一主视觉。
2. 小客人只是小星点/小光影/小云影。
3. 不抢小白狐位置。
4. 不做独立宠物动画。
5. 不做游戏化光效。
6. 不做"领取""解锁""获得"视觉。
```

### 8.2 技术实现

使用 Compose Canvas 绘制轻视觉点：

```kotlin
@Composable
private fun CompanionLightPoint(
    location: CompanionLocation,
    visualType: CompanionVisualType,
    viewportClass: CompanionRoomViewportClass,
) {
    val offset = location.toOffset(viewportClass)
    val infiniteTransition = rememberInfiniteTransition()
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 0.8f,
        animationSpec = infiniteRepeatable(
            animation = tween(3000, easing = EaseInOut),
            repeatMode = RepeatMode.Reverse,
        ),
    )

    Box(
        modifier = Modifier
            .offset(x = offset.x, y = offset.y)
            .size(visualType.size)
            .alpha(alpha)
            .background(
                brush = Brush.radialGradient(
                    colors = visualType.colors,
                ),
                shape = CircleShape,
            )
            .blur(radius = visualType.blurRadius),
    )
}
```

### 8.3 位置适配

根据 `CompanionRoomViewportClass` 适配不同屏幕：

```kotlin
private fun CompanionLocation.toOffset(
    viewportClass: CompanionRoomViewportClass,
): Offset {
    return when (this) {
        CompanionLocation.WindowSide -> when (viewportClass) {
            CompanionRoomViewportClass.Portrait -> Offset(120.dp, (-80).dp)
            CompanionRoomViewportClass.PortraitExpanded -> Offset(160.dp, (-100).dp)
            CompanionRoomViewportClass.LandscapeWide -> Offset(200.dp, (-60).dp)
            // ...
        }
        // 其他位置...
    }
}
```

---

## 9. 如何处理 quick actions

### 9.1 按钮来源

按钮文案完全来自后端 `ui_actions` 中的 `quick_actions`，D3 不自行新增或修改按钮文案。

### 9.2 现有实现

`ChildChatScreen.kt` 中已有 `childCompanionVisibleQuickActions()` 函数处理按钮显示逻辑：

```kotlin
internal fun childCompanionVisibleQuickActions(uiState: ChatUiState): List<QuickActionUi> {
    // 已有逻辑：过滤并显示后端返回的 quick actions
}
```

### 9.3 D3 职责

D3 只负责：

```text
1. 确保 companion_object 字段正确解析。
2. 确保轻视觉点正确渲染。
3. 不修改现有按钮显示逻辑。
```

---

## 10. 横屏 / 平板适配

### 10.1 现有适配机制

`CompanionRoomViewport.kt` 已定义视口分类：

```kotlin
enum class CompanionRoomViewportClass {
    Portrait,
    PortraitExpanded,
    LandscapeWide,
    LandscapeTablet,
    LandscapeSquare,
}
```

### 10.2 小客人视觉点适配

每个 `CompanionLocation` 都需要为不同 `CompanionRoomViewportClass` 提供偏移量：

```text
Portrait: 小屏手机竖屏
PortraitExpanded: 大屏手机/小平板竖屏
LandscapeWide: 宽屏横屏
LandscapeTablet: 平板横屏
LandscapeSquare: 方屏横屏
```

### 10.3 设计原则

```text
1. 小白狐仍是第一视觉。
2. 小屋空间更稳定。
3. 小客人轻视觉点不抢主视觉。
4. 横屏/平板时视觉点位置相对窗边/地毯边保持一致。
```

---

## 11. 测试策略

### 11.1 单元测试

| 测试文件 | 测试内容 |
|---|---|
| `ConversationDtosTest.kt` | companion_object 字段解析：正常解析、字段缺失、null 值 |
| `CompanionObjectVisualTest.kt` | 新建：视觉状态映射、位置映射、类型映射 |

### 11.2 测试用例

```kotlin
// ConversationDtosTest.kt 新增
@Test
fun sessionStateParsesCompanionObject() {
    val json = """
    {
        "base_scene": "daily.after_school",
        "active_scene": "companion.recall",
        "companion_object": {
            "id": "co_123",
            "name": "小棉花",
            "object_type": "小星星",
            "light_location": "窗边",
            "state": "active",
            "action": "recall"
        }
    }
    """
    val state = ConversationSessionState.fromJson(JSONObject(json))
    assertNotNull(state.companionObject)
    assertEquals("小棉花", state.companionObject?.name)
    assertEquals("窗边", state.companionObject?.lightLocation)
}

@Test
fun sessionStateHandlesNullCompanionObject() {
    val json = """
    {
        "base_scene": "daily.after_school",
        "active_scene": "free_chat"
    }
    """
    val state = ConversationSessionState.fromJson(JSONObject(json))
    assertNull(state.companionObject)
}

// CompanionObjectVisualTest.kt 新建
@Test
fun seedStateMapsToStarPoint() {
    val companion = CompanionObjectMeta(
        id = "co_123",
        name = "小棉花",
        objectType = "小星星",
        lightLocation = "窗边",
        state = "seed",
        action = "name_seed",
    )
    assertEquals(CompanionVisualType.StarPoint, companion.toVisualType())
}

@Test
fun recallStateMapsBasedOnObjectType() {
    val star = CompanionObjectMeta(
        id = "co_123",
        name = "小棉花",
        objectType = "小星星",
        lightLocation = "窗边",
        state = "active",
        action = "recall",
    )
    assertEquals(CompanionVisualType.StarPoint, star.toVisualType())

    val cloud = CompanionObjectMeta(
        id = "co_456",
        name = "小云朵",
        objectType = "小云朵",
        lightLocation = "窗外",
        state = "active",
        action = "recall",
    )
    assertEquals(CompanionVisualType.CloudShadow, cloud.toVisualType())
}
```

### 11.3 构建验证

```bash
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh lintDebug
```

---

## 12. 风险点

### 12.1 视觉点位置硬编码

风险：不同设备屏幕尺寸差异可能导致视觉点位置不准确。

控制：

```text
1. 使用相对位置而非绝对像素。
2. 参考现有 mascotOffsetYForViewport() 的适配方式。
3. 真机验证 Redmi K60 和 Honor Pad 5。
```

### 12.2 动画性能

风险：Canvas 绘制 + blur 可能在低端设备上卡顿。

控制：

```text
1. 使用 remember 缓存动画状态。
2. blur 半径保持小值（8-12dp）。
3. 避免在滚动列表中使用。
```

### 12.3 后端字段缺失兼容

风险：后端未返回 companion_object 时 Android 解析失败。

控制：

```text
1. 使用 optJSONObject 而非 getJSONObject。
2. 所有字段使用默认值。
3. null 时不渲染视觉点。
```

### 12.4 小白狐视觉被抢

风险：小客人视觉点过大或过亮，抢了小白狐主视觉。

控制：

```text
1. 视觉点尺寸限制在 16-24dp。
2. alpha 限制在 0.5-0.8。
3. 使用 blur 柔化边缘。
4. 不使用高饱和度颜色。
```

---

## 13. 发现的文档与代码冲突

无冲突。D2 交接文档中定义的 `CompanionObjectMeta` 字段与后端 schema 一致。

---

## 14. 需要主控确认的问题

### 14.1 视觉点具体样式

主控是否需要指定：
- 小星星的具体颜色（暖黄/金色/白色）？
- 小云朵的具体形态（圆润/飘散）？
- 光晕的具体效果（实心/空心/渐变）？

### 14.2 位置精度

light_location 字段值（窗边/地毯边/小白狐旁边/窗外）是否需要更精确的像素级定位，还是由开发方根据小屋布局自行判断？

### 14.3 动画节奏

- 呼吸式闪烁周期 3 秒是否合适？
- 浮动式动画周期 4 秒是否合适？
- 是否需要更慢/更快的节奏？

### 14.4 none 状态处理

当 companion_object 存在但 action="none" 时，是否仍显示视觉点？还是只在 seed/recall 状态下显示？

### 14.5 暂放状态视觉

当 state="paused" 时，是否仍显示视觉点？如果显示，是否需要降低 alpha 或改变颜色以示区分？

---

## 15. 实现依赖

D3 依赖 D2 的后端接口已完成。当前 D2 交接文档显示 companion_object 字段已就绪，D3 可以开始实现。

---

## 16. 预计工作量

```text
数据层：ConversationDtos.kt 修改约 30 行
视觉层：XiaobaohuCompanionStage.kt 新增约 150 行
测试层：约 80 行
总计：约 260 行新增/修改代码
```
