# AGENTS.md

本文件是 Codex 在本仓库工作时必须遵守的项目级指令。

---

## 1. 项目使命

本项目是一个面向 8 岁儿童的 AI 成长智能体，运行在安卓平板上，由父亲配置和治理。第一版目标是搭建安全、可控、可扩展的基础框架，而不是做一个开放式儿童聊天机器人。

核心闭环：

```text
孩子统一聊天入口
  -> 时间上下文注入
  -> 安全和意图识别
  -> 动态场景编排
  -> 模型可配置调用
  -> 结构化记忆
  -> 父亲日报
```

---

## 2. 必读文档

开始任何任务前，优先阅读：

```text
docs/SYSTEM_DESIGN_V0_1.md
docs/DEVELOPMENT_BACKLOG_V0_1.md
docs/CODEX_WORKFLOW_V0_1.md
docs/CODEX_TASK_PROMPTS_V0_1.md
```

如果文档与代码冲突：

```text
1. 先指出冲突。
2. 不要擅自改变产品原则。
3. 对于小的实现偏差，可以修代码。
4. 对于架构或产品范围冲突，先给计划并等待确认。
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
7. 高风险输入要鼓励孩子告诉父母或可信成人，并触发父亲提醒。
8. 不保存不必要的儿童原始音频、照片和长篇聊天原文。
9. 不在日志、测试、fixture 中写入真实儿童身份信息。
10. 不引入广告、陌生人社交、排行榜或上瘾式机制。
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

### 4.2 模型规则

```text
1. 第一版默认使用 MockModelProvider。
2. 不在 Android 端放任何模型 API key。
3. 不在业务代码中直接绑定某家模型 SDK。
4. OpenAICompatibleProvider 或其他真实 provider 默认 disabled。
5. 所有 provider 必须支持超时、错误处理和 fallback。
6. 测试不得依赖真实外部模型调用。
```

### 4.3 Prompt 规则

```text
1. 不要写一个巨大 Prompt。
2. Prompt 分层：global system、persona、scene、parent policy、memory context、output contract。
3. 学习场景 Prompt 必须包含“不直接给答案”。
4. 安全 Prompt 必须包含“不要求孩子保密”。
5. Prompt 模板要有版本或文件名可追踪。
```

### 4.4 Android 规则

```text
1. Android 端是统一智能体入口，不是功能按钮堆叠。
2. 第一版不要做复杂动画。
3. 第一版不要做账号系统。
4. 第一版不要接真实相机和真实语音作为必需功能，可先 mock。
5. 所有 AI 决策由后端完成，Android 负责展示、输入和轻量状态。
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
cd backend
pytest
ruff check .
uvicorn app.main:app --reload
```

项目脚本，具体以 scripts/ 为准：

```bash
bash scripts/test_backend.sh
bash scripts/dev_backend.sh
bash scripts/demo_backend_scenarios.sh
```

Android 命令，具体以 android/README.md 为准：

```bash
cd android
./gradlew assembleDebug
./gradlew test
```

如果命令不存在，不要假装运行成功；应创建脚本或说明未实现。

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
```

如果发现 P0/P1 问题，先修复，不要继续扩展功能。

---

## 10. 任务执行方式

对于复杂任务，先计划再实现：

```text
1. 阅读相关文档和代码。
2. 输出计划。
3. 列出会修改的文件。
4. 列出不会修改的文件。
5. 列出测试策略。
6. 等待确认或直接按任务要求执行。
```

完成后输出：

```text
1. 修改文件列表。
2. 行为变化。
3. 测试命令和结果。
4. 未完成事项。
5. 风险点。
```

---

## 11. 不确定时的默认选择

```text
1. 安全优先于体验。
2. 可控优先于智能。
3. Mock 优先于真实外部服务。
4. 小步 PR 优先于大改。
5. 测试优先于功能堆叠。
6. 文档事实优先于猜测。
7. 询问父亲/开发者优先于擅自改变产品方向。
```
