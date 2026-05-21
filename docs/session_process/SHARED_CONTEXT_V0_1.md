# 多会话共享上下文 v0.1

用途：记录所有子会话必须共享的本机环境事实、已知坑和处理方式，避免不同会话重复踩同一个问题。

本文件由主控会话维护。子会话发现新的共性问题时，必须在交接摘要里提出，由主控会话确认后写入本文件。

---

## 1. 子会话启动前必须做

每个子会话开始执行前，先做以下检查：

```text
1. 阅读 AGENTS.md。
2. 阅读 docs/session_process/README.md。
3. 阅读本文件 docs/session_process/SHARED_CONTEXT_V0_1.md。
4. 阅读 docs/CODEX_PROGRESS_BOARD_V0_1.md，确认当前阶段和上一会话交接。
5. 运行 bash scripts/doctor_local_env.sh。
```

如果 `doctor_local_env.sh` 已经证明某个环境能力可用，子会话不得再把它报告为“当前机器缺失”。如果直接运行裸命令失败，必须先尝试本文件里的标准入口。

### 1.1 标准入口命令

后续子会话优先使用以下入口，不要先用裸命令判断环境状态：

| 场景 | 标准入口 |
|---|---|
| 环境诊断 | `bash scripts/doctor_local_env.sh` |
| 后端测试 | `bash scripts/test_backend.sh` |
| 后端 lint | `bash scripts/lint_backend.sh` |
| 后端本地服务 | `bash scripts/dev_backend.sh` |
| 后端演示 | `bash scripts/demo_backend_scenarios.sh` |
| 本地 API 合约 | `bash scripts/e2e_local_api_check.sh` |
| Android 单测 | `bash scripts/android_gradle.sh test` |
| Android 构建 | `bash scripts/android_gradle.sh assembleDebug` |
| Android lint | `bash scripts/android_gradle.sh lintDebug` |
| 启动 tablet AVD | `bash scripts/start_android_emulator.sh` |
| 安装 debug 包 | `bash scripts/install_android_debug.sh` |

当前结论：JDK 17、Android SDK、adb、`child-ai` conda 环境和 `child_ai_tablet_api35` AVD 已配置。裸 `python3`、`conda`、`./gradlew` 或 `adb` 失败，只能说明当前 shell 可能没加载环境；必须先使用上表标准入口复跑。

### 1.2 并行会话文件所有权矩阵

并行会话以主控会话最新提示词为准。默认写入权如下：

| 文件或目录 | 默认拥有者 | 规则 |
|---|---|---|
| `backend/app/services/child_agent_runtime.py`、AgentRuntime 相关 tests | S15 ChildAgentRuntime 会话 | 可接 conversation 编排，但不得绕过 SafetyEngine、PromptManager、ModelRegistry |
| `backend/app/providers/model/`、模型外发 gate 相关配置/tests | S16 模型安全闸门会话 | 真实 provider 默认 disabled；不得提交真实 API key |
| `backend/app/services/memory*`、`backend/app/repositories/memory*`、日报素材接入 tests | S17 自动记忆闭环会话 | 不保存长篇逐字原文，不把 safety 记忆混入普通检索 |
| `backend/app/services/safety_engine.py`、`scene_orchestrator.py`、安全场景 tests | S18 安全场景细分会话 | 高风险优先；不得放宽儿童安全原则 |
| `android/` 父亲入口保护相关 UI / ViewModel / tests | S19 Android 父亲入口保护会话 | 不做账号系统，不在客户端加入模型 key |
| `docs/session_process/SHARED_CONTEXT_V0_1.md`、`docs/MANUAL_QA_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`docs/session_process/SUBSESSION_PROMPTS_V0_1.md` | S26 QA 与协作机制同步会话 | 只同步 QA、环境和协作事实；不得抢写代码 worker 结果 |
| `README.md`、`docs/`、`docs/session_process/` | 主控或文档同步会话 | 只同步事实，不夸大未完成能力 |

如果必须修改不属于自己的文件，子会话必须在计划中说明原因，并在交接中标记冲突风险。发现其他会话的并行改动时，先读取 diff 并适配，不要回退。

### 1.3 Merge gate

子会话交接前必须自查：

```text
1. 只修改授权文件范围。
2. 不包含真实 secret、真实儿童身份信息、真实照片或音频。
3. 没有绕过 ModelRegistry、PromptManager、SafetyEngine、IntentClassifier、SceneOrchestrator 等核心边界。
4. 相关标准入口测试或手动验证已运行；不能运行时说明真实阻塞。
5. 文档 PR 至少运行 git diff --check，并扫描明显过期表述。
6. 并行工作中发现的共性坑必须写进交接摘要，交给主控会话决定是否更新本文件。
```

并行 worker 合并前额外检查：

```text
1. 先运行 git status --short，确认没有误碰非授权文件。
2. 修改前后都不要格式化、重排或回退其他 worker 负责的文件。
3. 如果同一文件已有他人改动，先读 diff 并只做最小补丁；不能确认时交给主控合并。
4. 文档同步会话只能写已发生事实、待验收项和协作规则，不把代码 worker 的 todo 提前写成 done。
5. 不得重复报告已解决的 JDK、conda、AVD 或模拟器中文输入问题；先引用本文件标准处理方式。
6. 完成跨模块大改且相关测试通过后，不得只停留在未提交工作区；主控会话应及时本地 commit，并在当前直接进 main 流程下推送 origin/main，除非父亲明确要求暂缓。
```

---

## 2. 当前本机环境事实

以下事实由主控会话在 2026-05-19 验证：

```text
机器：Mac mini
时区：Asia/Shanghai
后端初期运行位置：本机
最近一次局域网 IP：192.168.0.118
```

注意：局域网 IP 可能随网络变化而改变。联调前用下面命令重新确认：

```bash
bash scripts/doctor_local_env.sh
```

### Python / Conda

项目约定后端 Python 环境：

```text
conda executable: /opt/homebrew/bin/conda
conda env: child-ai
child-ai Python: 3.12.x
```

后端测试和 lint 优先使用根目录脚本，不要直接依赖裸 `python`：

```bash
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
```

如果需要显式指定：

```bash
PYTHON_BIN="/opt/homebrew/bin/conda run --no-capture-output -n child-ai python" bash scripts/test_backend.sh
```

已知坑：部分非交互 shell 没有把 `/opt/homebrew/bin` 放进 `PATH`，会导致 `conda` 看起来不存在。不要因此直接改用系统 `python3` 做后端验证；系统 `python3` 可能是 3.9.x，不满足 backend `requires-python >=3.11`。

### JDK / Android SDK

项目约定 Android 本机环境：

```text
JDK 17: /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
Android SDK: /Users/wzy/Library/Android/sdk
```

Android 命令优先使用根目录包装脚本：

```bash
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh lintDebug
```

如果必须手动进入 `android/`：

```bash
bash -lc 'source scripts/android_env.sh && cd android && ./gradlew test assembleDebug'
```

已知坑：有些子会话 shell 不会继承 `JAVA_HOME` 或 `.zshrc`，裸 `./gradlew` 可能误报 `Unable to locate a Java Runtime`。遇到该错误时，先使用 `scripts/android_gradle.sh` 复跑；只有包装脚本也失败，才能报告 JDK 阻塞。

### Android 设备 / 模拟器

截至 2026-05-19，主控会话已安装 Android Emulator，并创建本机 tablet AVD：

```text
AVD name: child_ai_tablet_api35
System image: system-images;android-35;google_apis_tablet;arm64-v8a
Device profile: pixel_tablet
```

启动模拟器：

```bash
bash scripts/start_android_emulator.sh
```

无窗口 smoke test 可用：

```bash
bash scripts/start_android_emulator.sh --headless
```

安装并打开 debug 包：

```bash
bash scripts/install_android_debug.sh
```

模拟器访问宿主机后端时，后端必须监听 `0.0.0.0:8000`，模拟器侧使用 `10.0.2.2:8000`：

```bash
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
bash scripts/android_env.sh adb shell 'curl -fsS http://10.0.2.2:8000/api/v1/health'
```

已知坑：`child_ai_tablet_api35` 里 `AndroidWifi` 可能已保存但处于禁用/未连接状态，表现为 `ip route` 为空或 `10.0.2.2` 报 `Network is unreachable`。先执行：

```bash
bash scripts/android_env.sh adb shell cmd wifi connect-network AndroidWifi open
bash scripts/android_env.sh adb shell cmd wifi status
```

中文输入：

```bash
# 切到系统 Gboard 中文拼音 subtype，适合手动在模拟器里用拼音输入。
bash scripts/android_env.sh adb shell settings put secure selected_input_method_subtype 617035939
bash scripts/android_env.sh adb shell ime set com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME
```

自动化 QA 需要直接注入中文时，Android 自带 `adb shell input text` 对中文会失败或只输入拼音。当前模拟器已安装调试输入法 ADBKeyBoard，仅用于本机 emulator QA，不属于产品 APK，也不进入仓库：

```bash
# 如模拟器重建后需要重新安装，可从开源 release 下载到 /tmp 后安装。
curl -fL -o /tmp/child-ai-qa/adbkeyboard.apk \
  https://github.com/senzhk/ADBKeyBoard/releases/download/v2.5-dev/keyboardservice-debug.apk
bash scripts/android_env.sh adb install -r /tmp/child-ai-qa/adbkeyboard.apk
bash scripts/android_env.sh adb shell ime enable com.android.adbkeyboard/.AdbIME
bash scripts/android_env.sh adb shell ime set com.android.adbkeyboard/.AdbIME
bash scripts/android_env.sh adb shell am broadcast -a ADB_INPUT_TEXT --es msg '我有一道题不会'
```

设备侧验收前必须运行：

```bash
bash scripts/android_env.sh adb devices
```

如果 `adb devices` 没有设备，先启动上面的 AVD；如果模拟器启动失败，再考虑连接真实平板。

### Mimo 模型配置

Mimo OpenAI-compatible provider 已完成本机 smoke。注意模型 id 是：

```text
mimo-v2.5-pro
```

已知坑：`mimo-v2.5pro` 会返回 HTTP 400 `Not supported model`。不要再使用无连字符版本。

真实 smoke 只能用临时环境变量，不能把真实 key 写入 `.env`、文档、测试、Android 或 git：

```bash
export CHILD_AI_MODEL_PROVIDER=mimo
export CHILD_AI_MIMO_ENABLED=true
export CHILD_AI_MIMO_MODEL=mimo-v2.5-pro
export CHILD_AI_MIMO_ALLOW_CHILD_DATA=true
export CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=true
export CHILD_AI_MIMO_ALLOW_IMAGE=false
export CHILD_AI_MIMO_ALLOW_AUDIO=false
```

当前结论：在允许 child data 和 retention checked 均为 true 时，`ChildAgentRuntime`
可以走到 Mimo 并返回 `source=model`。运行时会清理模型输出中的 emoji/Markdown/过长内容；如果模型输出出现“悄悄告诉我”“只告诉我”“我们的小秘密”等秘密关系话术，会触发 fallback。

Mimo 相关协作规则：

```text
1. 默认仍是 MockModelProvider，真实 Mimo 只用于人工 smoke 或主控明确要求的临时验证。
2. 模型 id 必须是 mimo-v2.5-pro。
3. 真实 key 只能放在当前 shell 临时 env；不得写入 .env、.env.example、README、docs、测试、Android 或提交记录。
4. Android 端永远不放模型 key；所有真实模型调用只允许后端通过 ModelRegistry 和 provider gate。
5. QA 记录可以写“临时 env smoke 通过”，不能写出真实 token、账号、计费信息或请求正文中的真实儿童数据。
```

### 下一阶段 QA 清单

家庭内测前，后续 QA 子会话至少覆盖以下设备侧场景。全部使用虚构 child_id、虚构输入和 mock 题目，不使用真实儿童身份、照片或音频：

| 场景 | 核心期望 |
|---|---|
| 自由聊天 | 孩子输入普通兴趣话题时，不被固定按钮流程覆盖；回复保持温和、短句、不过度拟人依赖 |
| 学习求助 | 先引导读题、拆题、说思路；提供 `take_photo` / `speak_problem` 等动作；不直接给最终答案 |
| 直接要答案 | 明确拒绝直接给答案，改为分步提示和选择式引导 |
| 高风险 | 进入 `safety.guardian`，鼓励告诉父母/老师/可信成人，并触发父亲提醒 |
| 隐私边界 | 不索要或保存地址、电话、学校、照片等隐私；提醒不要告诉 AI 或陌生人 |
| 父亲入口保护 | 点击不直接进入父亲页；长按后输 dev PIN；错误 PIN 温和提示；正确 PIN 才进入 |
| Mock 拍题 | 点击拍题走 mock attachment + conversation 连续调用；不接真实 CameraX；不保存真实照片 |
| Android 后端断开提示 | 停止后端后，Android 显示温和错误和稍后再试，不诱导孩子反复刷请求或自责 |
| 语音预留 | `speak_problem` 只是占位或 mock，不接真实录音作为必需流程，不保存原始音频 |
| 小白狐动画预留 | 第一版只保留轻量视觉或占位，不做复杂动画或上瘾式反馈 |

---

## 3. 共性问题处理规则

### 3.1 先查共享上下文

如果遇到环境、命令、端口、base URL、网络、构建、测试相关问题，先搜索：

```bash
rg -n "关键词" docs/session_process docs/MANUAL_QA_V0_1.md backend/README.md android/README.md scripts
```

不要把已经记录过的坑当成新阻塞。

### 3.2 先用标准入口复现

常用标准入口：

```bash
bash scripts/doctor_local_env.sh
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/e2e_local_api_check.sh
```

子会话可以报告标准入口失败，但必须贴出标准入口命令和关键错误，不要只报告裸命令失败。

### 3.3 阻塞分级

```text
真实阻塞：
- 标准入口失败，且主控会话共享上下文没有已知解决方式。
- 缺少必须的人为操作，例如没有连接 Android 设备。

误判阻塞：
- 裸命令失败，但标准入口通过。
- PATH/JAVA_HOME/ANDROID_HOME/PYTHON_BIN 未加载，但仓库脚本可以补齐。

待确认阻塞：
- 网络 IP、设备连接、macOS 防火墙、代理/VPN 等可能随环境变化的问题。
```

### 3.4 交接必须包含共享上下文项

子会话交接时必须说明：

```text
共享上下文更新：
- 是否发现新的共性坑：
- 是否需要更新 docs/session_process/SHARED_CONTEXT_V0_1.md：
- 是否使用了标准入口命令：
```

主控会话负责决定是否更新共享上下文并提交。

---

## 4. 当前已知坑清单

| ID | 问题 | 状态 | 标准处理 |
|---|---|---|---|
| K01 | 子会话裸 `./gradlew` 误报缺少 Java Runtime | 已知 | 使用 `bash scripts/android_gradle.sh ...` 或 `bash scripts/android_env.sh <command>` |
| K02 | 非交互 shell 找不到 `conda` | 已知 | 根脚本会探测 `/opt/homebrew/bin/conda`；必要时显式设置 `PYTHON_BIN` |
| K03 | 系统 `python3` 是 3.9.x，不满足 backend | 已知 | 使用 `child-ai` conda 环境或 `PYTHON_BIN` |
| K04 | 设备侧 Android UI 验收需要真机或 AVD | 处理中 | 优先使用 `child_ai_tablet_api35` AVD；必要时连接真实平板 |
| K05 | 后端 policy/report/memory 是进程内存态 | v0.1 可接受 | 联调记录中说明重启会丢失，后续持久化再处理 |
| K06 | 模拟器 `AndroidWifi` 未连接导致 `10.0.2.2` 不通 | 已知 | `adb shell cmd wifi connect-network AndroidWifi open`，并用模拟器内 `curl http://10.0.2.2:8000/api/v1/health` 验证 |
| K07 | `adb shell input text` 不能可靠输入中文 | 已知 | 手动 QA 用系统 Gboard 中文拼音；自动化 QA 用 emulator 内 ADBKeyBoard 广播注入中文 |
| K08 | Mimo 模型名 `mimo-v2.5pro` 会被网关拒绝 | 已知 | 使用 `mimo-v2.5-pro` |

---

## 5. 主控会话职责

主控会话必须：

```text
1. 审查子会话报告里的阻塞是否已经在共享上下文中有处理方式。
2. 对误判阻塞及时纠正，并更新提示词或脚本。
3. 把新增共性坑写入本文件，而不是只留在聊天记录里。
4. 在后续子会话启动提示词中引用本文件。
5. 保持标准入口脚本可运行，避免每个子会话重新拼环境变量。
```
