# 儿童 AI 成长陪伴 App：ai-child

`ai-child` is an open-source reference implementation for a child-safe AI
companion app: Android client, FastAPI backend, local-first ASR, backend-only
model/TTS/vision provider calls, parent controls, and safety guardrails.

`ai-child` 是面向 5-10 岁儿童的 AI 成长陪伴 App，面向家庭内测，优先 Android。当前角色形象为“小白狐”。

产品目标不是做开放式儿童聊天机器人，而是提供一个由家长配置和治理的、安全、可控、可逐步扩展的儿童 AI 陪伴入口。

核心闭环：

```text
儿童 voice-first 对话入口
  -> 后端 ASR / 安全 / 意图 / 场景护栏
  -> 模型回复与小白狐表现层信号
  -> 结构化记忆与健康使用观测
  -> 家长日报与现实接话建议
```

---

## 1. 当前状态

当前项目已经从第一轮后端和 Android MVP，推进到家庭内测前体验加固阶段，并已完成五轮孩子可感知体验收尾。

当前下一阶段产品主方向为：

```text
小白狐连续陪伴与亲近感收敛
```

下一阶段不是继续开笼统的“第六轮体验大改”，而是围绕连续陪伴、主动回应、常驻轻共创、等待感优化和 App 界面重设计，形成孩子能直接感受到的陪伴体验。

当前主线能力：

```text
1. 默认 conversation.open 的 freedom-first 对话底座。
2. Android 儿童端 voice-first：点击录音、后端 ASR、成功后自动发送。
3. 后端本地 SenseVoice ASR 优先，MiMo ASR 仅作受控 fallback。
4. 后端 MiMo VoiceClone 生成小白狐 audio_url，Android 播放远程音频。
5. Streaming v1：渐进文字 + segment interleaved TTS + Android audio queue。
6. “拍给小白狐看”：系统相机/相册真实 multipart 上传 + 后端 vision/image context。
7. 小白狐状态图、phase reducer、视觉状态 resolver 与轻量防闪烁逻辑。
8. 家庭内测账号薄片：一个孩子一个账号，由家长代创建和管理。
9. 家长日报 model-first，并已进入 narrative v3：自然段落 + 今晚怎么聊 + 避免追问。
10. 家庭内测运行门禁：正式功能不得用 mock provider / mock 图片 / mock 语音冒充成功。
```

仍需重点验证：

```text
1. Redmi K60 / Honor Pad 5 完整设备 QA。
2. 真实儿童语音、噪音环境下的 ASR 准确率和延迟。
3. MiMo VoiceClone 首音频延迟和失败态。
4. 图片上传、vision 续聊、Android timeout 和本地预览。
5. stream / TTS segment queue / 停止 / 静音 / 迟到 opening 的真实表现。
6. 家长日报 v3 真实素材下的自然度和无监控感。
7. 连续陪伴、主动回应、常驻轻共创和界面重设计是否真正提升孩子亲近感。
```

---

## 2. 当前测试阶段最高原则

已经开发并进入当前测试范围的真实能力，必须在本地或真机测试环境中实际启用和验证。

执行规则：

```text
1. 不得以“安全默认值”为理由关闭或跳过当前要验收的真实能力。
2. 已开发但当前环境不能使用的功能，必须标记为 FAIL 或 BLOCKED，不能写成 done。
3. mock / fake / fallback 只能用于自动化测试或异常保护，不能冒充家庭内测成功路径。
4. 测试前必须确认后端和 Android 配置与本轮目标一致。
5. 儿童安全护栏仍必须工作，但不能用安全护栏替代真实链路验收。
```

---

## 3. 文档入口

公开仓库优先阅读：

```text
docs/SAFETY_AND_PRIVACY.md
docs/ARCHITECTURE.md
docs/ROADMAP.md
docs/PUBLIC_RELEASE_CHECKLIST.md
CONTRIBUTING.md
SECURITY.md
```

新会话或代码执行会话优先阅读：

```text
AGENTS.md
README.md
README.zh-CN.md

docs/下一阶段产品进化计划_V0_1.md
docs/项目现状与后续路线图_V0_2.md
docs/PRODUCT_DECISIONS_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
```

下一阶段产品规划、协作机制和执行顺序以以下文件为准：

```text
docs/下一阶段产品进化计划_V0_1.md
```

长期设计文档按需阅读：

```text
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/LOCAL_ASR_SENSEVOICE_DESIGN_V0_1.md
docs/ASR_INPUT_RESEARCH_V0_1.md
docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md
```

提示词、家长日报和产品文案相关任务还必须阅读：

```text
docs/提示词与文案归属规则_V0_1.md
```

说明：历史英文 task 文档只作为 git 历史参考，不再作为当前规划入口。

---

## 4. 安全原则摘要

```text
1. 不把 AI 设计成孩子唯一的朋友或最懂孩子的人。
2. 不要求孩子保密，不鼓励隐瞒父母、老师或可信成人。
3. 学习求助默认引导思路，不直接给最终答案。
4. 高风险输入要鼓励孩子告诉父母、老师或可信成人，并触发家长关注。
5. 不保存不必要的儿童原始音频、照片和长篇聊天原文。
6. 不在 Android 端放模型 API key。
7. 不引入广告、陌生人社交、排行榜、积分、连续打卡、抽卡、宠物饥饿或 FOMO。
```

完整规则以 `AGENTS.md`、`docs/PRODUCT_DECISIONS_V0_1.md` 和 `docs/下一阶段产品进化计划_V0_1.md` 为准。

公开仓库不应包含真实儿童身份信息、真实家庭 Prompt、原始音频/照片、私有截图、API key、`.env`、本地数据库、模型权重或生成的 TTS cache。公开前检查见
`docs/PUBLIC_RELEASE_CHECKLIST.md`。

---

## 5. 仓库结构

```text
backend/
  app/
    api/
    core/
    db/
    domain/
    providers/
    repositories/
    services/
    tests/
android/
  app/
docs/
scripts/
.github/
```

---

## 6. 本地命令入口

本机已配置 `child-ai` conda 环境、JDK 17 和 Android SDK。部分非交互 shell 可能没有继承 `PATH`、`JAVA_HOME` 或 `ANDROID_HOME`，因此裸命令失败不能直接判定机器缺少依赖；先使用根目录标准脚本复跑。

环境检查：

```bash
bash scripts/doctor_local_env.sh
```

后端：

```bash
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
bash scripts/dev_backend.sh
bash scripts/demo_backend_scenarios.sh
bash scripts/e2e_local_api_check.sh
```

后台服务：

```bash
bash scripts/start_backend_services.sh --agent main --host 0.0.0.0 --port 8000
bash scripts/status_backend_services.sh
bash scripts/stop_backend_services.sh --agent main
```

Android：

```bash
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh lintDebug
bash scripts/build_device_debug_apk.sh --base-url http://192.168.0.118:8000/
bash scripts/install_android_debug.sh
```

生产部署与 APK 发版：

```bash
bash scripts/bump_app_version.sh --bump patch --content "本次更新内容"
bash scripts/build_release_apk.sh --base-url http://ihealth.znitech.com:22026/ --publish-to-backend-storage
bash scripts/build_backend_deploy_package.sh --include-apk
```

生产环境部署说明见：

```text
deploy/centos7/README.md
```

后端细节以 `backend/README.md` 为准。Android 细节以 `android/README.md` 为准。多会话环境事实和已知坑以 `docs/session_process/SHARED_CONTEXT_V0_1.md` 为准。
