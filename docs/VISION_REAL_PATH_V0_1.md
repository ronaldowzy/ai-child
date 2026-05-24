# Vision Real Path v0.1

Status: implemented for active QA path; backend real MiMo upload smoke passed with a non-child synthetic image; real device QA still required.

## Scope

This document defines the current “拍给小白狐看” path for family testing.

```text
Android system camera / system photo picker
  -> multipart upload to backend
  -> backend short-term image attachment record
  -> MiMo vision / multimodal understanding
  -> controlled image_context injected into child_chat
  -> child_chat generates 小白狐 reply
```

CameraX and custom camera UI are not part of this slice.

## Product Rules

1. “拍给小白狐看” must use a real picture URI from the Android system camera or system picker.
2. Android must not create a fake attachment id for the child-facing default path.
3. Android must not store MiMo API keys or call MiMo directly.
4. Backend image upload must reject unsupported MIME types and oversized images.
5. Backend may store the uploaded image only as a short-term local test artifact for attachment lookup.
6. Raw image bytes, base64 image data, and provider raw responses must not be logged, stored in model debug traces, or committed.
7. Missing key, missing `allow_image`, provider HTTP failure, or network failure must be reported as BLOCKED/FAIL, not as a successful vision result.
8. Unit tests may use test doubles, but QA evidence must distinguish test-double behavior from real provider behavior.
9. Once `image_context` is available, child-facing replies must not say “小白狐看不到图片 / 没有看图功能”. If the model produces that refusal anyway, runtime repairs it into a short answer based on the controlled image context or asks for a clearer image.

## Model Routing

```text
Pure text child_chat:
  profile: mimo_child_chat
  model: CHILD_AI_MIMO_MODEL or mimo-v2.5-pro

Image / vision / OCR / multimodal:
  profile: mimo_vision or mimo_ocr
  model: CHILD_AI_MIMO_VISION_MODEL or mimo-v2.5

Opening greeting:
  deterministic policy/template default

ParentReport:
  model-first via ModelTaskType.PARENT_REPORT; deterministic fallback is not formal success

ASR:
  local_sensevoice first, MiMo ASR fallback

TTS:
  MiMo VoiceClone first, system TTS fallback/diagnostic only
```

Do not switch ordinary text conversation from `mimo-v2.5-pro` to `mimo-v2.5` just because vision exists.

## Backend API

### `POST /api/v1/attachments/images`

Request: `multipart/form-data`

```text
child_id: string
session_id: string
image_purpose: share | ask_what_is_this | tell_story | learning_homework | ...
child_caption: optional string
file: image/jpeg | image/png | image/webp
```

Response includes:

```text
attachment_id
recognized_content
reply
ui_actions
session_state
mime_type
size_bytes
created_at
```

The endpoint builds an in-memory/short-term attachment record and returns an `attachment_id`. Conversation requests can then include that id in `input.attachments`.

## Android Flow

1. Child taps “拍给小白狐看”.
2. App offers “拍照” and “从相册选”.
3. “拍照” uses `ActivityResultContracts.TakePicture` with a `FileProvider` URI.
4. The app prepares a compressed JPEG payload and uploads it with multipart form data.
5. Upload success stores the returned `attachment_id` as pending image context.
6. Follow-up actions such as “聊聊它 / 编个故事 / 问这是什么” send the attachment id to conversation.

The old text-entry attachment demo is not the child-facing default path.
If the child says “拍照给你看” before an image is attached, the reply should guide them to the “拍给小白狐看” entry instead of saying the app cannot see images.

## Real-Path Dev Backend

Use a temporary shell overlay. Do not write keys into git or Android.

```bash
CHILD_AI_MIMO_API_KEY=... bash scripts/run_real_path_dev_backend.sh
```

The script sets the intended QA defaults:

```text
CHILD_AI_MODEL_PROVIDER=mimo
CHILD_AI_CHILD_CHAT_PROFILE=mimo_child_chat
CHILD_AI_MIMO_MODEL=mimo-v2.5-pro
CHILD_AI_VISION_PROVIDER=mimo
CHILD_AI_VISION_PROFILE=mimo_vision
CHILD_AI_MIMO_VISION_MODEL=mimo-v2.5
CHILD_AI_MIMO_ENABLED=true
CHILD_AI_MIMO_ALLOW_CHILD_DATA=true
CHILD_AI_MIMO_ALLOW_IMAGE=true
CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=true
CHILD_AI_ASR_PROVIDER=local_sensevoice
CHILD_AI_LOCAL_SENSEVOICE_ENABLED=true
CHILD_AI_TTS_PROVIDER=mimo
CHILD_AI_MIMO_TTS_ENABLED=true
```

`model_debug_traces` is enabled by default in the current testing backend; no
trace enable switch is needed.

## QA Status

Implemented:

- Backend real image multipart upload endpoint.
- Android system camera / picker upload path.
- Backend MiMo vision path for real uploads.
- Attachment id continuation into conversation context.
- Model routing separation between `mimo-v2.5-pro` text chat and `mimo-v2.5` vision.
- Backend smoke on 2026-05-23:
  - `POST /api/v1/attachments/images`: PASS with `provider=mimo`, `model=mimo-v2.5` from timing logs, non-child synthetic PNG.
  - follow-up `POST /api/v1/conversation/message` with returned `attachment_id`: PASS with child_chat `model=mimo-v2.5-pro` from timing logs.

Still required:

- Redmi K60 real device QA.
- Honor Pad 5 compatibility/performance QA.
- Verification that failures show BLOCKED/FAIL instead of pretending the image was understood.

Not in scope:

- CameraX custom camera.
- Long-term image storage.
- Android-side model calls or keys.
- Real child photo fixtures.
