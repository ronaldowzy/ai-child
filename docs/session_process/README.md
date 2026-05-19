# Codex 多会话协作总则 v0.1

用途：定义本项目在 Codex 中如何拆分主会话和子会话，避免多个会话互相覆盖、重复设计或越权改变儿童安全原则。

本目录只管理协作流程，不替代 `AGENTS.md`、系统设计文档和 Backlog。所有子会话都必须服从根目录 `AGENTS.md`。

---

## 0. 共享上下文和已知坑

所有子会话启动前必须阅读：

```text
docs/session_process/SHARED_CONTEXT_V0_1.md
```

并先运行：

```bash
bash scripts/doctor_local_env.sh
```

规则：

```text
1. 不要只根据裸命令失败就判断本机缺少依赖。
2. 后端验证优先使用 scripts/test_backend.sh、scripts/lint_backend.sh、scripts/dev_backend.sh。
3. Android 验证优先使用 scripts/android_gradle.sh，而不是直接运行裸 ./gradlew。
4. 遇到 JDK、Conda、Android SDK、设备、局域网 IP、base URL 等问题，先查 SHARED_CONTEXT_V0_1.md。
5. 新发现的共性坑必须在交接摘要里提出，由主控会话确认后写入共享上下文。
```

当前已知重点：

```text
JDK 17 已安装，但部分非交互 shell 可能没有继承 JAVA_HOME。
Android SDK 已安装，但设备/模拟器是否连接需要每次联调时现场确认。
Conda 已安装在 /opt/homebrew/bin/conda，但部分 shell 的 PATH 可能找不到 conda。
```

---

## 1. 会话角色

### 1.1 主控会话：项目总控 / 架构治理

中文标识：

```text
主控会话：项目总控与架构治理
```

职责：

```text
1. 维护 v0.1 总体开发计划。
2. 拆分 Milestone 和子任务。
3. 决定任务边界、依赖顺序和验收标准。
4. 审查子会话产出是否违反 AGENTS.md。
5. 汇总测试结果、阻塞事项和下一步任务。
6. 处理跨模块接口变化。
7. 决定何时进入下一个 Milestone。
```

主控会话可以修改：

```text
docs/session_process/
docs/CODEX_PROGRESS_BOARD_V0_1.md
README.md
.gitignore
.env.example
scripts/
跨模块接口文档
```

主控会话默认不直接做大块功能实现，除非任务很小或需要修复 P0/P1 问题。

### 1.2 子会话：模块执行

子会话负责一个清晰模块或一个 Milestone 的一部分。每个子会话必须：

```text
1. 先阅读 AGENTS.md 和任务指定文档。
2. 先输出计划。
3. 列出会修改和不会修改的文件。
4. 等待确认或按提示明确授权后实现。
5. 添加或更新测试。
6. 运行相关测试。
7. 输出交接摘要。
8. 报告是否发现新的共性坑。
```

---

## 2. 子会话划分

| 会话编号 | 中文名称 | 主要目录 | 依赖 | 阶段 |
|---|---|---|---|---|
| S00 | 仓库初始化会话 | 根目录、docs、scripts | 无 | C0 |
| S01 | 后端骨架会话 | backend/app/api、domain、services、tests | S00 | M1 |
| S02 | 时间与父亲策略会话 | backend/app/services、api、domain | S01 | M2 |
| S03 | 模型注册与 Mock Provider 会话 | backend/app/providers、services | S01 | M3 |
| S04 | Prompt 管理会话 | backend/app/prompts、services | S03 | M4 |
| S05 | 安全与意图识别会话 | backend/app/services、domain、tests | S02/S03 | M5 |
| S06 | 场景编排会话 | backend/app/services、domain、repositories | S05 | M6 |
| S07 | 记忆系统会话 | backend/app/repositories、services、db | S06 | M7 |
| S08 | 父亲日报会话 | backend/app/services、api、domain | S07 | M8 |
| S09 | 附件与 Mock OCR 会话 | backend/app/api、providers、services | S06 | M9 |
| S10 | 后端质量与演示会话 | backend/app/tests、scripts | S01-S09 | Q1 |
| S11 | Android 壳会话 | android/ | S00 | A1 |
| S12 | Android API 接入会话 | android/ | Q1/S11 | A2 |
| S13 | Android 拍题与父亲页会话 | android/ | S09/S12 | A3/A4 |
| S14 | 端到端联调会话 | backend、android、docs | Q1/S13 | E2E |

---

## 3. 工作区规则

### 3.1 文件所有权

同一时间只允许一个子会话拥有某个模块的主要写入权。

```text
backend/app/api/              由当前 API 任务会话拥有
backend/app/domain/           由当前 schema/枚举任务会话拥有
backend/app/services/         由当前业务服务任务会话拥有
backend/app/providers/        由 provider 任务会话拥有
backend/app/repositories/     由数据访问任务会话拥有
backend/app/tests/            由对应功能会话同步维护
android/                      Android 会话拥有
docs/session_process/         主控会话拥有
```

如果子会话必须改不属于自己的文件，应先在计划里说明原因。

### 3.2 禁止事项

```text
1. 子会话不得擅自改变儿童安全原则。
2. 子会话不得引入真实模型调用作为默认行为。
3. 子会话不得把业务逻辑写进 API route。
4. 子会话不得删除其他会话新增的测试来让自己通过。
5. 子会话不得在未说明的情况下跨 Milestone 大改。
6. 子会话不得写入真实儿童身份信息或真实 secret。
```

---

## 4. 交接机制

每个子会话完成后，必须给主控会话交接：

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
3. 更新进度板。
4. 决定是否需要修复会话。
5. 给出下一个子会话启动提示词。
```

---

## 5. 本机环境规则

当前初期开发机是 Mac mini，本机运行后端服务。Python 环境统一使用：

```bash
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
```

如果必须手动使用 Conda：

```bash
/opt/homebrew/bin/conda run --no-capture-output -n child-ai python -m pytest
```

Android 环境统一使用：

```bash
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
```

如果命令不存在或失败，子会话必须如实报告，不能假装通过；但报告阻塞前必须先尝试共享上下文里的标准入口。

---

## 6. 推荐执行顺序

第一轮不要并行开太多子会话。推荐顺序：

```text
1. S00 仓库初始化会话
2. S01 后端骨架会话
3. S02 时间与父亲策略会话
4. S03 模型注册与 Mock Provider 会话
5. S04 Prompt 管理会话
6. S05 安全与意图识别会话
7. S06 场景编排会话
```

在 S01 到 S06 完成前，不建议启动 Android API 接入会话。Android 壳会话 S11 可以较早启动，但只能做静态 UI 和项目骨架，不应写死业务场景。
