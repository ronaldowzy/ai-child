# Streaming Interaction Design v0.1

用途：定义 ai-child 下一阶段流式交互方案。本文档只做架构设计，不代表后端或 Android 代码已经实现。

关联事实源：

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
docs/MANUAL_QA_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

核心约束：

```text
1. 保留现有 POST /api/v1/conversation/message。
2. 新增流式链路不得绕过 SafetyEngine、IntentClassifier、SceneOrchestrator、PromptManager、ModelRegistry、ChildAgentRuntime。
3. TTS 外发仍必须通过 TtsDataPolicyGuard。
4. 不在 Android 放模型或 TTS API key。
5. 不保存原始音频、原始照片或不必要的长篇逐字聊天原文。
6. 流式体验不得放松儿童安全边界：不制造秘密关系，不鼓励隐瞒父母，不直接给作业最终答案。
```

当前实现状态：

```text
S-Stream-1 后端骨架已新增独立 router/service/schema/text segmenter：
- backend/app/api/v1/conversation_stream.py
- backend/app/domain/schemas/conversation_stream.py
- backend/app/services/conversation_stream_service.py
- backend/app/services/text_segmenter.py

实现方式是 conservative sentence-level pseudo streaming：
1. 先发送 `session_started`。这个事件可以在完整会话链路执行前 flush，用于让客户端确认 stream 已建立。
2. 通过现有 ConversationService 复用 SafetyEngine、IntentClassifier、SceneOrchestrator、PromptManager、ModelRegistry 和 ChildAgentRuntime。
3. ConversationService 内部注入 no-op TTS，避免旧同步完整 TTS 阻塞 stream 文本。
4. `text_delta` 不是 raw LLM token，也不是 true LLM streaming；它必须等待 ChildAgentRuntime 得到完整回复并通过输出安全检查后，才按 sentence/chunk 伪流式输出。
5. text_final 先完成，再按句子尝试 TTS。
6. TTS 成功发送 audio_ready；TTS 失败发送 recoverable error，但不影响 text_final 和 done。

Coordinator 已在 `backend/app/main.py` 注册 stream router；`/api/v1/conversation/stream` 可通过后端测试和本地 curl 做 NDJSON 验证。Android stream client 尚未接入，生产 UI 仍使用旧 `/api/v1/conversation/message`。

当前延迟口径：
1. `session_started` 可立即出现，适合客户端进入 thinking 状态和记录 request_id。
2. 首个 child-visible `text_delta` 仍等待完整安全 LLM/mock reply，不降低模型生成本身耗时。
3. 当前收益主要是：文字不再等待完整 TTS；音频可按句段生成，而不是等整段回复 TTS 完成。

Ops P0 timing 复用：
1. 每个 stream 请求仍由 request_id middleware 写入 `X-Request-ID`。
2. `app.stream_timing` 记录 `conversation_stream_finished`，字段包含 request_id、session_id_hash、active_scene、first_text_ms、first_audio_ms、stream_total_ms、tts_segment_count 和 error_type。
3. 日志不得记录完整 child text、parent_message_raw、prompt、reply text、TTS segment text、API key 或带签名 query 的 audioUrl。
```

---

## 1. Current Sync Chain Problem

当前 Android 会话链路是完整同步等待：

```text
Android POST /api/v1/conversation/message
  -> backend ConversationService.handle_message()
  -> TimeContextService + ParentPolicyService
  -> SafetyEngine.classify_input()
  -> IntentClassifier
  -> SceneOrchestrator
  -> memory context + short conversation history
  -> ChildAgentRuntime.run()
     -> PromptManager
     -> ModelRegistry
     -> model provider full response
     -> SafetyEngine.classify_output()
  -> TtsService.generate_for_conversation()
     -> MiMo VoiceClone 或 mock TTS 生成完整音频
     -> 返回完整 audio_url
  -> Android 收到完整 text + audio_url
  -> Android remote audio player 播放完整音频
```

主要问题：

```text
1. Android 必须等完整 LLM 回复和完整 TTS 音频生成后，才看到第一段小白狐文字。
2. MiMo VoiceClone 打通后，同步等待会让请求耗时明显变长；45 秒 read timeout 只是临时稳定性修复。
3. 当前 Android 网络错误提示无法区分后端断开、LLM 慢、TTS 慢和音频播放失败。
4. TTS 失败虽不会破坏文本回复，但在同步链路里仍会推迟 Android 收到文本。
5. 现有 `ConversationApiClient` 只读取完整 JSON body，不支持边到边显示。
6. OpenAICompatibleProvider 和 MimoVoiceCloneProvider 当前都是同步返回完整结果，没有已实现的 true streaming provider 接口。
```

设计判断：

```text
1. 第一阶段不应打散主链路，也不应把未经输出安全检查的模型 token 直接显示给孩子。
2. 最小收益来自：文本先于完整 TTS 返回；TTS 按句子/分段生成并排队播放。
3. 如果未来确认 provider 支持 true streaming，也必须增加分段安全缓冲，不能把 raw model delta 直接透传给 Android。
```

---

## 2. Streaming Goals

新链路目标：

```text
child input
  -> backend 接受 POST /api/v1/conversation/stream
  -> 立即返回 stream headers 和 session_started
  -> 安全、意图、场景和 runtime 仍按后端统一链路执行
  -> 通过安全检查后的完整文本按 delta / sentence 伪流式输出
  -> sentence/chunk ready 后触发 TTS segment 生成
  -> audio segment ready 后 Android 排队播放
  -> 文本、语音、小白狐状态和 quick actions 渐进收敛到完整回合
```

阶段目标：

```text
S-Stream-1:
  - 新增 POST /api/v1/conversation/stream。
  - 保守实现：先生成完整安全 reply，再把安全 reply 切成 text_delta。
  - TTS 不再阻塞首个文本 delta；按句子生成 audio segment。
  - 旧 /conversation/message 保持兼容。

S-Stream-2:
  - Android 增加 stream client。
  - 单个 agent bubble 渐进追加文本。
  - TTS audio segment queue 按顺序播放。
  - stream 失败时 fallback 到旧同步接口或保留已有文本。

Future:
  - 调研并确认 MiMo / OpenAI-compatible provider 是否支持 true text/audio streaming。
  - 只有在分段安全策略可验证后，才允许 child-facing model delta 更早输出。
```

体验目标：

```text
1. stream 建立反馈从完整同步等待前移到 `session_started`。
2. 首个 `text_delta` 从“LLM 完整回复 + TTS 完整音频”调整为“完整安全回复文本可用后立即显示”；它仍等待完整 LLM/mock reply。
3. 首音频延迟从“完整回复 TTS”降低到“完整安全回复 + 第一句 TTS segment 可播放”。
4. TTS 失败不影响文本流完成。
5. stream 中断时保留已有安全文本，不让孩子自责，不诱导反复刷请求。
6. 高风险、隐私、学习和睡前场景的安全边界不因流式改变。
```

---

## 3. Backend Endpoint Design

### 3.1 Endpoint

```http
POST /api/v1/conversation/stream
Accept: application/x-ndjson
Content-Type: application/json; charset=utf-8
```

推荐 v0.1 使用 NDJSON，而不是先做 SSE：

```text
1. Android 当前使用 HttpURLConnection，POST + line-by-line JSON 最直接。
2. NDJSON 每行一个完整 JSON event，客户端 parser 简单，可容忍未知 event type。
3. POST body 可以复用现有 conversation request schema。
4. 如果未来需要 Web EventSource，可在 payload 不变的前提下增加 SSE adapter。
```

响应：

```http
HTTP/1.1 200 OK
Content-Type: application/x-ndjson; charset=utf-8
Cache-Control: no-cache
X-Accel-Buffering: no
```

FastAPI route 只负责：

```text
1. 接收 ConversationStreamRequest。
2. 调用 ConversationStreamService。
3. 返回 StreamingResponse。
```

业务逻辑必须放在 service 层。

### 3.1.1 Curl Smoke

启动本地后端：

```bash
bash scripts/dev_backend.sh --host 127.0.0.1 --port 8000
```

文本流 smoke，关闭 TTS，预期不会出现 `tts_started` 或 `audio_ready`：

```bash
curl -sS --no-buffer \
  -X POST http://127.0.0.1:8000/api/v1/conversation/stream \
  -H 'Content-Type: application/json; charset=utf-8' \
  -H 'Accept: application/x-ndjson' \
  -H 'X-Request-ID: stream-curl-smoke-001' \
  -d '{
    "child_id": "stream_demo_child",
    "session_id": "stream_demo_session",
    "input": {
      "type": "text",
      "text": "我想聊恐龙",
      "attachments": []
    },
    "client_context": {
      "device_time": "2026-05-21T16:35:00+08:00",
      "timezone": "Asia/Shanghai",
      "app_mode": "child"
    },
    "stream_options": {
      "protocol_version": "stream.v0.1",
      "text_granularity": "sentence",
      "include_tts": false,
      "audio_delivery": "url",
      "client_turn_id": "curl_smoke_001"
    }
  }'
```

应该看到每行一个 JSON event，大致顺序：

```text
session_started
route_decision
text_delta
sentence_ready
text_final
done
```

带 TTS 的 smoke 只在本地 TTS mock/cache 或明确允许的 dev 配置下运行：

```bash
curl -sS --no-buffer \
  -X POST http://127.0.0.1:8000/api/v1/conversation/stream \
  -H 'Content-Type: application/json; charset=utf-8' \
  -H 'Accept: application/x-ndjson' \
  -H 'X-Request-ID: stream-curl-smoke-tts-001' \
  -d '{
    "child_id": "stream_demo_child",
    "session_id": "stream_demo_tts_session",
    "input": {
      "type": "text",
      "text": "我想聊恐龙。再聊三角龙！",
      "attachments": []
    },
    "client_context": {
      "device_time": "2026-05-21T16:35:00+08:00",
      "timezone": "Asia/Shanghai",
      "app_mode": "child"
    },
    "stream_options": {
      "protocol_version": "stream.v0.1",
      "text_granularity": "sentence",
      "include_tts": true,
      "audio_delivery": "url",
      "client_turn_id": "curl_smoke_tts_001"
    }
  }'
```

TTS provider disabled、blocked 或失败时，预期仍会先看到 `text_final`，随后出现 recoverable `error`，最后 `done.status=completed`。

### 3.2 Request Schema

基础字段复用 `ConversationMessageRequest`：

```json
{
  "child_id": "dev-child",
  "session_id": "android-...",
  "input": {
    "type": "text",
    "text": "我想聊恐龙",
    "attachments": []
  },
  "client_context": {
    "device_time": "2026-05-20T20:30:00+08:00",
    "timezone": "Asia/Shanghai",
    "app_mode": "child"
  },
  "stream_options": {
    "protocol_version": "stream.v0.1",
    "text_granularity": "sentence",
    "include_tts": true,
    "audio_delivery": "url",
    "client_turn_id": "optional-client-generated-id"
  }
}
```

`stream_options` 初始默认：

| Field | Default | Meaning |
|---|---|---|
| `protocol_version` | `stream.v0.1` | 事件协议版本 |
| `text_granularity` | `sentence` | v0.1 优先按句子或短片段输出；未来可支持 token-like delta |
| `include_tts` | `true` | 是否请求后端生成 audio segment |
| `audio_delivery` | `url` | v0.1 只返回 audio URL，不直接流二进制音频 |
| `client_turn_id` | null | Android 可生成，用于断线排查和去重；不得包含儿童身份信息 |

### 3.3 Backend Processing Order

流式 endpoint 必须保持安全前置和统一编排顺序：

```text
1. build parent_policy
2. build time_context
3. SafetyEngine.classify_input(child_text)
4. attachment ready check / Mock OCR context
5. IntentClassifier.classify(...)
6. SceneOrchestrator.route(...)
7. memory_hooks.retrieve_context(...)
8. ConversationHistoryService.get_recent_model_messages(...) for open conversation
9. ChildAgentRuntime.run(...)
   - PromptManager.compose(...)
   - ModelRegistry.generate(...)
   - SafetyEngine.classify_output(...)
   - learning direct-answer guard
   - fallback to SceneRouteDecision.reply_text when unsafe or failed
10. split safe reply into text segments
11. emit text events
12. generate TTS segment URLs through TtsService and TtsDataPolicyGuard
13. emit limited route_decision summary only; do not put debug/session_state internals in text_final
14. record memory/history after safe reply is finalized
```

不得做：

```text
1. 不把 raw model token 直接发给 Android。
2. 不让 TTS 在 SafetyEngine 输出检查前开始。
3. 不让 Android 自己判断安全场景或学习场景。
4. 不在 stream event 里暴露 API key、provider 原始错误、完整 debug internals。
5. 不把原始音频或照片引入 stream request。
```

### 3.4 Conservative v0.1 Streaming Mode

由于当前 `ChildAgentRuntime.run()` 和 provider 都是同步完整回复，v0.1 推荐保守模式：

```text
1. Server 立即 flush `session_started`。
2. Server 执行完整后端安全链路。
3. ChildAgentRuntime 返回已安全检查的最终 reply_text。
4. Server 按 sentence/chunk 输出 `text_delta` 和 `sentence_ready`。
5. Server 输出 `text_final`。
6. Server 随后对每个 sentence/chunk 调用 TTS。
7. 每个 audio_url ready 后输出 `audio_ready`。
```

这不会降低模型生成本身的等待，也不会让 `text_delta` 早于完整安全回复出现；它只去掉“等待完整 TTS 后才显示文字”的体验阻塞，并让音频可以按句段完成。

### 3.5 Future True Model Streaming Mode

只有同时满足以下条件时，才允许 provider true streaming 输出 child-facing text：

```text
1. Provider adapter 支持可取消、可超时、可 fallback 的 stream API。
2. ModelRegistry 仍负责 provider 选择和 data policy guard。
3. ChildAgentRuntime 增加 stream-safe 执行模式，而不是由 API route 直接调 provider。
4. raw token 先进入 server-side safety buffer。
5. buffer 达到句子边界或最小安全片段后，先做局部规则检查。
6. 整轮完成后仍执行 SafetyEngine.classify_output(full_text)。
7. 学习场景必须继续执行 direct-answer guard。
8. 对 high-risk / privacy / bedtime / learning 场景，默认仍可选择 full-buffer-first，更保守。
```

若 final output safety 失败：

```text
1. 如果尚未发送 child-facing model text，直接发送安全 fallback reply。
2. 如果已经发送部分文本，必须停止继续输出，发送 turn.failed_safe_fallback 事件，并在后续版本设计替换/撤回 UI。
3. v0.1 不建议进入这种不可撤回路径，因此默认不直接透传 raw model delta。
```

---

## 4. Stream Event Envelope

每一行是一个 JSON event：

```json
{
  "event_id": "turn_abc:0004",
  "turn_id": "turn_abc",
  "seq": 4,
  "type": "text_delta",
  "created_at": "2026-05-20T20:30:04.123+08:00",
  "request_id": "stream-curl-smoke-001",
  "payload": {}
}
```

通用字段：

| Field | Required | Meaning |
|---|---|---|
| `event_id` | yes | turn 内唯一，便于日志和断点排查 |
| `turn_id` | yes | server turn id；不包含儿童真实身份 |
| `seq` | yes | 从 1 递增 |
| `type` | yes | event type |
| `created_at` | yes | server event time |
| `request_id` | no | request_id middleware value；用于脱敏排查 |
| `payload` | yes | event-specific object |

事件分类：

当前 S-Stream-1 后端实现只保证以下 snake_case 事件。表中 dotted event 是早期设计/未来 adapter 可选名称，Android v1 不应依赖 dotted 名称。

| Type | Purpose |
|---|---|
| `session_started` | stream 已建立；当前 S-Stream-1 实际事件名 |
| `route_decision` | 后端统一路由后的场景摘要；不包含 prompt、证据原文或 provider 细节 |
| `text_delta` | 追加安全文本片段；当前 S-Stream-1 实际事件名 |
| `sentence_ready` | 某个文本句段可用于 TTS 排队 |
| `tts_started` | 某段 TTS 开始生成 |
| `audio_ready` | 某段音频 URL 可播放 |
| `text_final` | 安全文本完整输出完成 |
| `done` | 整轮完成或失败收口 |
| `error` | 可恢复或不可恢复错误；TTS 错误必须可恢复 |
| `turn.started` | stream 已建立 |
| `agent_state` | Android 小白狐状态提示，如 thinking/speaking/network_error |
| `reply.started` | 安全 reply 已准备输出 |
| `text.delta` | 追加文本片段 |
| `text.done` | 文本输出完成 |
| `tts.segment_requested` | 某段 TTS 开始生成，可选 |
| `tts.segment_ready` | 某段音频 URL 可播放 |
| `tts.segment_failed` | 某段音频失败，文本继续 |
| `ui.actions` | 快捷动作 |
| `session.state` | 会话状态 |
| `turn.completed` | 整轮完成 |
| `turn.failed` | 整轮失败，带安全 fallback 或客户端提示策略 |

Android 必须忽略未知 `type`，不能因为新增 event 崩溃。

---

## 5. Text Delta Event Design

### 5.1 `reply.started`

```json
{
  "type": "reply.started",
  "payload": {
    "reply_type": "agent_message",
    "voice_enabled": true,
    "emotion": "encourage",
    "agent_motion": "listening_tail",
    "source": "model",
    "text_granularity": "sentence"
  }
}
```

`source` 只允许：

```text
model
fallback
mock
```

不得把 provider API 细节、raw prompt、raw safety evidence 发给儿童端 UI。

### 5.2 `text_delta`

```json
{
  "type": "text_delta",
  "payload": {
    "index": 0,
    "delta": "三角龙最厉害的是它头上的三根角，",
    "text_range": {
      "start": 0,
      "end": 18
    },
    "sentence_index": 0,
    "is_sentence_end": false
  }
}
```

规则：

```text
1. `delta` 只能来自已通过 ChildAgentRuntime 输出安全检查的 reply_text。
2. Android 按 seq 追加到当前 agent bubble。
3. 同一 turn 只能有一个 active agent bubble。
4. delta 不包含 Markdown 结构、debug 字段或 session_state。
5. 学习场景仍使用引导式文本，不直接给最终答案。
6. 高风险场景 delta 必须来自 safety.guardian / safe fallback，不使用开放聊天语气。
```

### 5.3 `text_final`

```json
{
  "type": "text_final",
  "payload": {
    "text": "三角龙听起来可以聊。你想先说它有趣的地方，还是说你为什么想到它？",
    "char_count": 54,
    "sentence_count": 2,
    "final_text_hash": "sha256:...",
    "is_final": true
  }
}
```

`final_text_hash` 用于排查一致性，不用于恢复原文。日志只记录 hash 和长度，不记录完整儿童回复文本。

---

## 6. TTS Sentence And Segment Event Design

### 6.1 Segmenting Rules

TTS 分段输入必须来自最终安全 reply。

推荐分段规则：

```text
1. 优先按中文句号、问号、感叹号、省略号和英文 . ? ! 切句。
2. 单段目标 20-80 个汉字；过短片段可与下一片段合并。
3. 单段不得超过 backend tts_max_text_chars。
4. 学习场景不要把一个关键提示拆得太碎，避免孩子听不懂上下文。
5. 高风险和隐私场景保持语气稳定，避免戏剧化和强刺激。
6. 睡前场景优先更短、更平稳的分段。
```

### 6.2 `tts_started`

当前实现事件，用于 Android 提前进入 speaking pending：

```json
{
  "type": "tts_started",
  "payload": {
    "index": 0,
    "segment_id": "seg_0",
    "sentence_index": 0,
    "text_range": {
      "start": 0,
      "end": 28
    },
    "play_order": 0,
    "audio_delivery": "url"
  }
}
```

不得在日志里写出完整 segment text。事件本身不需要包含 segment text；Android 可通过已收到的 `text_delta` 和 `text_range` 做 fallback。

### 6.3 `audio_ready`

```json
{
  "type": "audio_ready",
  "payload": {
    "index": 0,
    "segment_id": "seg_0",
    "sentence_index": 0,
    "audioUrl": "/media/tts/xiaobaohu_v01/abc.wav",
    "audio_url": "/media/tts/xiaobaohu_v01/abc.wav",
    "content_type": "audio/wav",
    "text_range": {
      "start": 0,
      "end": 28
    },
    "play_order": 0
  }
}
```

规则：

```text
1. `audio_url` 只指向后端受控 `/media/tts/...wav`。
2. 不暴露 voice sample、metadata json 或 provider raw response。
3. 生成音频前必须通过 TtsDataPolicyGuard。
4. TTS cache metadata 继续只保存 text hash、provider、model、voice sample hash 等必要信息。
5. Android 按 `play_order` 顺序播放；晚到的前段会阻塞后段播放，避免语音顺序错乱。
```

### 6.4 Recoverable TTS `error`

```json
{
  "type": "error",
  "payload": {
    "stage": "tts",
    "code": "tts_failed",
    "recoverable": true,
    "segment_id": "seg_0",
    "sentence_index": 0,
    "text_range": {
      "start": 0,
      "end": 28
    },
    "fallback": "system_tts_or_text",
    "safe_message": "这段声音没有放出来，但文字还在这里。"
  }
}
```

规则：

```text
1. TTS 失败不得中断文本流。
2. Android 可按父亲设置和 DevSettings 决定是否用系统 TTS fallback。
3. 若静音或自动朗读关闭，只记录 segment skipped，不显示错误打扰孩子。
4. provider 原始错误只进入脱敏后端日志，不进儿童 UI。
```

---

## 7. MiMo True Streaming Unknowns

当前项目已验证的事实：

```text
1. MiMo child chat provider 当前通过 OpenAI-compatible /chat/completions 同步返回完整文本。
2. MiMo VoiceClone provider 当前通过 /chat/completions 同步返回完整 JSON。
3. 当前适配从 choices[0].message.audio.data 读取完整 base64 音频。
4. 仓库代码没有 true streaming text/audio provider 接口。
```

必须调研但当前未知的问题：

```text
1. MiMo chat completions 是否支持 stream=true。
2. MiMo VoiceClone 是否支持 true streaming audio chunks。
3. VoiceClone 使用 data:audio/wav;base64 voice sample 时，是否仍支持 streaming。
4. streaming audio 的格式是 PCM、WAV chunk、Opus 还是其他格式。
5. Android MediaPlayer 是否可边下边播该格式，或是否需要 ExoPlayer / AudioTrack。
6. provider 是否支持取消正在生成的 TTS。
7. provider streaming 的首包延迟、分片大小、稳定性、超时和错误语义。
8. provider 对儿童相关文本的留存、训练、删除和审计策略是否覆盖 streaming。
9. streaming 计费方式是否与非流式不同。
10. 中国大陆网络下长连接稳定性是否满足家庭内测。
```

在这些问题确认前：

```text
1. 不把 MiMo true streaming 作为 v0.1 必需能力。
2. 不把 raw audio 或 raw child data 写入文档、测试或日志。
3. 不在 Android 直连 MiMo。
4. 不把 API key 或账号信息写入任何仓库文件。
```

---

## 8. Sentence-Level Pseudo Streaming

如果 MiMo 不支持 true streaming，v0.1 采用 sentence-level pseudo streaming。

### 8.1 Server Flow

```text
1. 建立 stream，发送 `session_started`。
2. 完整执行安全、场景和 ChildAgentRuntime。
3. 得到已安全检查的 reply_text。
4. 切成 sentence/chunk。
5. 发送所有 `text_delta` / `sentence_ready`。
6. 发送 `text_final`。
7. 再按 sentence/chunk 尝试 TTS。
8. 每段 TTS 完成后发送 `audio_ready`；失败发送 recoverable `error`。
9. 所有 TTS 尝试完成后发送 `done`。
```

可接受的并发：

```text
1. TTS segment 可以串行生成，最简单可靠。
2. TTS segment 也可以有限并发生成，但播放必须按 play_order。
3. 并发度需要配置，默认 1 或 2，避免 MiMo 压力和音频乱序。
```

### 8.2 Why This Is Still Useful

现有同步链路：

```text
first_text_ms ~= LLM full reply ms + full TTS ms
first_audio_ms ~= LLM full reply ms + full TTS ms + Android prepare ms
```

pseudo streaming：

```text
session_started_ms ~= stream accepted + flush ms
first_text_ms ~= LLM full reply ms + split/flush ms
first_audio_ms ~= LLM full reply ms + first sentence TTS ms + Android prepare ms
```

也就是说，即使模型文本仍是同步完整生成，也能先解决“文字被完整 TTS 阻塞”的问题；不能把它描述成降低了 LLM 首 token 延迟。

---

## 9. Android Stream Client Design

### 9.1 New Components

建议新增组件，不改现有同步 client 的稳定路径：

```text
ConversationStreamApiClient
  -> POST /api/v1/conversation/stream
  -> read application/x-ndjson line by line
  -> emit Flow<ConversationStreamEvent>

ConversationStreamRepository
  -> 包装 stream client
  -> fallback 到 ConversationRepository.sendTextMessage()

StreamEventParser
  -> tolerant JSON parser
  -> unknown event ignored or logged in dev

AudioSegmentQueuePlayer
  -> 接收 audio_ready
  -> 复用 RemoteAudioTtsController / AudioUrlPlayer 能力
  -> 顺序播放 segment
  -> 支持 stop / mute / clear current turn
```

现有组件保留：

```text
ConversationApiClient
ConversationRepository
RemoteAudioTtsController
AndroidTtsController
MediaPlayerAudioUrlPlayer
TtsUiState
VoiceProfile
```

### 9.2 ChatViewModel Behavior

发送时：

```text
1. 记录 child bubble。
2. 创建一个空 agent bubble，状态为 thinking。
3. 打开 stream。
4. 收到 `text_delta` 后追加到同一个 agent bubble。
5. 收到 `audio_ready` 后加入 audio queue。
6. 收到 `route_decision` 后可更新小白狐状态和必要的内部路由摘要。
7. 收到 `done` 后结束 sending 状态。
```

停止/静音：

```text
1. Stop 只停止当前音频和清空当前 turn 的 queued segments；不删除已显示文字。
2. Mute 后继续显示文本，不播放后续 segment。
3. Auto TTS off 时仍可请求 text stream；后端可通过 include_tts=false 减少 TTS 成本。
4. 离开页面或 ViewModel cleared 时取消 stream、停止 audio queue。
```

儿童 UI：

```text
1. 不显示 provider 名、debug JSON、policy reason、raw error。
2. 文本渐进显示要稳定，不闪烁，不重复追加。
3. 网络或 stream 中断使用温和提示：小白狐这次说到一半停住了，文字先保留，我们可以稍后再试。
4. 不诱导孩子反复点击，不说是孩子说错了。
```

### 9.3 Android Fallback Rules

```text
1. 如果 stream 建立前失败，自动调用旧 /conversation/message，并渲染完整回复。
2. 如果 stream 已收到至少一个 `text_delta`，默认不自动再调用旧接口，避免出现两个不同回复；保留已有文本并显示温和提示。
3. 如果 stream 只收到 `session_started` 但没有文本，可 fallback 旧接口。
4. 如果 `audio_ready` 播放失败，尝试系统 TTS fallback；仍失败则保留文字。
5. 如果 parser 遇到未知 event，忽略；遇到 malformed line，dev log 脱敏记录并继续下一行。
```

---

## 10. Fallback Plan

### 10.1 Backend Fallback

| Failure | Behavior |
|---|---|
| input safety high/critical | 进入 safety.guardian，输出安全回复，不调用开放聊天模型 |
| model provider blocked by data policy | ChildAgentRuntime fallback，输出 SceneRouteDecision.reply_text |
| model timeout/error | ChildAgentRuntime fallback，输出安全场景 fallback text |
| output safety failed | 不输出 raw model text，输出安全 fallback text |
| learning direct-answer detected | 不输出模型答案，输出学习引导 fallback |
| TTS provider disabled/blocked/error | 发送 recoverable `error`，文本继续 |
| client disconnected | 停止后续 event；不要继续为已断开的客户端生成不必要音频 |

### 10.2 Android Fallback

| Failure | Behavior |
|---|---|
| stream connect failure | fallback 到旧同步接口 |
| stream interrupted before text | fallback 到旧同步接口 |
| stream interrupted after text | 保留已有文本，停止 waiting，显示温和提示 |
| audio segment 404/timeout | 系统 TTS fallback 或文字 fallback |
| user taps stop | 停止音频，不取消已显示文本 |
| user sends new message | 取消上一 turn stream 和 audio queue，开始新 turn |

### 10.3 Product Fallback

如果流式效果在 Redmi K60 或 Honor Pad 5 上不稳定：

```text
1. 继续保留 /conversation/message。
2. DevSettings 或父亲设置允许关闭 stream。
3. Android 可按设备降级为同步文本 + audio_url。
4. Honor Pad 5 如音频分段卡顿，可优先文字渐进，音频退回完整段或关闭自动朗读。
```

---

## 11. QA Metrics

所有 QA 使用虚构 child_id、虚构输入、mock 题目；不使用真实儿童身份、真实家庭信息、真实照片或真实音频。

### 11.1 Required Metrics

| Metric | Definition | Source |
|---|---|---|
| `first_text_ms` | Android 点击发送 / 确认发送 到第一个 child-visible `text_delta` 追加完成 | Android client timing |
| `first_audio_ms` | Android 点击发送 / 确认发送 到第一段音频 `onStart` 或可播放确认 | Android audio queue timing |
| `server_first_event_ms` | 后端收到 request 到 `session_started` flush | backend timing |
| `server_reply_ready_ms` | 后端收到 request 到 ChildAgentRuntime 得到安全 reply | backend timing |
| `server_first_audio_ready_ms` | 后端收到 request 到第一段 `audio_ready` | backend timing |
| `total_turn_ms` | Android 点击发送 到 `done` 收到 | Android client timing |
| `total_audio_playback_ms` | Android 点击发送 到最后一段音频播放结束 | Android audio timing |
| `audio_segment_gap_ms` | 相邻音频段播放结束到下一段播放开始的间隔 | Android audio queue timing |
| `stream_interrupt_recovery` | stream 中断后是否保留已有文本并温和提示 | manual QA |

### 11.2 QA Scenarios

| Scenario | Expected |
|---|---|
| 普通兴趣聊天 | 文本渐进显示；不制造唯一朋友关系 |
| 学习求助 | 不直接给最终答案；delta 仍是引导思路 |
| 直接要答案 | 拒绝直接给答案，改为分步提示 |
| 高风险输入 | 进入 safety.guardian，鼓励告诉父母/老师/可信成人 |
| 隐私边界 | 不索要地址、电话、学校、照片等隐私 |
| TTS disabled | text stream 正常，无 audio segment |
| TTS provider blocked | text stream 正常，segment_failed 不吓到孩子 |
| stream disconnect | 已显示文本保留；温和提示；不重复两条 agent 回复 |
| Android mute | text stream 正常，不播放后续 segment |
| Honor Pad 5 低配 | 记录卡顿、发热、音频 gap 和是否需要降级 |

### 11.3 Initial Acceptance Direction

第一轮不硬编码绝对 SLA，先以当前同步链路为 baseline：

```text
1. session_started_ms 应明显早于旧链路完整 JSON response，用于确认连接和 request_id。
2. first_text_ms 只有在旧链路被完整 TTS 明显拖慢时才会改善；它不应被当成 LLM 首 token 指标。
3. first_audio_ms 应低于旧链路完整 audio_url 可播放时间，或至少不更差。
4. total_turn_ms 不应因分段 TTS 明显变差。
5. TTS 失败率不能影响文本完成率。
6. stream 中断恢复不能产生两个互相冲突的小白狐回复。
```

建议记录：

```text
device_model
android_version
backend_commit
apk_build_sha
network
conversation_provider
tts_provider
stream_enabled
first_text_ms
first_audio_ms
total_turn_ms
total_audio_playback_ms
audio_segment_gap_ms
fallback_used
notes
```

---

## 12. Implementation Notes For Later Sessions

S-Stream-1 后端建议：

```text
1. 新增 domain schemas：stream request / event envelope / payloads。
2. 新增 ConversationStreamService。
3. API route 只返回 StreamingResponse。
4. 不删除或改变 ConversationService.handle_message。
5. 先复用 ChildAgentRuntime.run() 的完整安全 reply，再做 pseudo streaming。
6. TTS segment 通过现有 TtsService / TtsDataPolicyGuard。
7. pytest 覆盖：事件顺序、text 不绕过 output safety、TTS 失败不中断文本、旧接口仍可用。
```

S-Stream-2 Android 建议：

```text
1. 新增 ConversationStreamApiClient，不替换 ConversationApiClient。
2. ChatViewModel 增加 stream path feature flag。
3. progressive bubble 必须可测试，避免重复 delta。
4. AudioSegmentQueuePlayer 必须尊重 stop/mute/autoTTS。
5. Android 单测覆盖 parser、fallback、delta append、segment ordering。
```

暂不做：

```text
1. 不做 raw binary audio streaming。
2. 不做云端 ASR。
3. 不做 hands-free conversational mode。
4. 不做 Android 直连 MiMo。
5. 不把 stream 设计写成已完成实现。
```
