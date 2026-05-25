# Child UI Polish Design v0.1

用途：记录 Task 06 之后儿童端小白狐聊天页的轻量视觉优化方向。本文只覆盖家庭内测前 thin slice，不表示儿童端视觉体验最终完成。

## 1. 目标

```text
1. 第一眼更像“小白狐正在陪我”，而不是控件堆叠。
2. 继续以 voice-first 和统一 ChildTurnUiPhase 为主，不新增复杂动画依赖。
3. 低配横屏不明显挤压消息区和输入栏。
4. 不加入积分、签到、排行榜、宠物饥饿值或连续奖励。
```

## 2. 本轮 thin slice

Android 已做：

```text
1. 小白狐区域增加轻背景，让角色、状态短语和消息区有更清晰层次。
2. 小白狐区域增加短状态 chip，由 ChildTurnUiPhase 派生：
   准备好了 / 正在听 / 正在听懂 / 正在想 / 正在说 / 正在看图 / 可以重说 / 需要大人 / 请大人检查。
3. chip 只显示儿童可理解短语，不显示工程状态、provider、backend 或 debug 信息。
4. 输入栏高度和 voice-first 主按钮逻辑不改，TTS pending/speaking 仍显示“停一下”。
5. Task 07 曾增加轻量 topic shift chips 作为换题出口；Task 09 后，普通话题 chips 改为后端 quick actions / conversation_control 驱动，Android 不再独立硬编码恐龙、太空等固定话题 fallback。它仍不是任务菜单、奖励或留存钩子。
```

## 3. 后续候选

```text
1. 继续验证后端返回的 reviewed/interest-aware seed labels 在 Redmi K60 / Honor Pad 5 上是否可读；仍不得抓实时网络热点。
2. 优化小白狐状态短语和 chip 在 Honor Pad 5 横屏下的字号和留白。
3. 为图片发送中的缩略图、stream 文本增量和 TTS 分段播放补真机视频验收。
```

## 4. 真机 QA

仍需 Redmi K60 / Honor Pad 5 验证：

```text
1. 横屏下小白狐轻背景和 chip 不遮挡动画，不让输入栏变高挤压消息区。
2. Ready / Listening / Recognizing / Thinking / Speaking / ImageProcessing / ServiceError 的 chip 与状态短语一致。
3. stream + TTS 分段播放时 chip 不闪烁到错误状态。
4. 低配设备 animation_v1、静态 WebP、Canvas fallback 都能保持可读。
5. 后端生成的换题 chips 不遮挡 voice-first 主按钮、“停一下”、静音和图片入口；不会让输入栏明显增高挤压消息区。
6. 登录/注册页和家长设置/日报页在横屏和 Honor Pad 5 上可读；孩子端不显示账号 token、密码、provider 或 debug 信息。
```
