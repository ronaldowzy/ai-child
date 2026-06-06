# AGENTS.md

本文件是 Codex 在本仓库工作时必须遵守的项目级指令。

---

## 1. 项目使命

本项目是面向 5-10 岁儿童的 AI 成长陪伴 App，面向家庭内测，优先 Android。儿童端陪伴角色是“小白狐”，由家长配置和治理。第一版目标是搭建安全、可控、可测试、可扩展的基础框架，而不是做一个开放式儿童聊天机器人。

核心闭环：

```text
儿童 voice-first 对话入口
  -> 后端 ASR / 安全 / 意图 / 场景护栏
  -> 模型回复与小白狐表现层信号
  -> 结构化记忆与健康使用观测
  -> 家长日报与现实接话建议
```

---

## 2. 必读文档

开始任何任务前，优先阅读：

```text
README.md
README.zh-CN.md
docs/项目现状与后续路线图_V0_2.md
docs/PRODUCT_DECISIONS_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
```

涉及 prompt、家长日报、儿童端文案、家长端文案或小白狐人格表达时，还必须阅读：

```text
docs/提示词与文案归属规则_V0_1.md
```

如果文档与代码冲突：

```text
1. 先指出冲突。
2. 不要擅自改变产品原则。
3. 对于小的实现偏差，可以修代码。
4. 对于架构或产品范围冲突，先给计划并等待确认。
5. confirmed/revised product decision 优先于旧 task 文档。
```

---

## 3. 儿童安全底线

任何代码、测试、文档、Prompt 都不得违反以下规则：

```text
1. 不把 AI 设计成孩子“唯一的朋友”或“最懂他的人”。
2. 不让 AI 要求孩子保密。
3. 不鼓励孩子隐瞒父母、老师或可信成人。
4. 不给孩子贴固定负面人格标签，例如胆小、不合群、懒、不聪明。
5. 不把内向视为缺陷。
6. 学习问题默认不直接给最终答案，要先引导思路。
7. 高风险输入要鼓励孩子告诉父母、老师或可信成人，并触发家长关注。
8. 不保存不必要的儿童原始音频、照片和长篇聊天原文。
9. 不在日志、测试、fixture 中写入真实儿童身份信息。
10. 不引入广告、陌生人社交、排行榜、积分、连续打卡、抽卡、宠物饥饿、FOMO 或上瘾式机制。
```

---

## 4. 架构规则

### 4.1 后端规则

```text
1. API route 只负责 HTTP 入参、出参和调用 service。
2. 业务逻辑放在 app/services/。
3. 外部能力适配放在 app/providers/。
4. 数据访问放在 app/repositories/。
5. Pydantic schema 放在 app/domain/ 或 app/domain/schemas/。
6. 模型调用必须通过 ModelRegistry。
7. Prompt 组装必须通过 PromptManager。
8. 安全分类必须通过 SafetyEngine。
9. 意图识别必须通过 IntentClassifier。
10. 场景选择必须通过 SceneOrchestrator。
```

### 4.2 模型 / 语音规则

```text
1. 当前测试阶段已开发的真实 provider / 本地 provider 必须在对应测试环境中启用并验证。
2. 不在 Android 端放任何模型 API key。
3. 不在业务代码中直接绑定某家模型 SDK。
4. 真实 provider 只能由后端通过受控配置、数据策略和临时测试环境调用；不能因为未启用配置而把已开发功能写成完成。
5. 所有 provider 必须支持超时、错误处理和 fallback。
6. 单元测试可使用 mock/fake 替身，但功能验收必须区分真实链路 PASS、真实执行 FAIL、外部条件 BLOCKED。
7. ASR v1 当前第一选择是后端本地 sherpa-onnx + SenseVoice-Small int8；MiMo ASR 仅作受控 fallback。
8. 儿童默认 voice-first：ASR 成功且 transcript 非空后自动发送；confirm-before-send 仅保留为 DevSettings / 家长调试模式。
9. 小白狐正式音色路径是后端 MiMo VoiceClone audio_url；Android 系统 TTS 不得作为正式小白狐自动 fallback。
```

### 4.3 Prompt 规则

```text
1. 不要写一个巨大 Prompt。
2. Prompt 分层：global system、persona、scene、parent policy、memory context、output contract。
3. 学习场景 Prompt 必须包含“不直接给答案”。
4. 安全 Prompt 必须包含“不要求孩子保密”。
5. Prompt 模板要有版本或文件名可追踪。
6. 产品敏感文案由主控会话设计或明确批准；代码执行会话只负责实现和测试。
```

### 4.4 Android 规则

```text
1. Android 端是统一智能体入口，不是功能按钮堆叠。
2. 第一版不要引入重型实时 3D 引擎或复杂动画依赖。
3. 已开发的真实语音、图片或模型能力进入测试范围后，Android/后端配置必须与目标链路一致；mock/fake 只能作为异常兜底或自动测试替身。
4. 所有 AI 决策由后端完成，Android 负责展示、输入和轻量状态。
5. 儿童端默认隐藏文字输入框、发送按钮和可编辑 ASR 确认面板；保留重说、取消、停止朗读、静音等大按钮。
6. 家长入口必须有访问保护，不能让儿童轻易进入家长设置和日报。
```

---

## 5. 推荐仓库结构

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
  README.md
docs/
scripts/
.github/
```

不要在根目录散放大量脚本或业务文件。

---

## 6. 开发命令

后端命令，具体以 backend/README.md 为准：

```bash
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
bash scripts/start_backend_services.sh --agent main --port 8000
bash scripts/status_backend_services.sh
bash scripts/stop_backend_services.sh --agent main
```

项目脚本，具体以 scripts/ 为准：

```bash
bash scripts/doctor_local_env.sh
bash scripts/test_backend.sh
bash scripts/start_backend_services.sh --agent main --port 8000
bash scripts/status_backend_services.sh
bash scripts/stop_backend_services.sh --agent main
bash scripts/demo_backend_scenarios.sh
```

多 agent 协作时，任何 agent 不得手写 `uvicorn`、`nohup`、`launchctl` 或直接 kill 共享服务。后台服务启停必须统一使用 `start_backend_services.sh` / `status_backend_services.sh` / `stop_backend_services.sh`，并通过 `--agent <name>` 和不同 `--port` 隔离各 Lane；默认只停止自己的 FastAPI 进程，不停止共享 PostgreSQL。

Android 命令，具体以 android/README.md 为准：

```bash
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh lintDebug
```

如果裸命令失败，不要立即报告机器缺少依赖；先查 `docs/session_process/SHARED_CONTEXT_V0_1.md` 并使用标准脚本复跑。如果标准脚本也失败，不要假装运行成功；应说明真实阻塞。

---

## 7. 测试要求

### 7.1 后端

每个后端功能 PR 至少满足：

```text
1. 新增或更新 pytest。
2. 相关测试通过。
3. 不依赖真实外部网络调用。
4. 高风险安全逻辑必须有测试。
5. API schema 改动必须有 API 测试。
```

### 7.2 Android

每个 Android PR 至少满足：

```text
1. 可以编译。
2. 关键 UI 状态可手动验证。
3. API client mapping 有测试或清晰验证步骤。
```

---

## 8. PR 要求

每个 PR 最后必须说明：

```text
Summary:
- 做了什么。

Tests:
- 运行了哪些测试，结果如何。

Safety:
- 是否涉及儿童数据、安全策略、学习答案策略。

Docs:
- 是否更新了文档。

Known issues:
- 未完成事项或风险。
```

禁止合并：

```text
1. 测试失败但未说明。
2. 引入真实 secret。
3. 绕过核心架构服务。
4. 改变儿童安全原则。
5. 未经确认新增生产依赖。
6. 把 mock/fake 路径写成真实能力通过。
```

---

## 9. Review guidelines

审查时重点看：

```text
1. 是否直接给作业答案。
2. 是否诱导孩子长时间聊天。
3. 是否制造秘密关系或过度拟人依赖。
4. 是否保存过多儿童原始数据。
5. 是否把安全逻辑放在模型调用之后才处理。
6. 是否绕过 ModelRegistry、PromptManager、SafetyEngine、SceneOrchestrator。
7. 是否缺少测试。
8. 是否过度工程化。
9. 是否擅自改写 prompt、家长日报或产品文案。
10. 是否与 PRODUCT_DECISIONS confirmed/revised 决策冲突。
```

如果发现 P0/P1 问题，先修复，不要继续扩展功能。

---

## 10. 任务执行方式

对于复杂任务，先计划再实现：

```text
1. 阅读相关文档和代码。
2. 阅读共享上下文并运行 `bash scripts/doctor_local_env.sh`。
3. 输出计划。
4. 列出会修改的文件。
5. 列出不会修改的文件。
6. 列出测试策略。
7. 等待确认或直接按任务要求执行。
```

完成后输出：

```text
1. 修改文件列表。
2. 行为变化。
3. 测试命令和结果。
4. 未完成事项。
5. 风险点。
6. 是否发现需要写入共享上下文的新共性坑。
```

---

## 11. Product Decision Sync

```text
1. 家长/产品负责人确认的新想法、方案调整、边界原则，必须写入 docs/PRODUCT_DECISIONS_V0_1.md。
2. 涉及语音、小白狐形象、儿童安全、模型外发、记忆、家长治理的决策，不允许只存在对话中。
3. 子会话开始前必须检查 PRODUCT_DECISIONS 是否有影响本任务的新决策。
4. 子会话完成后如果发现新的产品事实或限制，必须建议主会话更新 PRODUCT_DECISIONS 或对应设计文档。
5. 代码实现不得与 confirmed/revised decision 冲突；如冲突，先报告，不要擅自改产品方向。
6. UI、产品、设计和测试说明统一使用正式名称“小白狐”；代码 class 名 FoxAgent 暂可保留，后续重命名必须单独 refactor。
```

---

## 12. 不确定时的默认选择

```text
1. 安全优先于体验。
2. 可控优先于智能。
3. 当前测试阶段真实可用优先；已开发功能必须开启验证，mock/兜底不能替代验收。
4. 小步 PR 优先于大改。
5. 测试优先于功能堆叠。
6. 文档事实优先于猜测。
7. confirmed/revised 产品决策优先于旧 task 文档。
8. 询问家长/产品负责人优先于擅自改变产品方向。
```
