# ASR Input Research v0.1

用途：记录 MiMo 音频输入 / ASR 能力调研结论，以及本项目在儿童语音输入上的数据边界。本文档是研究和架构依据，不表示已经启用云端 ASR。

来源：

```text
/Users/wzy/Downloads/mimo_asr_integration_spec.md
```

脱敏处理：

```text
1. 已先扫描外部规格中的 API key、token、真实儿童信息、真实音频路径和其他 secret。
2. 未发现真实 API key、真实儿童身份信息或真实家庭信息。
3. 外部规格中出现的是占位符形式的鉴权字段和示例测试路径；本文档不复制真实密钥、账号、计费信息、真实音频内容或可识别儿童信息。
4. 本文档只保留接口形态、模型名、约束和项目边界。
```

---

## 1. Product Position

当前 confirmed decision 仍然优先：

```text
1. 语音输入 v1 默认 Android 本地 SpeechRecognizer。
2. 识别文本必须 confirm-before-send，不自动进入对话回复。
3. 默认不上传儿童原始音频到后端。
4. Android 不保存模型 API key；任何真实 ASR provider 只能由后端受控调用。
5. 不保存原始音频、长篇逐字转写或真实儿童身份信息到长期记忆。
```

MiMo ASR / audio input 的定位：

```text
1. 是云端 ASR 候选方案，不是 v1 默认路径。
2. 可作为后续 fallback、人工 smoke 或受控实验能力。
3. 必须在儿童音频外发、供应商留存和训练策略完成确认后才能启用。
4. 即使启用，也只返回待确认文本，不能绕过 confirm-before-send。
```

---

## 2. Research Findings

| Topic | Finding | Project Interpretation |
|---|---|---|
| Model names | 外部规格称 `mimo-v2.5` 和 `mimo-v2-omni` 支持音频输入转写。 | 作为 ASR 候选模型记录；真实接入前必须在本项目受控 env 下重新 smoke。 |
| Unsupported ASR-only names | 外部规格称 `MiMo-V2.5-ASR` / `mimo-v2.5-asr` 未开放或不可用。 | 不把 ASR-only 名称写成默认配置。 |
| Endpoint | OpenAI-compatible chat completions endpoint，路径为 `/v1/chat/completions`。 | 后端 provider 层适配，不让 Android 直连供应商。 |
| Mode | 当前规格只证明非流式整段音频输入。 | v1 不做边说边转；streaming audio input 仍是 future research。 |
| Request shape | user message content 同时包含 input audio 和转写指令。 | Provider 层封装，业务层只看到 `audio -> transcript`。 |
| Response shape | 转写文本位于 assistant message content。 | Service 层抽取后返回 `transcript` 和 `requiresConfirmation=true`。 |
| Audio format | 推荐 WAV；规格也列出 MP3 / M4A。 | 后端第一阶段只接受白名单格式，优先 WAV。 |
| Audio params | 建议 16 kHz+、mono、16 bit。 | Android 侧如进入云 ASR，应尽量产出 16 kHz mono WAV。 |
| Duration | 外部规格建议不超过 30 秒。 | 本项目先采用 30 秒硬上限，儿童端也应限制。 |
| Size | 外部规格建议不超过 25 MB。 | 本项目可先采用更保守上限；不允许长录音上传。 |
| Auth | Bearer token；key 从环境变量读取。 | 只能后端临时 env / config 管理，不能进 Android、docs、tests 或 git。 |
| Retention/training | 外部规格没有给出可验证的留存、删除和训练承诺。 | 默认不可外发儿童音频；必须由父亲/产品负责人确认供应商策略后才能启用。 |
| Performance | 外部规格给出 20 秒级测试音频的数秒级延迟。 | 只能作为参考；儿童语音、网络和设备需独立 QA。 |

---

## 3. Streaming And Non-Streaming

当前可作为设计依据的能力：

```text
1. Non-streaming audio input：可提交一段完整音频，等待整段转写结果。
2. Streaming audio input：未确认，不进入当前实现范围。
```

后续如果供应商支持 streaming audio input，也不能直接升级为自动对话模式。必须先补齐：

```text
1. partial transcript 纠错策略。
2. 打断、取消和确认逻辑。
3. 高风险词早期拦截和父亲提醒策略。
4. 原始音频和 partial transcript 的日志脱敏策略。
5. first_partial_ms、final_transcript_ms、error_rate 等 QA 指标。
```

---

## 4. Child Audio Data Boundary

默认边界：

```text
1. Android 不长期保存原始音频。
2. 后端默认不接收原始音频。
3. 如果后续启用云 ASR，音频只在一次转写请求中短暂存在，不写数据库、不进日志、不进 memory。
4. 转写结果在孩子确认前只是 pending transcript，不作为正式 child message。
5. 孩子确认或父亲确认后，才把编辑后的文本发送到 `/api/v1/conversation/message`。
6. 长期记忆只允许保存必要的结构化摘要，不保存原始音频、完整逐字长转写或可识别家庭隐私。
```

云 ASR 启用前必须确认：

```text
1. 供应商是否保存上传音频。
2. 保存多久。
3. 是否用于训练或人工审核。
4. 是否可关闭训练用途。
5. 是否可删除。
6. 数据区域、账号权限、日志和审计范围。
7. 失败请求是否仍会被保存。
```

如果以上信息缺失，项目默认结论是：

```text
MiMo ASR provider disabled; use local Android SpeechRecognizer or text input.
```

---

## 5. Permission And UX Boundary

语音输入权限和体验必须保持：

```text
1. 只有孩子主动点击语音按钮时才请求 RECORD_AUDIO。
2. 不后台录音，不常开麦克风，不做唤醒词。
3. 权限拒绝后继续支持文字输入。
4. 识别失败时温和提示重试或改用打字。
5. 识别文本必须可编辑、可取消、可重说。
6. 不因 ASR 结果直接触发小白狐回复。
```

即使云 ASR 可用，儿童端流程仍是：

```text
tap voice
  -> record short audio
  -> transcribe
  -> show editable transcript
  -> confirm / retry / cancel
  -> confirmed text to conversation API
```

---

## 6. Error And Fallback Categories

| Category | Example | Child-facing fallback |
|---|---|---|
| permission_denied | 麦克风权限被拒绝 | 继续打字，不阻断聊天。 |
| local_asr_unavailable | 设备不支持本地识别 | 改用打字；如果云 ASR 已明确启用，可提示重试语音。 |
| asr_policy_blocked | 未允许儿童音频外发或未确认留存策略 | 不上传音频，回到本地识别或文字输入。 |
| audio_too_long | 超过 30 秒 | 请短一点再说，或直接打字。 |
| audio_too_large | 超过大小上限 | 请重新说短一点。 |
| unsupported_format | 格式不在白名单 | 客户端转 WAV 或改用本地识别。 |
| provider_timeout | 供应商超时 | 不自动重发原始音频；提示稍后重试或打字。 |
| provider_http_error | 外部 HTTP 错误 | 记录脱敏 provider error code，返回温和失败。 |
| empty_transcript | 没有识别出文本 | 提示“我刚才没听清”。 |
| unsafe_pending_text | 待确认文本包含高风险内容 | 仍需确认；确认发送后进入后端安全场景。 |

---

## 7. Recommended QA

全部 QA 使用虚构 child_id、虚构语音内容和专门测试音频，不使用真实儿童身份或真实家庭录音。

| ID | Check | Expected |
|---|---|---|
| ASR-QA-01 | 本地 SpeechRecognizer 正常识别 | 展示可编辑文本，不自动发送。 |
| ASR-QA-02 | 云 ASR disabled | 后端返回 policy blocked 或未启用，不外发。 |
| ASR-QA-03 | 超长音频 | 客户端和后端均拒绝。 |
| ASR-QA-04 | 超大音频 | 后端拒绝，日志不记录 base64。 |
| ASR-QA-05 | 空结果 | 温和提示重试或打字。 |
| ASR-QA-06 | 学习求助语音 | 确认发送后仍走学习引导，不直接给最终答案。 |
| ASR-QA-07 | 高风险语音文本 | 确认发送后触发 safety.guardian 和父亲提醒。 |
| ASR-QA-08 | Secret scan | repo、logs、tests 不含真实 key、真实儿童信息、原始音频和长 base64。 |
| ASR-QA-09 | Latency | 记录 tap-to-transcript ms 和 provider total ms。 |
| ASR-QA-10 | Child voice | 记录儿童声音识别主观准确率和失败样例摘要。 |

---

## 8. Open Questions

```text
1. MiMo audio input 的正式模型名是否应使用 `mimo-v2.5`、`mimo-v2-omni`，还是与现有文本模型配置统一到其他 model id。
2. MiMo 是否提供明确的儿童音频 retention / no-training / deletion policy。
3. MiMo 是否支持真正的 streaming audio input。
4. 后端 ASR endpoint 是否应只作为 DevSettings fallback，还是可进入父亲设置治理。
5. 云 ASR 生成的 pending transcript 是否需要短暂 request_id 级审计字段，且如何避免保存正文。
```

在这些问题未确认前，当前实现方向保持：

```text
Android local ASR first; cloud MiMo ASR disabled by default.
```
