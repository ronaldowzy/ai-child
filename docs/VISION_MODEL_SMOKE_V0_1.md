# Vision Model Smoke v0.1

用途：记录本项目在不接 CameraX、不外发真实儿童图片的前提下，验证 OpenAI-compatible MiMo vision / OCR 请求链路的最小方案。

## Scope

```text
已实现：
1. ModelRequest 支持 text + image data URI 的多模态 payload。
2. OpenAICompatibleProvider 在 metadata/context 中存在 image_data_uri 时构造 OpenAI-compatible image_url content array。
3. AttachmentCreateRequest 支持可选 image_data_uri，并限制为 png/jpeg/webp data URI，解码后最大 5MB。
4. AttachmentService 在真实 vision QA 中必须进入 ModelRegistry vision path；只有测试替身或异常兜底才使用 MockOCRProvider。
5. ModelDataPolicyGuard 要求 image 外发必须 CHILD_AI_MIMO_ALLOW_IMAGE=true 且 CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=true。
6. scripts/smoke_vision_model_opt_in.sh 提供真实 MiMo vision opt-in smoke。
7. 2026-05-22 真实 smoke 已确认：MiMo image understanding 必须使用 `mimo-v2.5` / `mimo-v2-omni` 这类 multimodal model；`mimo-v2.5-pro` 会触发 `No endpoints found that support image input`。
8. MiMo OpenAI-compatible chat completions 对 MiMo provider 使用 `max_completion_tokens`；不要用 `max_tokens` 作为 MiMo vision 请求参数。
```

```text
未实现：
1. CameraX / 真相机接入。
2. 图片长期存储。
3. true LLM streaming。
4. 上架级儿童图片合规流程。
```

## Env Gate

真实 MiMo vision smoke 只有以下条件全部满足才运行：

```bash
CHILD_AI_VISION_PROVIDER=mimo
CHILD_AI_MIMO_ENABLED=true
CHILD_AI_MIMO_ALLOW_IMAGE=true
CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=true
CHILD_AI_MIMO_VISION_MODEL=mimo-v2.5
CHILD_AI_MIMO_API_KEY=<shell env only>
CHILD_AI_VISION_SMOKE_IMAGE=/path/to/fake-smoke-test-image.png
```

图片文件名必须包含 `fake`、`smoke`、`test`、`fixture` 或 `sample` 之一，且不得是真实儿童照片或真实家庭照片。

## Output Boundary

脚本只输出：

```text
VISION_STATUS
provider
model
recognized_type
text_length
```

禁止输出：

```text
API key
image base64
完整图片描述
provider raw response
真实儿童或家庭身份信息
```

## Verified Smoke

```text
2026-05-22:
  result: PASS
  provider: mimo
  model: mimo-v2.5
  input: generated fake/test PNG data URI
  latest_observed_recognized_type: privacy_sensitive
  latest_observed_text_length: 176
  printed text: length only, no full image description
  note: recognized_type may vary with the generated fake image; this smoke validates real provider routing and redaction, not classification quality.
```

关键修正：

```text
1. OpenAICompatibleProvider 现在优先使用 ModelProfile.model_name，避免全局 CHILD_AI_MIMO_MODEL=mimo-v2.5-pro 覆盖 vision profile。
2. vision / ocr profile 默认模型改为 mimo-v2.5。
3. MiMo provider payload 使用 max_completion_tokens。
4. smoke 脚本默认临时设置 CHILD_AI_MIMO_VISION_MODEL=mimo-v2.5。
```

## Attachment Boundary

`/api/v1/conversation/attachment` 可以接收 `image_data_uri` 用于当次识别，但运行时记录只保存 `has_image_data_uri=true` 和 `image_data_uri_stored=false` 等非敏感 metadata，不保存 raw image、base64、OCR debug 或 provider raw response。

对疑似作业图，vision path 只提取题目内容和要求，不直接给最终答案。对疑似地址、电话、证件、学校名、人脸等内容，识别结果应进入 privacy boundary。
