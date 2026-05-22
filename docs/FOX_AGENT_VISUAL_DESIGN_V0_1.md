# 小白狐形象资源规范与设计 Brief v0.1

用途：给非 Codex 设计端提供第一批小白狐形象设计 brief、资源命名和交付规范。本文档只定义资源，不接入资源，不修改 Android 代码。

---

## 0. 已确认输入

本文档遵循 `docs/PRODUCT_DECISIONS_V0_1.md` 中和小白狐相关的 confirmed decisions：

```text
1. 下一阶段优先解决语音交互和小白狐形象体验。
2. 正式名称确定为“小白狐”。
3. 小白狐形象应温和、好奇、活泼开朗，优先采用 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感。
4. Compose Canvas fallback 或 2D 静态图只作为前期替代，不是最终视觉目标。
5. 后端继续通过 reply.emotion 和 reply.agent_motion 向 Android 暴露表现层信号。
6. 小白狐表现层不得制造依赖感。
7. 所有新体验继续遵守儿童安全底线和数据最小化原则。
8. Android 第一版优先使用预渲染 3D PNG/WebP 状态图 + 轻量 Compose 动画，不引入实时 3D 引擎或大型动画依赖作为必需能力。
9. Honor Pad 5 Android 9 / 4GB 是低配兼容性目标设备，不阻塞高配手机上的第一阶段功能闭环。
```

命名约定：

```text
1. 面向儿童端的正式角色名称统一为“小白狐”。
2. Android drawable 资源命名优先使用 fox_3d_*。
3. 旧有“小狐狸”表述只作为历史代码或旧文档背景，不作为新设计 brief 的正式命名。
```

## 1. 角色定位

小白狐是运行在 Android 平板儿童端的统一智能体形象，服务对象是 8 岁儿童，治理者是父亲。它的定位是学习小伙伴和成长教练，负责陪孩子表达、拆解问题、复盘一天、提醒边界和在风险场景中引导孩子找可信成人。

角色应传达：

```text
1. 温和、好奇、有耐心。
2. 亲和、聪明、愿意听孩子慢慢说。
3. 能鼓励孩子说明思路，但不替孩子完成学习任务。
4. 能安静陪伴，也能在需要时做清晰边界提醒。
5. 能表达安全关注，但不制造恐慌。
6. 表现为陪伴和引导，不诱导孩子沉迷。
```

角色不应传达：

```text
1. 它是孩子的真人朋友或情感替代对象。
2. 它比父母、老师或可信成人更重要。
3. 它负责奖励孩子持续使用 App。
4. 它能独立处理所有危险或隐私问题。
```

## 2. 视觉关键词

```text
核心气质：温和、清澈、聪明、好奇、耐心、活泼开朗。
目标风格：3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感。
最终方向：三维立体小白狐形象，适合后续扩展为稳定状态机和轻量动画。
前期替代：Compose Canvas fallback 或 2D 静态占位可以保留，但只用于资源缺失或早期过渡。
年龄适配：适合 8 岁儿童，明亮但保持年龄感。
造型语言：soft rounded child-friendly shape，边缘柔和，表情克制。
主体颜色：白色或浅奶白色为主体，可用浅橙、浅金、柔和青绿或低饱和蓝灰作为少量辅助。
材质方向：柔软、干净、轻毛绒质感；避免油腻高光和塑料玩具质感。
比例方向：头身比例可偏亲和，但不要婴儿化；耳朵和尾巴有识别度。
情绪表达：通过眼睛、耳朵、尾巴、身体重心和小幅动作表达状态。
屏幕适配：在 Android 平板聊天页中作为顶部或中部主视觉，缩小到 96dp 仍能识别。
动作方向：可以有说话、倾听、轻轻蹦跳等状态，但节奏要短、可收尾，不做奖励连击或强刺激循环。
```

## 3. 禁止风格和安全边界

以下内容只能作为禁止项理解，不得作为推荐方向：

```text
1. 不设计成孩子的“唯一朋友”，不表达“只有我懂你”。
2. 不做要求孩子保密、远离父母老师或隐藏聊天的视觉暗示。
3. 不加入排行榜、连击、连击动画、连续签到、抽奖、宝箱、强刺激奖励或上瘾式奖励动画。
4. 不使用真实儿童形象、真实照片、真实音频或可识别家庭信息作为设计素材。
5. 不做过度拟人成人化、恋爱化、偶像化、神秘陪伴者或心理治疗师风格。
6. 不做网红宠物风、强刺激游戏风、赛博风、恐怖谷效果或过度幼稚婴儿化。
7. 不做恐怖、阴暗、压迫、哭喊、夸张惊吓或惩罚式表情。
8. 不做过度兴奋的大幅弹跳、烟花、炫光或高频闪烁动画。
9. 不在图片里写入文字、答案、标语、水印或可变 UI 文案。
10. 不把内向、慢热、不会做题等表现画成缺陷、羞辱或固定负面标签。
11. 不用表现层诱导孩子延长使用时长或反复触发奖励。
```

## 4. 基础形象规格

最终资源目标是三维立体小白狐形象，以 3D rendered PNG/WebP sequence 交付给 Android 使用。前期可继续保留 Compose Canvas fallback 或 2D 静态占位，但不得为了赶进度硬塞低质量临时图片。

```text
画布：1024x1024 px。
格式：3D rendered PNG/WebP sequence，透明背景优先。
主体：白色或浅奶白色小白狐，亲和、温和、聪明、好奇。
主体占比：角色主体建议占画布宽高的 72%-86%，四周保留安全边距。
背景：透明，不要画固定场景背景。
轮廓：柔和圆润，避免尖锐攻击性轮廓。
五官：表情清楚但克制，眼睛和嘴部能支持多状态差异。
比例：各状态保持一致角色比例、头身关系、耳朵位置、尾巴体量和主色。
姿态：consistent character pose and lighting，各状态变化只改变必要表情和小幅姿态。
风格：3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感；not too cartoonishly babyish。
文字：no text baked into image；所有文案由 Android UI 渲染。
光影：柔和、稳定、适合儿童端；避免强对比和复杂反光。
```

建议设计端同时维护一个 3D 源文件母版，用于统一比例、色板、材质、灯光、相机角度和导出。

## 5. 第一批状态列表

| 状态 ID | 使用场景 | 视觉要求 |
|---|---|---|
| `neutral_idle` | 默认聊天、普通问候、无特殊情绪 | 自然站立或坐姿，轻微微笑，耳朵放松，尾巴稳定。 |
| `listening` | 孩子正在输入、语音预留、倾听表达 | 身体略前倾，眼睛专注，耳朵朝前，尾巴小幅上扬。 |
| `speaking` | TTS 朗读、小白狐正在说话 | 开口说话或挥手，活泼但不吵闹，适合短句朗读。 |
| `jumping_happy` | 小进步、鼓励、轻量开心反馈 | 小幅蹦跳或抬脚，不能做连击奖励或强刺激庆祝。 |
| `thinking` | AI 正在生成回复、引导拆题 | 眼神向上或略收，头部轻轻倾斜，表现思考而不是困惑。 |
| `encouraging` | 孩子说清楚想法、完成一步推理 | 温和鼓励，小幅开心，避免胜利式夸张庆祝。 |
| `calm` | 孩子低能量、不想说话、睡前放松 | 呼吸感、低刺激、表情安静，适合慢慢说。 |
| `sleepy` | 睡前复盘、准备收尾 | 眼睛半闭或眨眼，姿态放松，不鼓励继续聊很久。 |
| `safety_concern` | 高风险或需要可信成人介入 | 稳定、认真、关切，避免惊吓；表达“需要大人一起处理”。 |
| `privacy_boundary` | 隐私、陌生人、个人信息边界 | 温和但清晰，姿态坚定，可用轻微护住胸前/停一下的手势。 |
| `homework_focus` | 学习求助、拍题、读题 | 专注、耐心，可带小书本/铅笔等低调学习元素，但不要给答案。 |
| `network_error` | 后端断开或网络不可用 | 轻微抱歉和安静等待，不自责、不催促孩子反复操作。 |

## 6. 第一批动作列表

动作优先通过 Android Compose 对 3D rendered PNG 做轻量位移、透明度或缩放，不要求第一批交付复杂骨骼动画。所有动效都应支持陪伴和引导，不诱导孩子沉迷。

| 动作 ID | 对应状态 | 动作描述 | 节奏要求 |
|---|---|---|---|
| `gentle_blink` | `neutral_idle` | 轻柔眨眼，身体不晃动或极小幅呼吸。 | 慢，低频，不吸引孩子反复等待。 |
| `listening_tail` | `listening` | 尾巴小幅摆动或耳朵轻微前倾。 | 小幅、稳定，表示正在听。 |
| `thinking_nod` | `thinking` | 头部轻点或轻微倾斜。 | 1 次短动作后回到稳定姿态。 |
| `small_encourage` | `encouraging` | 轻轻抬头、微笑或小幅上浮。 | 不超过 360ms 的小反馈。 |
| `calm_breathe` | `calm` | 轻微呼吸起伏。 | 慢速循环，幅度很小。 |
| `sleepy_blink` | `sleepy` | 慢眨眼或眼睛半闭。 | 低刺激，适合收尾。 |
| `concerned_still` | `safety_concern` | 基本静止，只保留认真表情。 | 不做弹跳或庆祝。 |
| `steady_boundary` | `privacy_boundary` | 稳定站姿或轻微停住手势。 | 明确、平静、不吓人。 |

## 7. 资源格式和命名

第一批资源优先目标是 Android 可直接使用的 3D rendered PNG/WebP 静态状态图和本地 WebP 序列帧。当前小白狐 v1 候选静态资产已经导入仓库，包含 11 个状态；父亲随后提供的 animation_v1 动态资源包也已进入 Android assets，并已从验收 PNG 全量包转换为 runtime WebP sequence。它们仍不是最终完整视觉系统，需继续在真实设备上验证资源质量、内存占用、切换流畅度和低配降级。

当前候选资产：

```text
docs/assets/fox/v1/little_white_fox_character_sheet_v1.png
docs/assets/fox/v1/fox_3d_neutral_idle.png
docs/assets/fox/v1/fox_3d_listening.png
docs/assets/fox/v1/fox_3d_speaking.png
docs/assets/fox/v1/fox_3d_jumping_happy.png
docs/assets/fox/v1/fox_3d_thinking.png
docs/assets/fox/v1/calm.png
docs/assets/fox/v1/sleepy.png
docs/assets/fox/v1/safety_concern.png
docs/assets/fox/v1/privacy_boundary.png
docs/assets/fox/v1/homework_focus.png
docs/assets/fox/v1/network_error.png
```

建议 Android drawable 路径：

```text
android/app/src/main/res/drawable-nodpi/fox_3d_character_sheet_v1.webp
android/app/src/main/res/drawable-nodpi/fox_3d_neutral_idle.webp
android/app/src/main/res/drawable-nodpi/fox_3d_listening.webp
android/app/src/main/res/drawable-nodpi/fox_3d_speaking.webp
android/app/src/main/res/drawable-nodpi/fox_3d_jumping_happy.webp
android/app/src/main/res/drawable-nodpi/fox_3d_thinking.webp
android/app/src/main/res/drawable-nodpi/fox_3d_calm.webp
android/app/src/main/res/drawable-nodpi/fox_3d_sleepy.webp
android/app/src/main/res/drawable-nodpi/fox_3d_safety_concern.webp
android/app/src/main/res/drawable-nodpi/fox_3d_privacy_boundary.webp
android/app/src/main/res/drawable-nodpi/fox_3d_homework_focus.webp
android/app/src/main/res/drawable-nodpi/fox_3d_network_error.webp
```

当前 Android 动态序列帧路径：

```text
android/app/src/main/assets/mascot/xiaobaohu/v1/
```

该目录由 manifest 驱动，不使用 `drawable-nodpi` 平铺 frames。运行时保留：

```text
mascot_manifest.json
每个状态 manifest.json
每个状态 frames_webp/*.webp
```

当前 manifest 声明 11 个动态状态：

```text
safety_concern
privacy_boundary
network_error
speaking
thinking
listening
homework_focus
calm
sleepy
jumping_happy
idle
```

所有状态当前均为 24 帧、12 FPS，长边压到 512px，使用透明 WebP sequence。运行时 assets 约 4.9MB。验收全量包、PNG frames、preview html、gif/webp 预览和 spritesheet 调试资料不作为 Android 运行时依赖。详细清单见：

```text
docs/assets/fox/animation_v1/README.md
```

## 7.1 状态覆盖检查要求

父亲真机反馈已确认动态小白狐形象可见，但当前尚不确定每个设计状态是否都由真实业务事件触发。下一阶段必须输出状态覆盖矩阵，不允许把“资源已存在”误写成“业务已覆盖”。

覆盖矩阵应检查：

```text
状态名 | 资源存在 | manifest 可解析 | MascotState 存在 | MascotController 可设置 | 业务触发路径 | QA 状态
```

当前必须检查的状态：

```text
idle
listening
thinking
speaking
homework_focus
sleepy
calm
privacy_boundary
safety_concern
network_error
jumping_happy
```

业务触发期望：

```text
idle：App 默认等待
listening：未来录音中；ASR 前可由 debug/测试入口触发
thinking：发送消息后等待后端或 stream 回复
speaking：播放 MiMo audioUrl 或 fallback TTS 时
homework_focus：learning.homework_help
sleepy：daily.bedtime_reflection
calm：低能量、comfort、calm 回复
privacy_boundary：privacy.boundary
safety_concern：safety.guardian / safety.gentle_checkin
network_error：后端连接失败或 stream 中断
jumping_happy：鼓励、答对、正向反馈后的短循环
```

如果某状态只有资源但没有业务触发，记录为 `resource_ready_but_not_triggered`。

设计交付包中可同步保留源资产路径：

```text
assets/fox/v1/3d/fox_3d_neutral_idle.webp
assets/fox/v1/3d/fox_3d_listening.webp
assets/fox/v1/3d/fox_3d_thinking.webp
assets/fox/v1/3d/fox_3d_encouraging.png
assets/fox/v1/3d/fox_3d_calm.webp
assets/fox/v1/3d/fox_3d_sleepy.webp
assets/fox/v1/3d/fox_3d_safety_concern.webp
assets/fox/v1/3d/fox_3d_privacy_boundary.webp
assets/fox/v1/3d/fox_3d_homework_focus.webp
assets/fox/v1/3d/fox_3d_network_error.webp
```

每个文件要求：

```text
1. 3D rendered PNG/WebP sequence。
2. 1024x1024。
3. transparent background 优先；候选图如仍含背景或阴影，应在资源 QA 中记录并后续替换。
4. sRGB 色彩空间。
5. 文件名全小写 snake_case。
6. consistent character pose and lighting。
7. 角色比例、视角、光源、边距一致。
8. no text baked into image。
9. 不包含水印、UI 按钮、对话气泡或答案内容。
10. 可另外提供 3D 源文件、渲染参数或 2D fallback，但 Android 第一批不依赖复杂动画引擎或实时 3D。
```

可选附加导出：

```text
1. 512x512 PNG：用于轻量预览或低端设备 fallback。
2. 256x256 PNG：用于文档或内部索引预览。
3. 状态对照图：一张总览 PNG，标注状态 ID，仅用于设计评审，不进入儿童端 UI。
4. 2D fallback：在 3D 资源未完成前可用于占位，但必须明确标注为 fallback。
```

## 8. Android 集成方式

当前 Android 端已有 Compose Canvas fallback，并根据后端 `reply.emotion` 和 `reply.agent_motion` 做轻量状态映射。第一版资源接入原则如下：

```text
1. 最终方向是三维立体小白狐形象，优先接入 animation_v1 WebP 序列帧。
2. 旧静态 `fox_3d_*` drawable-nodpi WebP 作为第二层 fallback。
3. 当前 Compose Canvas fallback 必须保留，作为资源缺失、资源加载失败、低性能设备或 3D 资源未交付时的最后显示。
4. 2D 静态图也只作为前期替代，不应取代最终 3D / soft 3D 方向。
5. 资源进入仓库前不要硬编码临时图片，不要引用本地设计软件路径。
6. 不为了动画引入复杂依赖，除非主会话确认。
7. 后端仍只输出语义状态和动作 ID，Android 负责展示映射。
8. 图片不承载业务逻辑、安全判断、学习答案或父亲策略。
9. 不硬塞低质量临时图片；资源质量不达标时继续使用静态 WebP 或 Canvas fallback。
10. 使用 `MascotController` / `AssetManifestLoader` / `FrameSequencePlayer` 播放 animation_v1。
11. 使用 `FoxAgentAssetMapper` 做旧静态资源选择：输入 `FoxAgentUiState` / `FoxMood` / `FoxMotion`，输出 drawable resource id 或 Canvas fallback。
12. 使用 `DevSettings.FOX_RENDER_MODE` 控制渲染模式：`animation_v1` / `png_static` / `canvas` / `auto`。
13. Honor Pad 5 等低配设备必须保留低性能模式：减少动画、降低图片尺寸、关闭自动动画或仅保留静态状态图。
```

建议后续接入映射：

| 后端/界面语义 | 推荐 drawable | 推荐动作 |
|---|---|---|
| 默认、温和 | `fox_3d_neutral_idle.webp` | `gentle_blink` |
| 倾听、孩子输入中 | `fox_3d_listening.webp` | `listening_tail` |
| TTS speaking / future speaking state | `fox_3d_speaking.webp` | 轻量 speaking 状态 |
| 思考、拆题 | `fox_3d_thinking.webp` | `thinking_nod` |
| 鼓励、小进步 | `fox_3d_jumping_happy.webp` | `small_encourage` |
| 安静、低能量 | `fox_3d_calm.webp` | `calm_breathe` |
| 睡前 | `fox_3d_sleepy.webp` | `sleepy_blink` |
| 高风险关注 | `fox_3d_safety_concern.webp` | `concerned_still` |
| 隐私边界 | `fox_3d_privacy_boundary.webp` | `steady_boundary` |
| 学习聚焦 | `fox_3d_homework_focus.webp` | `thinking_nod` |
| 网络错误 | `fox_3d_network_error.webp` | `gentle_blink` |

资源缺失、低性能设备或 QA 发现图像不合适时，继续使用最接近状态或 Canvas fallback，不阻塞 TTS / 对话链路调试。

## 9. 设计端交付物

设计端第一批交付建议包含：

```text
1. 3D 角色设定图：正面为主，必要时补 3/4 视角。
2. 材质和色板：主体白色/浅奶白色、辅助色、线条/阴影、毛绒质感和禁用色说明。
3. 11 张状态 PNG：按 fox_3d_* 命名和 1024x1024 透明背景规格导出。
4. 灯光和相机说明：确保后续追加状态时一致。
5. 动作建议表：8 个动作的幅度、时长、循环方式和注意事项。
6. 缩放预览：1024、512、256、96dp 近似尺寸下的可读性预览。
7. Android 接入备注：哪些状态可以共用同一母版，哪些状态必须单独渲染。
8. fallback 说明：如提供 2D 或 Canvas 参考，只能标记为替代方案。
9. 版权说明：确认素材原创或已获得可商用授权。
```

设计评审时优先看：

```text
1. 是否像稳定的成长教练，而不是刺激性奖励角色。
2. 是否适合 8 岁儿童长期看。
3. 是否具备 soft 3D / 毛绒感 / 立体绘本感，而不是普通扁平插画。
4. 是否能在安全关注和隐私边界场景中保持温和、清晰、可靠。
5. 是否能和当前 Android 的暖色、低压力聊天界面协调。
```

## 10. QA 清单

资源进入仓库或接入 Android 前，至少检查：

```text
1. 文件名和路径符合 android/app/src/main/res/drawable-nodpi/fox_3d_*.webp 规范。
2. 所有 PNG 是 1024x1024，透明背景，sRGB。
3. 10 个状态角色比例、主色、边距、灯光和视角一致。
4. 主体是白色或浅奶白色小白狐，亲和、温和、聪明、好奇。
5. 缩小后仍能分辨 listening、thinking、safety_concern、privacy_boundary。
6. 图片内没有文字、水印、对话气泡、答案或按钮。
7. 动作建议不包含高频闪烁、夸张弹跳或刺激性奖励。
8. safety_concern 不恐吓孩子，privacy_boundary 不羞辱孩子。
9. homework_focus 不暗示直接给最终答案。
10. network_error 不暗示孩子做错了事。
11. Android 仍可在资源缺失时使用 Compose Canvas fallback。
12. 不需要新增复杂动画依赖即可完成第一批表现。
13. 设计端能说明素材版权来源和可使用范围。
14. 未把 2D fallback 或低质量临时图当作最终 3D 方向交付。
15. 高配 Android 手机上 PNG 状态图显示正常。
16. Honor Pad 5 Android 9 / 4GB 上显示不卡顿或有明确降级策略。
17. 进入学习求助时优先显示 homework_focus；资源异常时可复用 thinking 或 Canvas fallback。
18. 进入倾听或普通聊天时显示 listening / neutral 状态。
19. TTS 朗读时后续能切到 speaking 状态。
20. 网络错误时不能崩溃，应 fallback 到 neutral 或 Canvas。
21. 缺失状态资源时不能崩溃。
22. 不引入实时 3D 引擎或大型动画依赖。
```

## 11. 待父亲和设计端确认的问题

```text
1. 3D 小白狐的具体毛绒程度：偏真实软毛，还是偏低多边形/绘本材质。
2. 主体白色和浅奶白色的精确色值，以及是否保留少量浅橙作为耳朵/尾巴辅助识别。
3. 是否允许低调学习道具，例如小书本、铅笔、叶子胸饰。
4. safety_concern 和 privacy_boundary 是否需要更明显的状态差异。
5. 第一批是否只交付 11 张静态 3D rendered PNG，还是同时交付 3D 源文件和渲染参数。
6. 后续资源进入仓库时，由 Android 会话放入 res/drawable，还是先放独立设计资产目录再统一接入。
```
