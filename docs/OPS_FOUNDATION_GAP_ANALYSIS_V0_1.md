# Ops Foundation Gap Analysis v0.1

日期：2026-05-20  
会话：Ops-Foundation-1  
范围：运行基础组件缺口分析和小步补齐计划  
约束：不接第三方 APM，不引入外部日志平台；本地开发和家庭内测必须按测试目标启用真实可验证链路；不改变儿童安全和数据边界。

---

## 1. 结论摘要

当前系统已经具备最小可运行基础：

```text
1. 后端已有 `app.request_timing` 请求耗时日志。
2. 后端已有 `GET /api/v1/health`。
3. 已有 PostgreSQL foundation、SQLAlchemy `pool_pre_ping`、Alembic 和本地 compose。
4. 已有 TTS cache，本地保存 wav 和 metadata，metadata 保存 textHash 而不是原始文本。
5. 已有 `scripts/smoke_mimo_tts.sh`，可验证 MiMo VoiceClone TTS 和 conversation audioUrl。
6. Android 已有网络不可达的儿童友好提示、TTS 诊断和 remote audio fallback。
7. `.gitignore` 已忽略 `.env`、`logs/`、`tmp/` 和 `backend/storage/tts_cache/*`。
```

但家庭内测和后续 stream / TTS 开发仍缺少一层可观测性骨架：

```text
1. 没有 request_id / trace_id，后端日志、Android 报错和 QA 记录无法稳定对应同一请求。
2. 日志仍是普通文本，不是稳定 JSON 字段，后续检索和对比成本高。
3. request timing 只记录 HTTP 总耗时，不拆分 LLM、TTS、cache、DB 和 provider 耗时。
4. health 只能返回 ok，无法区分 backend alive、PostgreSQL、TTS cache、MiMo config 是否健康。
5. env 配置只有 Pydantic 类型解析，缺少组合校验和启动期诊断。
6. 错误分类没有统一字段，Android 只能显示“后端没连上”，父亲/开发者难以判断是 timeout、provider、policy、cache 还是 DB。
7. 还没有 stream latency 指标，后续 stream endpoint 需要预先定义 `first_text_ms`、`first_audio_ms`、`stream_total_ms`。
8. 数据保留和清理策略有原则和 memory TTL，但缺少可执行清理脚本、TTS cache TTL、日志保留窗口和 QA 报告模板。
```

首批建议只做本地可用的基础能力，不引入新平台：

```text
P0-1 request_id middleware
P0-2 结构化 JSON 日志格式
P0-3 request timing 扩展
P0-4 provider timing：LLM latency / TTS latency / cache hit
P0-5 health 扩展：postgres / tts_cache / mimo_config
P0-6 logs 目录和启动脚本统一
```

---

## 2. 现状证据

| 组件 | 当前状态 | 证据 |
|---|---|---|
| 请求耗时日志 | 部分已有 | `backend/app/main.py` 中 `app.request_timing` 记录 method、path、status、elapsed_ms；异常时记录 `request_failed` |
| 日志格式 | 基础已有 | `backend/app/core/logging.py` 使用 `%(asctime)s %(levelname)s %(name)s %(message)s` 文本格式 |
| health endpoint | 基础已有 | `backend/app/api/v1/health.py` 返回 `{"status": "ok"}` |
| PostgreSQL foundation | 基础已有 | `backend/app/db/session.py` 使用 SQLAlchemy engine 和 `pool_pre_ping=True`；`docker-compose.local.yml` 有 Postgres healthcheck |
| TTS cache | 基础已有 | `backend/app/services/tts_cache_service.py` 写入 wav 和 json metadata；metadata 使用 `textHash`，不保存原始 TTS 文本 |
| TTS media path 安全 | 基础已有 | `backend/app/api/tts_media.py` 限制 voice_version、`.wav` 文件名和 cache 目录边界 |
| MiMo TTS smoke | 已有 | `scripts/smoke_mimo_tts.sh` 检查 env、voice sample、TTS endpoint、conversation audioUrl 和 RIFF/WAV |
| Android 错误提示 | 部分已有 | `ChatViewModel` 网络失败时给儿童温和提示；`ConversationApiClient` 包装 HTTP/IO 异常 |
| Android TTS 诊断 | 部分已有 | `AndroidTtsController` 和 `RemoteAudioTtsController` 记录 engine、locale、voice、speak result、remote_audio 状态 |
| logs 目录 | 部分已有 | 仓库已有 `logs/`，`.gitignore` 忽略 `logs/`；但标准启动脚本未统一写入固定日志文件 |
| secret 策略 | 部分已有 | `.env.example` 不含真实 key；provider guard 默认禁用真实外发；smoke 脚本打印 key length 而不是 key |

---

## 3. 缺口矩阵

优先级定义：

```text
P0：后续 stream / TTS / 真机 QA 前应先补。
P1：家庭内测前需要补齐。
P2：可以在第一轮内测后增强。
```

| 检查项 | 当前状态 | 缺口 | 优先级 | 建议补齐 |
|---|---|---|---|---|
| 结构化日志 | 缺失 | 日志不可机器稳定解析，字段不能统一检索 | P0 | 后端改为单行 JSON log，保留 `timestamp`、`level`、`logger`、`event`、`request_id`、`trace_id`、`path`、`status`、`elapsed_ms` |
| request_id / trace_id | 缺失 | Android 报错、后端 request timing、provider 日志无法串联 | P0 | 新增 middleware：读取 `X-Request-ID` 或生成 UUID；响应写回 header；日志 context 自动带 `request_id`；`trace_id` v1 可等于 request_id |
| 请求耗时日志 | 部分已有 | 只有总耗时；无 request_id、route_name、client、error_category | P0 | 扩展 `app.request_timing`：`event=request_finished/request_failed`、`request_id`、`method`、`path`、`status`、`elapsed_ms`、`error_category` |
| LLM latency | 缺失 | 无法判断慢在模型、Prompt、Safety 还是 TTS | P0 | 在 `ModelRegistry.generate()` 或 provider wrapper 记录 `provider_latency_ms`、`provider`、`model`、`task_type`、`fallback_used`、`policy_blocked` |
| TTS latency | 缺失 | MiMo VoiceClone 慢时只能看 HTTP 总耗时 | P0 | 在 `TtsService.generate_xiaobaihu()` 记录 `tts_total_ms`、`tts_provider_ms`、`cache_hit`、`provider`、`model`、`voice_version`、`audio_duration` |
| stream latency | 缺失 | stream endpoint 尚未实现，但指标未预定义 | P0 | 在 stream 设计中固定 `first_text_ms`、`first_audio_ms`、`first_sentence_ms`、`stream_total_ms`、`fallback_to_sync` 字段 |
| 错误分类 | 部分已有 | Python 异常类型存在，但 API/日志没有统一 error category | P0 | 定义本地 error taxonomy：`validation_error`、`policy_blocked`、`provider_timeout`、`provider_http_error`、`provider_parse_error`、`tts_cache_error`、`db_error`、`client_disconnect`、`unknown_error` |
| env 配置校验 | 部分已有 | `Settings` 有类型解析，但缺少组合规则校验 | P0 | 启动时输出 non-secret config summary；校验 MiMo enabled 必须有 key、allow、retention；TTS provider 枚举；cache/sample 路径存在且可读写 |
| secret 不落日志 | 部分已有 | 未发现主动打印 API key；但没有统一 redaction 层，provider HTTP error 可能带回敏感响应片段 | P0 | 建立 redaction filter，统一屏蔽 `api_key`、`authorization`、`token`、`.env` 值；禁止记录完整 request/response body |
| health endpoint | 基础已有 | 只返回 ok，无法定位局部故障 | P0 | 保留 `/health` 简单 ok；新增 `/health/detail` 或扩展 debug-only detail，返回各组件 `ok/warn/fail` |
| PostgreSQL 连接健康 | 缺失于 API | compose 有 Postgres healthcheck，后端 health 不查 DB | P0 | health detail 执行轻量 `SELECT 1`，记录 `postgres.status`、`latency_ms`、`error_category`；不可阻塞普通 health |
| TTS cache 健康 | 缺失于 API | 启动会 mkdir，但不检查可写、剩余空间、metadata 损坏 | P0 | health detail 检查 cache dir exists/writable、voice subdir、sample exists、可选统计 file_count/bytes |
| MiMo provider smoke script | 部分已有 | TTS smoke 已有；通用 LLM MiMo smoke 只在 QA 记录，未标准化脚本 | P1 | 保留 `scripts/smoke_mimo_tts.sh`；新增或补充 `scripts/smoke_mimo_chat.sh`，只用虚构输入，不打印 key 和儿童原文 |
| Android 客户端错误诊断 | 部分已有 | 儿童提示足够温和，但开发者看不到 request_id、HTTP status、timeout kind | P1 | Android request header 加 `X-Request-ID`；失败时 DevSettings 下记录 request_id、endpoint、status、elapsed_ms、exception kind；儿童界面仍只展示温和文案 |
| 本地文件存储路径检查 | 部分已有 | TTS cache path 和 media guard 已有；启动前未统一检查 logs/cache/tmp 权限 | P0 | 新增 startup filesystem check：`logs/`、`backend/storage/tts_cache/`、voice sample、tmp dir；结果写入 startup log 和 health detail |
| QA 报告模板 | 部分已有 | `MANUAL_QA_V0_1.md` 有记录，但没有固定 request_id/latency/health 表格 | P1 | 增加 QA 模板字段：device、backend base URL、request_id、HTTP status、request_elapsed_ms、llm_ms、tts_ms、first_audio_ms、error_category |
| 崩溃日志收集方案 | 缺失 | Android 和 backend 没有统一本地 crash/logcat 采集流程 | P1 | 不接外部 crash 平台；增加本地脚本或 QA 步骤：`adb logcat -d` 过滤 app tag、后端 logs 打包，保存到 ignored `logs/qa/<date>/` |
| 数据保留和清理策略 | 部分已有 | memory 有 TTL；TTS cache、logs、QA artifacts 没有清理策略 | P1 | 明确本地保留窗口：logs 7-14 天、QA 截图/logcat 7 天、TTS cache 可配置 TTL 或容量上限；新增 dry-run 清理脚本 |
| 日志脱敏 | 部分已有 | conversation summary 不记原文，但 Android remote audio prepare 日志会打印完整 URL；后端 HTTP error body 截断但未脱敏 | P0 | Redaction filter + 日志字段白名单；URL 只记录 path 或 hash；禁止完整 child text、reply text、raw audio、photo path、Authorization |

---

## 4. 建议日志字段

### 4.1 通用字段

```json
{
  "timestamp": "2026-05-20T13:00:00.000Z",
  "level": "INFO",
  "logger": "app.request_timing",
  "event": "request_finished",
  "request_id": "req_...",
  "trace_id": "req_...",
  "environment": "dev"
}
```

### 4.2 HTTP request timing

```json
{
  "event": "request_finished",
  "request_id": "req_...",
  "method": "POST",
  "path": "/api/v1/conversation/message",
  "status": 200,
  "elapsed_ms": 10543.5,
  "client": "android",
  "error_category": null
}
```

禁止字段：

```text
完整 child_text
完整 reply_text
Authorization / API key / token
原始音频路径
原始照片路径
完整 provider request/response body
```

### 4.3 provider timing

```json
{
  "event": "model_provider_finished",
  "request_id": "req_...",
  "task_type": "child_chat",
  "provider": "mimo",
  "model": "mimo-v2.5-pro",
  "latency_ms": 4210.8,
  "fallback_used": false,
  "policy_blocked": false,
  "error_category": null
}
```

```json
{
  "event": "tts_provider_finished",
  "request_id": "req_...",
  "provider": "mimo",
  "model": "mimo-v2.5-tts-voiceclone",
  "voice_version": "xiaobaohu_v01",
  "cache_hit": false,
  "tts_total_ms": 6120.4,
  "provider_latency_ms": 5900.2,
  "audio_duration_ms": 2800,
  "error_category": null
}
```

### 4.4 future stream timing

```json
{
  "event": "conversation_stream_finished",
  "request_id": "req_...",
  "first_text_ms": 700.0,
  "first_sentence_ms": 1800.0,
  "first_audio_ms": 3200.0,
  "stream_total_ms": 9800.0,
  "chunks_text": 12,
  "chunks_audio": 3,
  "fallback_to_sync": false,
  "error_category": null
}
```

### 4.5 Healthy Engagement observability

Task 04 已新增 `app.healthy_engagement` 本地结构化日志，用于家庭内测前看清小白狐是否尊重儿童边界、是否过度追问、以及 stream 首字/首音频是否过慢。该日志不是留存、签到或成瘾指标。

非 stream turn：

```json
{
  "event": "healthy_engagement_turn",
  "request_id": "req_...",
  "child_id_hash": "sha256:...",
  "session_id_hash": "sha256:...",
  "active_scene": "conversation.open",
  "age_band": "age_7_8",
  "reply_char_count": 32,
  "question_count": 0,
  "turn_guidance_hints": ["child_requests_topic_change"],
  "boundary_signal": "no_chat",
  "boundary_respected": true,
  "same_topic_score": 1,
  "consecutive_recent_questions": 0,
  "reply_normalized": true,
  "first_text_ms": null,
  "first_audio_ms": null,
  "turn_total_ms": 245.1,
  "runtime_source": "model",
  "fallback_reason": null
}
```

stream turn 完成时会补一条 `healthy_engagement_stream`，把 `first_text_ms`、`first_audio_ms`、`turn_total_ms` 写入同一类非原文字段。

禁止字段保持不变：

```text
完整 child_text
完整 reply_text
父母寄语原文
原始音频路径
原始照片路径
完整 provider request/response body
Authorization / API key / token
```

---

## 5. Health 扩展建议

保留当前轻量接口：

```text
GET /api/v1/health
-> {"status": "ok"}
```

新增本地开发和 QA 使用的 detail 接口：

```text
GET /api/v1/health/detail
```

建议返回：

```json
{
  "status": "ok",
  "environment": "dev",
  "components": {
    "api": {"status": "ok"},
    "postgres": {"status": "ok", "latency_ms": 12.3},
    "tts_cache": {
      "status": "ok",
      "path_configured": true,
      "exists": true,
      "writable": true,
      "file_count": 24
    },
    "xiaobaohu_voice_sample": {
      "status": "ok",
      "exists": true,
      "sha256_prefix": "8eec0f98"
    },
    "mimo_chat_config": {
      "status": "disabled",
      "enabled": false,
      "api_key_present": false,
      "child_data_allowed": false,
      "retention_policy_checked": false
    },
    "mimo_tts_config": {
      "status": "disabled",
      "enabled": false,
      "api_key_present": false,
      "child_text_allowed": false,
      "retention_policy_checked": false
    }
  }
}
```

注意：

```text
1. detail health 不输出完整 API key、完整数据库 URL、完整本地绝对路径中的敏感片段。
2. `api_key_present` 只能是 boolean。
3. Postgres 失败不应让简单 `/health` 误报服务进程死亡；detail 中标记 `postgres.status=fail`。
4. MiMo disabled 是正常状态，不是 fail；enabled 但缺 key/allow/retention 才是 warn/fail。
```

---

## 6. Android 诊断建议

儿童界面保持当前温和文案，不暴露技术细节：

```text
小白狐现在没有连上后端。我们先停一下，请大人检查网络后再试。
```

DevSettings 或父亲诊断视图应补充：

```text
1. request_id
2. endpoint
3. HTTP status
4. elapsed_ms
5. exception kind: timeout / connection_refused / unknown_host / http_error / parse_error
6. backend response header `X-Request-ID`
7. audio_url playback source: remote_audio / system_tts_fallback / text_only
8. first_audio_ms：remote audio request accepted 到 MediaPlayer onStart 的时间
```

Android 不应记录：

```text
完整 child text
完整 agent reply
真实儿童姓名
真实音频内容
模型 API key
```

---

## 7. 本地文件和日志目录策略

当前 `.gitignore` 已忽略：

```text
.env
logs/
tmp/
backend/storage/tts_cache/*
```

建议统一运行输出：

```text
logs/backend_dev_<port>.log
logs/qa/<date>/<device>_logcat.txt
logs/qa/<date>/backend_excerpt.log
logs/qa/<date>/health_detail.json
```

启动脚本建议：

```text
1. `scripts/dev_backend.sh` 支持 `CHILD_AI_LOG_TO_FILE=true`。
2. 默认创建 `logs/`，但不强制所有开发启动都重定向。
3. 启动时打印日志文件路径、base URL、environment、provider summary。
4. 禁止把 `.env` 内容 dump 到日志。
```

TTS cache 建议：

```text
1. health detail 检查 cache dir 可写。
2. metadata 继续只保存 textHash，不保存原始文本。
3. 清理策略先支持 dry-run：按 age 或总大小删除 wav/json 成对文件。
4. 清理日志只记录 cache_key 前 8 位、文件数量和字节数。
```

---

## 8. QA 报告模板补充

后续 `MANUAL_QA` 或独立 QA 记录建议统一增加：

| 字段 | 示例 |
|---|---|
| QA 日期 | 2026-05-20 |
| 设备 | Redmi K60 / Honor Pad 5 |
| Android 版本 | Android 14 / Android 9 |
| 后端 base URL | `http://192.168.0.118:8000/` |
| request_id | `req_...` |
| 场景 | 普通聊天 / TTS / 学习求助 / stream |
| HTTP status | 200 / timeout / 502 |
| request elapsed ms | 10543.5 |
| LLM latency ms | 4210.8 |
| TTS latency ms | 6120.4 |
| first text ms | stream 场景填写 |
| first audio ms | TTS / stream 场景填写 |
| error category | `provider_timeout` / `client_timeout` / `none` |
| 儿童界面文案 | 是否温和、是否泄漏 debug |
| 日志脱敏检查 | 无 key、无完整儿童原文、无真实音频/照片 |

---

## 9. 数据保留和清理策略

当前原则已经正确：

```text
1. 长期记忆只保存结构化摘要。
2. 不保存原始音频、原始照片或长篇逐字聊天。
3. TTS cache metadata 保存 textHash，不保存原始 TTS 文本。
4. 真实 provider 外发需要显式 allow 和 retention policy checked；进入测试范围后必须实际验证或标记 BLOCKED/FAIL。
```

仍需补齐可执行策略：

| 数据类型 | 建议 v0.1 本地保留 | 清理方式 |
|---|---|---|
| backend logs | 7-14 天 | 本地脚本按 mtime 删除，dry-run 默认 |
| QA logcat / 截图 | 7 天 | 保存到 ignored `logs/qa/`，人工确认后删除 |
| TTS cache wav/json | 14-30 天或容量上限 | 按 age/size 删除 wav/json 成对文件 |
| PostgreSQL conversation messages | 待 DB1-C 决策 | 不保存 debug、原始音频、照片路径；可配置保留期 |
| structured memories | 已有 per-type TTL | 继续使用 `expires_at`，后续加定期清理 |
| parent reports | 待 DB1-E 决策 | 不含逐字聊天；保留期由父亲设置治理 |

---

## 10. 小步实现计划

### Phase 1：P0 本地可观测性骨架

修改范围建议：

```text
backend/app/core/logging.py
backend/app/main.py
backend/app/core/config.py
backend/app/api/v1/health.py
backend/app/services/model_registry.py
backend/app/services/tts_service.py
scripts/dev_backend.sh
backend/app/tests/
```

实现：

```text
1. request_id middleware：生成/透传 `X-Request-ID`，响应写回。
2. 结构化 JSON log formatter：本地 stdout 和可选 file 共用。
3. request timing 扩展：加入 request_id、error_category、status、elapsed_ms。
4. provider timing：ModelRegistry 和 TtsService 记录 provider latency。
5. health detail：postgres、tts_cache、voice sample、mimo config。
6. logs 目录和启动脚本统一：可选 `CHILD_AI_LOG_TO_FILE=true`。
```

测试：

```text
1. pytest：health detail 正常/失败分支。
2. pytest：request_id header 透传和生成。
3. pytest：日志不含 Authorization、API key、完整 child text。
4. pytest：provider timing fallback/policy_blocked 字段。
5. `bash scripts/test_backend.sh`。
6. `bash scripts/lint_backend.sh`。
```

当前实现状态（2026-05-21）：

```text
已完成 P0 thin slice。
1. 新增 request_id middleware：生成/透传安全的 `X-Request-ID`，响应头写回；非法或超长 header 会被替换。
2. 后端日志改为单行 JSON structured log，并通过 request_id 上下文关联 request timing、model timing 和 TTS timing。
3. `app.request_timing` 记录 `request_finished` / `request_failed`、method、path、status_code、elapsed_ms 和 error_type。
4. `ModelRegistry.generate()` 记录 `model_call_finished`，包含 task_type、provider、model、elapsed_ms、fallback_used、policy_blocked、error_type、child_id_hash 和 session_id_hash。
5. `TtsService.generate_xiaobaihu()` 记录 `tts_call_finished`，包含 provider、model、voice_version、emotion、cache_hit、elapsed_ms、audio_bytes、text_chars、cache_key_prefix 和 error_type。
6. 新增 `GET /api/v1/health/detail`，检查 postgres、tts_cache、xiaobaohu_voice_sample 和 mimo_tts_config；组件异常返回 degraded，不让 detail endpoint 直接 500。
7. 新增后端测试覆盖 request_id、日志脱敏、model/TTS timing、health detail 不泄露 API key、postgres degraded 和 tts_cache degraded。
```

当前允许记录的字段：

```text
request_id
method / path / status_code / elapsed_ms
provider / model / task_type
fallback_used / policy_blocked / cache_hit
voice_version / emotion / audio_bytes / text_chars
child_id_hash / session_id_hash
cache_key_prefix
error_type
```

当前禁止记录的字段：

```text
完整 child text
完整 prompt
完整 parent_message_raw
完整图片描述或原始照片路径
完整 TTS text
完整 reply text
API key / Authorization / token / secret
完整 audioUrl query 参数或未来签名 URL
原始音频内容或真实儿童身份信息
```

QA 使用方式：

```text
1. Android 或 curl 传入 `X-Request-ID` 后，可在响应头和后端 JSON 日志中使用同一 request_id 关联。
2. 如果 Android 未传入，后端会生成 `req_<uuid>` 并写回响应头。
3. 本地排查慢请求时，先看 `request_finished.elapsed_ms`，再用同一 request_id 查 `model_call_finished.elapsed_ms` 和 `tts_call_finished.elapsed_ms`。
4. `GET /api/v1/health/detail` 用于区分进程存活、PostgreSQL、TTS cache、voice sample 和 MiMo TTS 配置问题；普通 `/health` 仍保持轻量 ok。
5. Streaming v1 后端将复用 request_id 和 provider timing，并新增 `first_text_ms`、`first_audio_ms`、`stream_total_ms`。
```

### Phase 2：Android 和 QA 诊断

修改范围建议：

```text
android/app/src/main/java/com/childai/companion/data/
android/app/src/main/java/com/childai/companion/ui/chat/
android/app/src/main/java/com/childai/companion/voice/
docs/MANUAL_QA_V0_1.md 或独立 QA 模板
```

实现：

```text
1. Android 生成 `X-Request-ID` 并记录到 Dev diagnostics。
2. ConversationApiException 分类 timeout/http/parse/network。
3. remote audio 记录 first_audio_ms，但不打印完整 URL。
4. QA 模板增加 request_id 和 latency 字段。
```

测试：

```text
1. Android unit tests 覆盖 request_id header、HTTP status、timeout 分类。
2. TTS tests 覆盖 first_audio_ms 或 remote pending/play/error transitions。
3. `bash scripts/android_gradle.sh test`。
```

### Phase 3：保留和清理

修改范围建议：

```text
scripts/
backend/app/services/tts_cache_service.py
docs/
```

实现：

```text
1. `scripts/cleanup_local_runtime_data.sh --dry-run`。
2. 清理 logs/qa、backend logs、TTS cache。
3. 输出只包含文件数量、字节数和 cache_key prefix。
4. 文档明确本地保留窗口。
```

---

## 11. 不建议现在做

```text
1. 不接 Sentry、Datadog、OpenTelemetry Collector 或外部日志平台。
2. 不把完整 conversation request/response body 写入日志。
3. 不把真实 MiMo key 写入 `.env.example`、文档、测试或 Android。
4. 不在 Android 端保存模型 key 或直接调用 MiMo。
5. 不为 v0.1 建复杂账号体系或生产级权限系统。
6. 不为 health detail 暴露公网或儿童界面入口。
```

---

## 12. 验收标准

首批 P0 完成后，至少应满足：

```text
1. 任一 Android 报错都能拿到 request_id，并在后端日志中找到同一 request_id。
2. `POST /api/v1/conversation/message` 能区分 HTTP 总耗时、LLM 耗时、TTS 耗时和 cache hit。
3. `GET /api/v1/health` 继续返回简单 ok。
4. `GET /api/v1/health/detail` 能看出 postgres、tts_cache、voice sample、mimo config 状态。
5. 日志中不含真实 API key、Authorization、完整儿童原文、完整回复文本、原始音频、原始照片。
6. `scripts/dev_backend.sh` 可以把本地运行日志稳定落到 ignored `logs/`。
7. QA 报告能记录 request_id、elapsed_ms、provider latency 和 error_category。
```
