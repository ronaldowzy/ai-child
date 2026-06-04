# S1：奇怪小门 Demo 素材整理交接

日期：2026-06-04

执行角色：素材整理与接入准备会话

素材来源：

```text
/Users/wzy/Downloads/ai-child-strange-door-assets-final-20260604
```

任务边界：

```text
只检查、整理、转换和生成 manifest / 预览图；
不改产品设计；
不新增素材；
不改儿童端文案；
不改 D1 代码；
不启动 UI 编码。
```

---

## 1. 本轮结论

10 个素材全部可用，可以放行 D2 正式 UI 编码。

结论明细：

```text
1. 10 个源文件全部存在。
2. 10 个源文件均为 RGBA PNG，透明背景有效。
3. 10 个源文件尺寸全部符合主控要求。
4. 主体均居中，边缘均保留透明边，没有贴边。
5. 人工预览未发现文字、水印、背景、人物、小白狐、宝箱感或奖励感。
6. 已转换为 lossless alpha WebP。
7. 已放入 android/app/src/main/res/drawable-nodpi/。
8. WebP 文件名与 D1 StrangeDoorAssetContract 完全一致。
9. 已生成素材 manifest。
10. 已生成棋盘格预览图。
```

---

## 2. 源素材检查

| 源文件 | 目标尺寸 | 实际尺寸 | 透明背景 | 主体边缘 | 状态 |
|---|---:|---:|---|---|---|
| `01_strange_door_closed.png` | 1024x1024 | 1024x1024 | 通过 | 有透明边 | usable |
| `02_strange_door_cracked.png` | 1024x1024 | 1024x1024 | 通过 | 有透明边 | usable |
| `03_strange_door_almost_open.png` | 1024x1024 | 1024x1024 | 通过 | 有透明边 | usable |
| `04_strange_door_open.png` | 1024x1024 | 1024x1024 | 通过 | 有透明边 | usable |
| `05_round_lock.png` | 512x512 | 512x512 | 通过 | 有透明边 | usable |
| `06_transform_glow.png` | 512x512 | 512x512 | 通过 | 有透明边 | usable |
| `07_door_success_glow.png` | 512x512 | 512x512 | 通过 | 有透明边 | usable |
| `08_riddle_bubble_panel.png` | 1024x512 | 1024x512 | 通过 | 有透明边 | usable |
| `09_tool_card_panel.png` | 1024x768 | 1024x768 | 通过 | 有透明边 | usable |
| `10_door_ground_shadow.png` | 1024x512 | 1024x512 | 通过 | 有透明边 | usable |

尺寸不符：

```text
无。
```

透明背景问题：

```text
无。
```

风格问题：

```text
未发现文字、水印、背景、人物、小白狐、宝箱感、奖励感、强刺激或恐怖感。
```

---

## 3. Android 资源输出

已输出到：

```text
android/app/src/main/res/drawable-nodpi/
```

文件清单：

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

转换方式：

```text
cwebp -lossless -exact -z 9
```

结论：

```text
已转 WebP。
已保留 alpha。
已放入 drawable-nodpi。
已通过 assembleDebug 资源打包验证。
```

---

## 4. manifest 和预览图

manifest：

```text
docs/assets/strange_door/strange_door_assets_manifest.json
```

manifest 字段包含：

```text
asset_key
file_name
source_file
width
height
transparent_background
android_resource_path
status
```

额外记录：

```text
source_format
android_format
expected_width
expected_height
size_ok
webp_alpha_ok
alpha_bbox
transparent_margins_px
center_offset_px
touches_edge
visual_review
```

预览图：

```text
docs/assets/strange_door/strange_door_assets_preview.png
```

预览图说明：

```text
使用棋盘格背景展示透明边界和主体位置；
用于 D2 UI 编码前快速确认资源内容。
```

---

## 5. 与 D1 合同一致性

D1 合同文件：

```text
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/StrangeDoorAssetContract.kt
```

一致性结论：

```text
1. manifest 中 10 个 file_name 均存在于 StrangeDoorAssetContract。
2. drawable-nodpi 中 10 个 WebP 文件均存在。
3. manifest all_assets_usable=true。
4. 文件名无需调整 D1 合同。
```

---

## 6. 测试和校验

已执行：

```bash
git fetch origin main
git pull --ff-only origin main
file /Users/wzy/Downloads/ai-child-strange-door-assets-final-20260604/*.png
sips -g pixelWidth -g pixelHeight -g hasAlpha /Users/wzy/Downloads/ai-child-strange-door-assets-final-20260604/*.png
cwebp -lossless -exact -z 9 ...
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.strangedoor.*'
```

结果：

```text
PNG 尺寸和透明通道检查通过。
WebP 转换和透明通道复检通过。
manifest 与 D1 合同一致性检查通过。
assembleDebug 通过。
D1 strangedoor 包单测通过。
```

---

## 7. 是否放行 D2

结论：

```text
允许 D2 开始正式 UI 编码。
```

放行条件已满足：

```text
1. 10 个素材齐全。
2. 10 个素材全部可用。
3. Android WebP 资源已落位。
4. manifest 已生成。
5. 预览图已生成。
6. 文件名与 D1 合同一致。
7. Android 构建已验证资源可打包。
```

---

## 8. 未完成事项

```text
1. 未做正式 UI。
2. 未改 ChildChatScreen。
3. 未改 ChatViewModel。
4. 未接拍照真实流程。
5. 未接怪问题真实交互。
6. 未改后端。
```

这些都符合 S1 禁止范围。
