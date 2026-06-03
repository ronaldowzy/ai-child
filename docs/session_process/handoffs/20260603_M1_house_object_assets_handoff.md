# M1 小屋小物件素材接入交接

状态：CONDITIONAL

更新时间：2026-06-03

---

## Summary

本轮按主控要求进入 M1：小屋小物件素材设计接入。开发侧不再继续用代码手调 Canvas 形状、alpha、path 来设计小物件；当前 Canvas 实现只作为资源缺失时的 fallback。6 个正式透明背景素材已转为 WebP 并放入 Android `drawable-nodpi`，`visual_kind` 会优先映射到正式素材。

---

## Source

源素材目录：

```text
/Users/wzy/Downloads/ai_child_xiaobaihu_warm_house_icons_512_transparent
```

源素材：

```text
01_star_小星星_512_transparent.png
02_cloud_小云朵_512_transparent.png
03_paper_boat_小纸船_512_transparent.png
04_story_door_小门_512_transparent.png
05_dinosaur_shadow_小恐龙影子_512_transparent.png
06_block_glow_小积木光点_512_transparent.png
```

所有源图均为：

```text
512 x 512 PNG
透明背景
```

---

## Android Resources

转换参数：

```text
cwebp -q 95 -alpha_q 100 -m 6
```

资源路径：

```text
android/app/src/main/res/drawable-nodpi/companion_object_star.webp
android/app/src/main/res/drawable-nodpi/companion_object_cloud.webp
android/app/src/main/res/drawable-nodpi/companion_object_paper_boat.webp
android/app/src/main/res/drawable-nodpi/companion_object_tiny_door.webp
android/app/src/main/res/drawable-nodpi/companion_object_dino_shadow.webp
android/app/src/main/res/drawable-nodpi/companion_object_block_light.webp
```

资源体积：

```text
companion_object_star.webp        40K
companion_object_cloud.webp       32K
companion_object_paper_boat.webp  32K
companion_object_tiny_door.webp   48K
companion_object_dino_shadow.webp 36K
companion_object_block_light.webp 36K
```

未提交源 PNG 到 Android 资源目录。

---

## Mapping

映射位置：

```text
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuCompanionStage.kt
```

映射关系：

```text
star        -> companion_object_star
cloud       -> companion_object_cloud
paper_boat  -> companion_object_paper_boat
tiny_door   -> companion_object_tiny_door
dino_shadow -> companion_object_dino_shadow
block_light -> companion_object_block_light
```

渲染策略：

```text
1. CompanionObjectMeta.shouldShowVisual() 不变。
2. visual_kind 先映射为 CompanionVisualType。
3. CompanionVisualType 再映射到资源名。
4. 运行时通过资源名查找 drawable。
5. 找到资源时使用 Image + painterResource 渲染正式素材。
6. 资源缺失时回退到原 Canvas 绘制。
```

---

## Visual Behavior

保持既有业务状态含义：

```text
seed + name_seed      可见
active + co_create    可见
active + recall       可见
paused / none         不显示
```

视觉差异只做素材层接入：

```text
co_create：素材略大、透明度更高
recall：素材柔和但可见
seed：比 recall 稍明显，作为起名入口提示
```

本轮没有新增：

```text
宠物动画
奖励动画
图鉴
列表
收藏
任务
```

---

## Tests

已运行：

```text
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh testDebugUnitTest --tests com.childai.companion.ui.chat.CompanionObjectVisualTest
bash scripts/android_gradle.sh assembleDebug
```

结果：

```text
通过
```

设备状态：

```text
本轮 doctor 未检测到已连接 Android 真机，因此没有新增真机截图。
```

---

## Known Issues

```text
1. 尚未在 Honor Pad 5 / Redmi K60 上做 M1 素材真机截图回归。
2. 当前仍保留 Canvas fallback，但正式视觉以后应以主控 image2 素材为准。
3. 工作区仍有 storage/ 生成物未跟踪，本轮不提交。
```

