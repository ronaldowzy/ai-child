# Local ASR SenseVoice Design v0.1

用途：记录本项目语音输入从云端 MiMo 优先修订为本地 ASR 优先后的工程方案、数据边界、配置和 QA 要求。

状态：

```text
implementation_plus_non_child_smoke_pass
preferred_real_provider=local_sensevoice
runtime=sherpa-onnx
model=SenseVoice-Small int8 ONNX
fallback_provider=mimo
default_provider=mock
latest_non_child_smoke=PASS provider=local_sensevoice model=model.int8.onnx
```

---

## 1. Decision Summary

```text
1. 语音输入真实识别的第一选择改为 sherpa-onnx + SenseVoice-Small int8 本地推理。
2. Android 仍只负责点击录音、上传后端 ASR 和儿童端语音状态；Android 不保存模型 API key，也不直接接供应商。
3. 后端 `/api/v1/asr/transcribe` 仍只返回 transcript，不直接调用 conversation/message 或 conversation/stream。
4. 本地 ASR 异常时才 fallback 到原有识别方式，默认配置项为 `CHILD_AI_ASR_FALLBACK_PROVIDER=mimo`。
5. MiMo 作为云端 fallback 仍必须通过 ASR data policy gate；未授权时不得外发真实儿童音频。
6. 原始音频只作为一次请求内数据，不入库、不进日志、不进长期 memory、不提交 git。
7. 儿童默认 ASR ok 且 transcript 非空后由 Android 自动发送；DevSettings / 父亲调试模式可查看确认面板。
```

---

## 2. Local Runtime Choice

本轮本机验证结论：

| Candidate | Local result | Project decision |
|---|---|---|
| sherpa-onnx + SenseVoice-Small int8 | Apple M2 / 8GB 上加载约 0.7s，5.6s 中文样例约 83ms，RTF 约 0.015，进程常驻约 471MB。 | 第一选择。中文识别速度和资源占用更适合当前家庭内测。 |
| sherpa-onnx + Fun-ASR-Nano int8 | 加载约 3.6s，7-9s 样例约 0.7-1.3s，RTF 约 0.09-0.14，进程常驻约 1.58GB。 | 备选研究方向，不作为当前第一版默认。 |
| whisper.cpp small/base | 可本地运行，但中文和儿童语音准确率需要额外验证。 | 不作为本轮首选。 |
| 云端 MiMo ASR | 已能通过 fake/smoke audio 跑通 provider 链路，但每轮上传到大模型端识别耗时较高。 | 保留为异常 fallback 和对照测试，不作为第一选择。 |

以上数据只来自非儿童公开测试音频或 synthetic smoke audio，不代表真实儿童声音最终准确率。

---

## 3. Backend Flow

```text
POST /api/v1/asr/transcribe
  -> schema / duration / size / data URI validation
  -> AsrDataPolicyGuard
       - local_sensevoice: local-only, no cloud policy flags required
       - mimo: external provider, all child-audio policy flags required
  -> LocalSenseVoiceAsrProvider
       - lazy import sherpa_onnx and numpy
       - lazy load model.int8.onnx and tokens.txt
       - decode short WAV request bytes in memory
       - return transcript
  -> if local provider raises provider/config/runtime error
       - fallback to configured original provider
       - fallback provider still runs through its policy guard
  -> response with requiresConfirmation=true as backend ASR metadata
  -> Android child mode auto-sends non-empty transcript by product decision
```

边界：

```text
1. API route 不加业务逻辑，只调用 AsrService。
2. 本地模型适配放在 app/providers/asr/。
3. fallback 编排放在 AsrService，不放在 Android。
4. ASR 不调用 SafetyEngine / SceneOrchestrator / ModelRegistry；安全判断仍发生在 transcript 进入 conversation 后。
```

---

## 4. Configuration

当前测试阶段应显式选择 `local_sensevoice` 并验证本地识别链路；未安装本地模型的机器应标记为 BLOCKED，而不是写成通过：

```bash
CHILD_AI_ASR_PROVIDER=local_sensevoice
CHILD_AI_ASR_FALLBACK_PROVIDER=mimo
CHILD_AI_LOCAL_SENSEVOICE_ENABLED=true
CHILD_AI_LOCAL_SENSEVOICE_MODEL_PATH=backend/models/asr/sensevoice/model.int8.onnx
CHILD_AI_LOCAL_SENSEVOICE_TOKENS_PATH=backend/models/asr/sensevoice/tokens.txt
CHILD_AI_LOCAL_SENSEVOICE_NUM_THREADS=4
CHILD_AI_LOCAL_SENSEVOICE_USE_ITN=true
CHILD_AI_LOCAL_SENSEVOICE_LANGUAGE=zh
```

启用本地 ASR：

```bash
cd backend
python -m pip install -e ".[dev,asr-local]"

export CHILD_AI_ASR_PROVIDER=local_sensevoice
export CHILD_AI_LOCAL_SENSEVOICE_ENABLED=true
export CHILD_AI_ASR_FALLBACK_PROVIDER=mimo
```

`CHILD_AI_ASR_FALLBACK_PROVIDER=mimo` 时，如果本地模型缺失、依赖缺失或推理异常，后端会尝试原 MiMo ASR 路径；MiMo 路径仍必须满足 `CHILD_AI_MIMO_ASR_*` policy flags 和 key。若要本地开发时只回退 mock，可临时设置：

```bash
export CHILD_AI_ASR_FALLBACK_PROVIDER=mock
```

模型文件不进入 git；仓库已忽略 `backend/models/`。

---

## 5. Model Files

推荐目录：

```text
backend/models/asr/sensevoice/model.int8.onnx
backend/models/asr/sensevoice/tokens.txt
```

可从 sherpa-onnx 的 SenseVoice ONNX release 下载：

```bash
mkdir -p backend/models/asr/sensevoice /tmp/child-ai-asr-models
curl -L \
  -o /tmp/child-ai-asr-models/sensevoice.tar.bz2 \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
tar -xjf /tmp/child-ai-asr-models/sensevoice.tar.bz2 -C /tmp/child-ai-asr-models
cp /tmp/child-ai-asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/model.int8.onnx backend/models/asr/sensevoice/model.int8.onnx
cp /tmp/child-ai-asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/tokens.txt backend/models/asr/sensevoice/tokens.txt
```

本地模型目录不得提交；如果要复现实验，使用公开非儿童测试音频或 synthetic smoke audio。

---

## 6. Audio Requirements

当前本地 provider 第一版只直接处理 WAV：

| Requirement | Policy |
|---|---|
| Format | `wav` for local SenseVoice; `m4a` may fallback to MiMo if configured and allowed |
| Sample rate | Android 当前录制 16 kHz mono WAV，符合目标 |
| Bit depth | 16-bit PCM preferred |
| Duration | max 30 seconds |
| Decoded size | max 10 MB |
| Storage | request memory only, no DB/log/memory/git persistence |

如需让本地 provider 直接支持 `m4a`，后续应通过明确音频解码库和测试接入，不在 service 层做 ad-hoc shell 转码。

---

## 7. QA

必须验证：

| ID | Check | Expected |
|---|---|---|
| LOCAL-ASR-01 | 后端 mock 默认 | 未配置本地模型时普通测试仍可通过。 |
| LOCAL-ASR-02 | `local_sensevoice` provider 构造 | 不在启动阶段加载模型；第一次识别时懒加载。 |
| LOCAL-ASR-03 | 本地识别非儿童中文测试 WAV | `provider=local_sensevoice`，返回短 transcript，日志不含 base64 或 transcript。 |
| LOCAL-ASR-04 | 本地模型缺失或依赖缺失 | 触发 fallback provider；若 fallback 是 MiMo，仍受 policy guard 控制。 |
| LOCAL-ASR-05 | MiMo policy 未授权 | 本地异常后不得绕过 policy 外发儿童音频。 |
| LOCAL-ASR-06 | 学习求助语音 | transcript 自动发送后仍走学习引导，不直接给最终答案。 |
| LOCAL-ASR-07 | 高风险语音 | transcript 自动发送后进入安全场景并触发父亲提醒。 |
| LOCAL-ASR-08 | 真机延迟 | 记录 tap-to-transcript、provider elapsed、首句回复延迟和失败率。 |

当前自动化测试覆盖 provider 选择、本地 policy allow、本地异常 fallback、mock/MiMo 旧路径和日志脱敏基础。真实中文识别准确率仍需非儿童测试音频和真机 QA。

---

## 8. Smoke Harness

新增本地 smoke harness：

```bash
python scripts/check_local_sensevoice_asr_status.py \
  --audio /path/to/non_child_test.wav \
  --fallback mock \
  --expect-pass \
  --output docs/LOCAL_ASR_SENSEVOICE_SMOKE_V0_1.md
```

状态语义：

| Status | Meaning |
|---|---|
| PASS | `numpy` / `sherpa_onnx` 可 import，`model.int8.onnx` / `tokens.txt` 存在，ASR response provider 为 `local_sensevoice`，status 为 `ok` 或 `needs_retry`。 |
| BLOCKED | 缺依赖、缺模型、缺 tokens、缺 `--expect-pass` 音频，或 local primary 失败后只走了 fallback。`fallback=mock` 可验证兜底链路，但不能写成本地 ASR 通过。 |
| FAIL | 非预期 provider/API 崩溃、route 崩溃，或报告/日志泄漏 raw audio/base64。 |

当前本机收口结果：

```text
date=2026-05-23
status=PASS
audio_source=synthetic_non_child_wav generated via macOS say/afconvert
provider=local_sensevoice
model=model.int8.onnx
transcript_status=ok
report=docs/LOCAL_ASR_SENSEVOICE_SMOKE_V0_1.md
```

该结果只证明本地依赖、模型文件、provider 和服务调用链可跑通；不代表真实儿童语音准确率，不代表 Android 真机 QA，不提交 WAV、ONNX、tokens 或 DB dump。
