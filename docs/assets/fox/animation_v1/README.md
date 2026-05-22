# 小白狐 animation_v1 序列帧资源记录

来源：父亲 / 产品负责人提供的本机资源包 `/Users/wzy/Downloads/fox`。

当前接入状态：

```text
资源形态：3D 风格 WebP 序列帧动画
Android 路径：android/app/src/main/assets/mascot/xiaobaohu/v1/
运行时文件：mascot_manifest.json、每个状态的 manifest.json、frames_webp/*.webp
未作为运行时依赖提交：验收全量包、PNG frames、preview html、gif/webp 预览、spritesheet 调试文件
Android fallback：animation_v1 -> png_static -> canvas
```

资源清单以 `mascot_manifest.json` 为准，不硬编码状态数量。当前实际状态为 11 个：

| 状态 | 类型 | 帧数 | FPS | 尺寸 |
|---|---|---:|---:|---|
| `safety_concern` | `oneshot_hold` | 24 | 12 | 512x341 |
| `privacy_boundary` | `oneshot_hold` | 24 | 12 | 512x341 |
| `network_error` | `oneshot_hold` | 24 | 12 | 512x341 |
| `speaking` | `loop` | 24 | 12 | 512x341 |
| `thinking` | `loop` | 24 | 12 | 512x341 |
| `listening` | `loop` | 24 | 12 | 512x341 |
| `homework_focus` | `loop` | 24 | 12 | 512x341 |
| `calm` | `loop` | 24 | 12 | 512x341 |
| `sleepy` | `loop` | 24 | 12 | 512x341 |
| `jumping_happy` | `short_loop` | 24 | 12 | 512x512 |
| `idle` | `loop` | 24 | 12 | 512x512 |

优先级：

```text
safety_concern > privacy_boundary > network_error > speaking > thinking > listening > homework_focus > calm > sleepy > jumping_happy > idle
```

运行时体积：

```text
Android assets animation_v1 runtime：约 4.9MB
WebP frames：264 张
```

运行时包处理原则：

```text
1. `dist/accepted/` 只作为美术验收源包、开发转换源包、QA 留档包和重新导出母包。
2. App 内每个状态只保留一套运行时资源；当前选择 512px WebP sequence。
3. 不把 PNG frames、spritesheet、preview、GIF、HTML、QA 文档或 README 随 runtime assets 一起打进 APK。
4. 如后续改为一个状态一个文件，优先 Animated WebP，不主用 GIF。
```

实现约束：

```text
1. 不接 Rive。
2. 不接实时 3D 引擎。
3. 不一次性常驻加载全部帧。
4. 不删除旧静态 WebP fallback。
5. 不删除 Compose Canvas fallback。
6. 不让动画影响 MiMo remote audioUrl 播放。
7. 不在儿童正常界面暴露复杂调试面板。
```

设备 QA 重点：

```text
1. Redmi K60：idle / listening / thinking / speaking / network_error 切换是否流畅。
2. Redmi K60：MiMo 音频播放期间是否进入 speaking。
3. Honor Pad 5 Android 9 / 4GB：是否卡顿、发热、掉帧，是否需要低性能模式。
4. 资源缺失或 manifest 解析失败时是否 fallback 到静态 WebP 或 Canvas。
5. 安全 / 隐私状态优先级是否高于 speaking。
```
