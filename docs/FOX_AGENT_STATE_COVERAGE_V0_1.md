# 小白狐动态状态覆盖检查 v0.1

日期：2026-05-20
子会话：Fox-Coverage-1
范围：Android 小白狐 animation_v1 资源、manifest 解析、表现层状态映射和业务触发路径静态检查。

---

## 1. 检查范围

本次只读取并核对以下文件和目录，未修改 Android 代码、后端代码或既有文档：

```text
android/app/src/main/assets/mascot/xiaobaohu/v1/mascot_manifest.json
android/app/src/main/assets/mascot/xiaobaohu/v1/*/v*/manifest.json
android/app/src/main/assets/mascot/xiaobaohu/v1/*/v*/frames_webp/*.webp
android/app/src/main/java/com/childai/companion/mascot/
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt
android/app/src/main/java/com/childai/companion/ui/chat/AgentPresentation.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/config/DevSettings.kt
```

说明：任务中提到的 `FoxAgentUiState.kt` 在当前仓库中不存在；`FoxAgentUiState`、`FoxMood`、`FoxMotion` 和 reply 映射实际定义在 `AgentPresentation.kt`。

---

## 2. Manifest 当前状态

以 `android/app/src/main/assets/mascot/xiaobaohu/v1/mascot_manifest.json` 为准，当前 manifest 包含 11 个状态，没有第 12 个状态。

```text
defaultState: idle
defaultFps: 12
assetPackageVersion: 0.1.1-runtime-webp
state count: 11
statePriority:
  safety_concern, privacy_boundary, network_error, speaking, thinking,
  listening, homework_focus, calm, sleepy, jumping_happy, idle
```

每个状态的主 manifest 条目、子 manifest、`framePattern` 和 24 帧 WebP 均已静态核对。

---

## 3. 覆盖矩阵

| 状态名 | 资源存在 | manifest 可解析 | MascotState 存在 | MascotController 可设置 | 业务触发路径 | QA 状态 |
|---|---|---|---|---|---|---|
| idle | 是。`idle/v0.2.0`，24/24 WebP；静态 fallback `fox_3d_neutral_idle.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.Idle("idle")`。 | 是。默认 `FoxAgentUiState()`、未知 state/reply fallback 都落到 Idle。 | App 初始状态；未知 `emotion` / `agent_motion`；`defaultState=idle`；短循环完成后当前 UI 也会回 idle。 | 静态覆盖通过；需真机确认 idle 动画和静态 fallback 显示。 |
| listening | 是。`listening/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_listening.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.Listening("listening")`。 | 是。`FoxMood.Listening` 或 `FoxMotion.ListeningTail`。 | 后端 reply `emotion=listening/curious` 或 `agent_motion=listening_tail/tail_wag/gentle_tail` -> `toFoxAgentUiState()` -> `MascotController.stateFor()`。 | 静态覆盖通过；需真机确认倾听动画低刺激、不会诱导长聊。 |
| thinking | 是。`thinking/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_thinking.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.Thinking("thinking")`。 | 是。`FoxMood.Thinking` 或 `FoxMotion.ThinkingBlink`。 | 后端 reply `emotion=thinking/focused` 或 `agent_motion=thinking_blink/blink/thinking` -> UI state -> mascot state。 | 静态覆盖通过；需真机确认思考状态不会卡住或遮挡聊天。 |
| speaking | 是。`speaking/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_speaking.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.Speaking("speaking")`。 | 是。`FoxMotion.Speaking` 优先映射。 | 主要由本地 TTS 路径触发：`maybeAutoReadReply()` 接受朗读请求后调用 `asSpeakingPending()`，TTS `onStart` 调用 `asSpeaking()`；后端也可用 `agent_motion=speaking/talking`。 | 静态覆盖通过；需 Redmi K60 验证 remote audio 播放、停止/静音后回到 base state。 |
| homework_focus | 是。`homework_focus/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_homework_focus.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.HomeworkFocus("homework_focus")`。 | 是。`FoxMood.HomeworkFocus` 或 `FoxMotion.HomeworkFocus`。 | 后端学习/拍题链路 reply `emotion=homework/homework_focus` 或 `agent_motion=thinking_nod/homework_focus`；Android mock 拍题成功后继续走 conversation reply 映射。 | 静态覆盖通过；需 QA 确认学习场景仍只引导思路、不直接给答案。 |
| sleepy | 是。`sleepy/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_sleepy.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.Sleepy("sleepy")`。 | 是。`FoxMood.Sleepy` 或 `FoxMotion.SleepyBlink`。 | 后端 bedtime/sleepy reply `emotion=sleepy/bedtime` 或 `agent_motion=sleepy_blink`。 | 静态覆盖通过；需真机确认睡前表现低刺激、可收尾。 |
| calm | 是。`calm/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_calm.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.Calm("calm")`。 | 是。`FoxMood.Calm` 或 `FoxMotion.CalmStill`。 | 后端 reply `emotion=calm/safety/gentle` 或 `agent_motion=calm_still/still/safety_still/calm_breathe`。 | 静态覆盖通过；需 QA 确认安全/安抚文案不制造“只有我懂你”的依赖感。 |
| privacy_boundary | 是。`privacy_boundary/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_privacy_boundary.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.PrivacyBoundary("privacy_boundary")`。 | 是。优先级高于 speaking。 | 后端 privacy boundary reply `emotion=privacy/privacy_boundary/steady` 或 `agent_motion=steady_boundary` -> UI state；manifest priority 位于 safety 之后、network 之前。 | 静态覆盖通过；当前 one-shot completion 在 UI 层会回 idle，需真机确认是否符合“boundary hold”预期。 |
| safety_concern | 是。`safety_concern/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_safety_concern.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.SafetyConcern("safety_concern")`。 | 是。最高优先级。 | 后端高风险/guardian reply `emotion=safety_concern/concerned` 或 `agent_motion=concerned_still`；Android 只展示状态，不在客户端自行放宽安全判断。 | 静态覆盖通过；当前 one-shot completion 在 UI 层会回 idle，需 QA 确认高风险提醒足够稳定且鼓励告诉可信成人。 |
| network_error | 是。`network_error/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_network_error.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.NetworkError("network_error")`。 | 是。优先级高于 speaking。 | Android 本地网络/后端失败直接设置 `FoxMood.NetworkError` + `FoxMotion.NetworkError`；后端也可返回 `emotion=network_error` 或 `agent_motion=network_error`。 | 静态覆盖通过；当前 one-shot completion 在 UI 层会回 idle，需 QA 确认断网错误不会被朗读/动画覆盖。 |
| jumping_happy | 是。`jumping_happy/v0.1.0`，24/24 WebP；静态 fallback `fox_3d_jumping_happy.webp` 存在。 | 是。root 和 state manifest 均可解析。 | 是。`MascotState.JumpingHappy("jumping_happy")`。 | 是。`FoxMood.Encouraging` 或 `FoxMotion.CelebrateSmall`。 | 后端鼓励类 reply `emotion=encouraging/happy/proud` 或 `agent_motion=celebrate_small/small_bounce/encourage`；`FrameSequencePlayer` 按 `short_loop` 播放 2 次后完成。 | 静态覆盖通过；需真机确认庆祝动作轻量，不形成奖励/连击式刺激。 |

---

## 4. 触发链路摘要

动态资源主链路：

```text
ConversationReply.emotion / ConversationReply.agent_motion
  -> AgentPresentation.toFoxAgentUiState()
  -> ChatViewModel.uiState.agent
  -> CartoonAgentView()
  -> MascotController.stateFor()
  -> AssetManifestLoader.loadFrameSequenceOrNull()
  -> FrameSequencePlayer()
```

本地覆盖触发：

```text
TTS pending/start
  -> FoxAgentUiState.asSpeakingPending() / asSpeaking()
  -> speaking

conversation 或 attachment 网络失败
  -> FoxMood.NetworkError + FoxMotion.NetworkError
  -> network_error

ChildChatScreen debug switcher
  -> MascotState.entries
  -> 任意状态手动切换
```

注意：debug switcher 受 `DevSettings.SHOW_MASCOT_DEBUG_SWITCHER=false` 控制，默认不可见。

---

## 5. 发现的问题和后续 QA 点

1. 当前 manifest 没有第 12 个状态；矩阵只覆盖 manifest 中的 11 个状态。
2. `MascotController.stateAfterCompletion()` 只在单元测试中使用；`CartoonAgentView` 当前直接用 `completedShortState` 将已完成的 `short_loop` / `oneshot_hold` 状态切到 `Idle`。因此 `privacy_boundary`、`safety_concern`、`network_error` 的 `oneshot_hold` 是否能按设计保持最后一帧，需要设备侧 QA 或后续代码复核。
3. 本次为静态覆盖检查，没有启动模拟器或真机做视觉渲染确认；设备侧仍需覆盖 Redmi K60 和 Honor Pad 5 的动画流畅度、内存、低配降级和 remote audio speaking 联动。
4. 儿童安全相关状态的资源与映射存在，但最终安全行为仍应以后端 SafetyEngine / SceneOrchestrator / reply contract 为准，Android 不应自行扩展安全判断。
