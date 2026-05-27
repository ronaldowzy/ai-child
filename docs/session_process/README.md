# 多会话协作总则 v0.2

用途：定义本项目如何拆分主控会话和执行会话，避免多个会话互相覆盖、重复设计或越权改变儿童安全原则。

本目录只管理协作流程，不替代 `AGENTS.md`、`README.md`、`docs/项目现状与后续路线图_V0_2.md` 和 `docs/PRODUCT_DECISIONS_V0_1.md`。

---

## 0. 子会话启动前必须做

所有执行会话启动前必须阅读：

```text
AGENTS.md
README.md
docs/项目现状与后续路线图_V0_2.md
docs/PRODUCT_DECISIONS_V0_1.md
docs/session_process/SHARED_CONTEXT_V0_1.md
```

并先运行：

```bash
bash scripts/doctor_local_env.sh
```

规则：

```text
1. 不要只根据裸命令失败就判断本机缺少依赖。
2. 后端验证优先使用 scripts/test_backend.sh、scripts/lint_backend.sh。
3. 后台服务启停必须使用 scripts/start_backend_services.sh、scripts/status_backend_services.sh、scripts/stop_backend_services.sh。
4. Android 验证优先使用 scripts/android_gradle.sh，而不是裸 ./gradlew。
5. 遇到 JDK、Conda、Android SDK、设备、局域网 IP、base URL 等问题，先查 SHARED_CONTEXT_V0_1.md。
6. 新发现的共性坑必须在交接摘要里提出，由主控会话确认后写入共享上下文。
```

---

## 1. 会话角色

### 1.1 主控会话：项目总控与架构治理

职责：

```text
1. 维护当前开发计划和后续路线图。
2. 拆分任务、定义边界、依赖顺序和验收标准。
3. 审查执行会话产出是否违反 AGENTS.md 和 PRODUCT_DECISIONS。
4. 汇总测试结果、阻塞事项和下一步任务。
5. 处理跨模块接口变化。
6. 决定何时进入下一个阶段。
7. 维护文档事实源，删除过期过程文档。
```

主控会话可以修改：

```text
README.md
AGENTS.md
docs/项目现状与后续路线图_V0_2.md
docs/PRODUCT_DECISIONS_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/
scripts/
跨模块接口文档
```

主控会话默认不直接做大块功能实现，除非任务很小或需要修复 P0/P1 问题。

### 1.2 执行会话：模块实现或专项修复

执行会话负责一个清晰模块或专项任务。每个执行会话必须：

```text
1. 先阅读 AGENTS.md、README、当前路线图、PRODUCT_DECISIONS 和任务指定文档。
2. 先输出计划。
3. 列出会修改和不会修改的文件。
4. 等待确认或按提示明确授权后实现。
5. 添加或更新测试。
6. 运行相关测试。
7. 输出交接摘要。
8. 报告是否发现新的共性坑。
```

---

## 2. 当前阶段任务划分

早期 S00-S14 会话编号已经完成历史使命，不再作为当前执行顺序。

当前阶段按产品方向拆分执行会话：

| 会话类型 | 主要范围 | 默认拥有文件 | 备注 |
|---|---|---|---|
| 家长日报 v3 验收 / 修复 | ParentReportService、日报测试、家长日报 UI 文案 | `backend/app/services/parent_report_service.py`、相关 tests、必要 docs | 不得恢复拼接式日报 |
| Voice-first polish | Android 录音/ASR/TTS 状态、后端 ASR 错误态 | `android/` voice/chat 相关文件、`backend/app/services/asr*` | confirm-before-send 只保留调试模式 |
| TTS / streaming latency | 后端 TTS、stream、Android audio queue、timing | stream/TTS 服务、Android player、timing tests | 没有 request_id + logcat + 时间点证据，不做猜测修复 |
| 图片分享 v2 | 系统相机/相册、图片上下文、vision 续聊 | attachment、vision、Android 图片入口 | “拍给小白狐看”是默认，不默认作业 |
| Relationship Memory v2 | 记忆召回、频率限制、家长/儿童使用分离 | memory services、relationship memory tests | 禁止依赖钩子 |
| Conversation Arc v2 | 对话阶段、停止/转话题、收尾 | runtime、prompt、trace tests | 不强拉长会话 |
| Healthy Engagement metrics | 非原文指标、QA、边界观测 | healthy engagement、logging、QA docs | 不保存 raw transcript |
| Parent governance | auth、session、retention、delete controls | auth/session/parent settings | multi-child 后置 |
| 文档治理 | README、AGENTS、路线图、决策、进度板 | docs、README、AGENTS | 删除过期过程文档，中文入口优先 |

---

## 3. 文件所有权规则

同一时间只允许一个执行会话拥有某个模块的主要写入权。

```text
backend/app/api/              当前 API 任务会话拥有
backend/app/domain/           当前 schema/枚举任务会话拥有
backend/app/services/         当前业务服务任务会话拥有
backend/app/providers/        provider 任务会话拥有
backend/app/repositories/     数据访问任务会话拥有
backend/app/tests/            对应功能会话同步维护
android/                      Android 会话拥有
docs/session_process/         主控会话拥有
README.md / AGENTS.md         主控会话拥有
```

如果执行会话必须改不属于自己的文件，应先在计划里说明原因。

---

## 4. 禁止事项

```text
1. 不得擅自改变儿童安全原则。
2. 不得引入真实模型调用作为自动化测试默认行为。
3. 不得把业务逻辑写进 API route。
4. 不得删除其他会话新增的测试来让自己通过。
5. 不得在未说明的情况下跨模块大改。
6. 不得写入真实儿童身份信息、真实照片、真实音频或真实 secret。
7. 不得让代码执行会话自行设计 prompt、家长日报或儿童/家长端产品文案。
8. 不得把 mock/fake 路径写成家庭内测真实能力通过。
```

---

## 5. 交接机制

每个执行会话完成后，必须给主控会话交接：

```text
1. 修改文件列表。
2. 行为变化。
3. 测试命令和结果。
4. 安全影响。
5. 文档更新。
6. 未完成事项。
7. 下一个会话需要知道的接口或约束。
8. 共享上下文是否需要更新。
```

主控会话收到交接后：

```text
1. 检查是否符合 AGENTS.md。
2. 检查是否越过任务边界。
3. 更新进度板或当前路线图。
4. 决定是否需要修复会话。
5. 给出下一个执行会话启动提示词。
```

---

## 6. 本机环境规则

当前开发机是 Mac mini，本机运行后端服务。Python 环境统一使用：

```bash
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
```

后台服务统一使用：

```bash
bash scripts/start_backend_services.sh --agent main --port 8000
bash scripts/status_backend_services.sh
bash scripts/stop_backend_services.sh --agent main
```

多 agent 并行时必须给每个 Lane 分配独立 `--agent` 和 `--port`；不要手写 `uvicorn`、`nohup`、`launchctl` 或直接 kill 其他 agent 的服务。

Android 环境统一使用：

```bash
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh lintDebug
```

如果命令不存在或失败，执行会话必须如实报告，不能假装通过；但报告阻塞前必须先尝试共享上下文里的标准入口。

---

## 7. 当前推荐执行顺序

```text
1. 完成文档事实源收口：中文入口、删除过期 task 文档、修正 README / AGENTS / 协作流程。
2. 验收 Parent Report v3：普通、图片、学习、安全、素材少、模型失败场景。
3. 生成并安装下一版 QA APK。
4. Redmi K60 / Honor Pad 5 跑家庭内测主链路。
5. 基于 request_id + Android logcat + 手工时间点修复 voice / TTS / stream latency。
6. 新建 Voice-first conversation polish 执行任务。
7. 再进入 Relationship Memory v2、Conversation Arc v2、Healthy Engagement metrics。
```
