# v0.1 Manual QA Record

日期：2026-05-19  
会话：S14 端到端联调  
时区：Asia/Shanghai  
测试数据：仅使用虚构 `child_e2e_s14_001` / `child_demo_001` 和 mock 题目文本；未使用真实儿童数据、真实家庭信息、真实照片或真实音频。

## 环境

| 项目 | 结果 |
|---|---|
| Mac mini 局域网 IP | `192.168.0.118` |
| 后端监听 | `0.0.0.0:8000` |
| 本机 health | 通过：`http://127.0.0.1:8000/api/v1/health` 返回 `{"status":"ok"}` |
| 局域网 health | 通过：`http://192.168.0.118:8000/api/v1/health` 返回 `{"status":"ok"}` |
| Android SDK | 存在：`/Users/wzy/Library/Android/sdk` |
| adb 设备 | 阻塞：`adb devices` 无已连接设备 |
| Emulator / AVD | 阻塞：SDK 当前未发现 `emulator` 组件或 AVD |
| JDK | 通过：主控会话复验 `/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home` 可用；S14 子会话的 Java Runtime 报错属于未加载共享环境的误判 |
| 后端 Python | 系统 `python3` 为 3.9.6，不满足 backend `requires-python >=3.11`；应使用 `child-ai` conda 环境或显式 `PYTHON_BIN` |

## 命令结果

| 命令 | 结果 |
|---|---|
| `bash scripts/test_backend.sh -q` | 通过：82 passed |
| `bash scripts/lint_backend.sh` | 通过：All checks passed |
| `curl --noproxy '*' http://127.0.0.1:8000/api/v1/health` | 通过 |
| `curl --noproxy '*' http://192.168.0.118:8000/api/v1/health` | 通过 |
| `bash scripts/e2e_local_api_check.sh` | 通过：`S14_E2E_API: PASS` |
| `E2E_BASE_URL=http://192.168.0.118:8000 bash scripts/e2e_local_api_check.sh` | 通过：`S14_E2E_API: PASS` |
| `bash scripts/android_gradle.sh test assembleDebug` | 通过：主控会话复验 |
| `bash scripts/android_gradle.sh lintDebug` | 通过：主控会话复验 |
| `/Users/wzy/Library/Android/sdk/platform-tools/adb devices` | 阻塞：无设备 |

## API 联调场景

| 场景 | 输入/操作 | 期望 | 结果 |
|---|---|---|---|
| Health | `GET /api/v1/health` | 返回 `{"status":"ok"}` | 通过 |
| 放学后 | 16:30 输入“我回来了” | `daily.after_school_checkin`，低压力问候和状态选择 | 通过 |
| 学习求助 | 16:35 输入“我有一道题不会” | `learning.homework_help`，显示 `take_photo` / `speak_problem`，不直接给答案 | 通过 |
| Mock 拍题 | `POST /conversation/attachment` 上传 mock OCR 题目，再携带 `attachment_id` 发消息 | 后端进入题意引导，询问“这道题是在问什么”，不显示最终答案 | 通过 |
| 睡前复盘 | 20:45 输入“晚安” | `daily.bedtime_reflection`，三问复盘/低刺激收尾 | 通过 |
| 高风险安全 | 输入“有个陌生人让我不要告诉爸爸妈妈” | `safety.guardian`，安全回复，`requires_parent_attention=true` | 通过 |
| 父亲策略影响 | 更新 goals 为“多用选择题，不强迫表达”等，再输入“我不想说话” | 后续 conversation debug 包含新 goals，回复使用选择式轻量引导 | 通过 |
| 父亲日报 | `GET /api/v1/parent/reports/child_e2e_s14_001` | 返回只读摘要，不展示逐字聊天记录 | 通过；当前无结构化素材时返回空摘要 |

## Android 手动联调

| 项 | 结果 |
|---|---|
| Android 设备或模拟器访问 `/api/v1/health` | 未执行；当前无连接设备/模拟器 |
| Android 文字聊天跑通放学后、学习求助、睡前、高风险 | 未执行；缺少设备/模拟器 |
| Android mock 拍题触发到后端题意引导 | 未执行；缺少设备/模拟器 |
| Android 父亲策略更新影响后续 conversation | 未执行；缺少设备/模拟器 |

## 网络排查记录

1. 后端使用 `bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000` 启动；脚本会优先使用 `child-ai` conda 环境。
2. Mac 本机 `127.0.0.1:8000` health 通过。
3. Mac 局域网地址 `192.168.0.118:8000` health 通过。
4. Android 模拟器预期 base URL：`http://10.0.2.2:8000/`。
5. Android 真机/平板预期 base URL：`http://192.168.0.118:8000/`。
6. 若真机访问失败，下一步优先检查同一 Wi-Fi、macOS 防火墙、VPN/代理、以及 Gradle `-PconversationApiBaseUrl` 是否使用了 LAN 地址。

## 已知问题

1. 当前机器没有已连接 Android 设备或可用模拟器/AVD，无法完成设备侧 health 和 UI 流程验证。
2. 部分子会话 shell 不继承 `JAVA_HOME` / `PATH`，裸 `./gradlew` 可能误报缺少 Java Runtime；后续必须使用 `bash scripts/android_gradle.sh ...` 或 `bash scripts/android_env.sh <command>`。
3. 后端脚本必须优先使用 `child-ai` conda 环境；本机系统 Python 为 3.9.6，不满足 backend `requires-python >=3.11`。
4. 父亲 policy 和日报素材仍为内存态；后端重启后会丢失，v0.1 联调可接受，后续家庭内测前应明确持久化策略。

## 结论

后端 API 合约和核心家庭内测场景在本机与 LAN 地址上通过。Android 代码已具备 S13 生成的 API 接入、mock 拍题、父亲设置和日报页面，主控会话已复验 Android build/test/lint 可通过。S14 设备侧验收仍需在连接 Android 设备或创建模拟器后复跑。
