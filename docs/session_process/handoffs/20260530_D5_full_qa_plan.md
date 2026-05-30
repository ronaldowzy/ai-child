# D5 完整 QA 计划：小白狐关系与轻连续体验版验收

状态：计划待主控审核

更新时间：2026-05-30

---

## 0. 任务目标

验证"小白狐关系与轻连续体验版"是否可进入连续三天真实家庭测试。

D5 不改代码，除非发现明确阻塞 bug 并经主控确认。

---

## 1. 已阅读文档

```text
README.md
AGENTS.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
docs/session_process/轻量交接协议_2026_05_30_V0_1.md
docs/session_process/handoffs/20260530_D1_companion_object_handoff.md
docs/session_process/handoffs/20260530_D2_runtime_companion_object_handoff.md
docs/session_process/handoffs/20260530_D3_android_companion_object_handoff.md
docs/session_process/handoffs/20260530_D4_parent_summary_boundary_handoff.md
docs/小白狐关系与轻连续体验总设计_2026_05_30_V0_1.md
docs/小屋小客人共创延续机制设计_2026_05_30_V0_1.md
docs/明天还记得轻记忆与召回规则_2026_05_30_V0_1.md
docs/小白狐首次与每日打开体验设计_2026_05_30_V0_1.md
docs/四个核心场景话术与状态库_2026_05_30_V0_1.md
docs/连续三天真实家庭测试脚本_2026_05_30_V0_1.md
docs/小白狐关系与轻连续体验开发任务清单_2026_05_30_V0_1.md
```

---

## 2. D1-D4 提交确认

| 泳道 | 提交 | 状态 |
|---|---|---|
| D1 后端小屋小客人与轻记忆 | `bdf6f91` / `1f6d2b0`（返修） | done |
| D2 对话运行时与提示词接入 | `5749654` / `a0d6c2f`（返修） | done |
| D3 Android 儿童端小屋呈现 | `49feab6` | done |
| D4 家长端摘要边界 | `a480cc3` | done |

---

## 3. QA 分阶段计划

### 阶段 A：后端完整测试（自动化）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| A1 | 后端全量单测 | `bash scripts/test_backend.sh` | 0 failed |
| A2 | 后端 lint | `bash scripts/lint_backend.sh` | 无新增 error |
| A3 | companion_object 专项 | `bash scripts/test_backend.sh -k "test_companion_object" -v` | 全部 passed |
| A4 | companion_object_runtime 专项 | `bash scripts/test_backend.sh -k "test_companion_object_runtime" -v` | 全部 passed |
| A5 | parent_report_companion 专项 | `bash scripts/test_backend.sh -k "test_parent_report_companion" -v` | 全部 passed |
| A6 | bedtime opening 修复确认 | `bash scripts/test_backend.sh -k "test_bedtime_opening" -v` | 全部 passed |
| A7 | 禁止话术扫描 | grep 后端代码和 prompt 模板，扫描 master-copy 禁止列表中的关键词 | 0 匹配 |

### 阶段 B：Android 测试与构建（自动化）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| B1 | Android 全量单测 | `bash scripts/android_gradle.sh test` | 已知失败仅 `audioReadyUsesQueueWhenNotMuted`，无新增失败 |
| B2 | Android assembleDebug | `bash scripts/android_gradle.sh assembleDebug` | BUILD SUCCESSFUL |
| B3 | Android lintDebug | `bash scripts/android_gradle.sh lintDebug` | 无新增 error |
| B4 | 已知失败复核 | 检查 `ChatViewModelStreamTest > audioReadyUsesQueueWhenNotMuted` 是否仍为 D3 前已有失败 | 确认非 D1-D4 引入 |

### 阶段 C：首次打开小星星 seed（代码验证 + 真机）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| C1 | 后端 seed 逻辑 | 代码审查 `opening_service.py`：无小客人历史 + 非睡前 + 安全场景 → `COMPANION_STAR_SEED` | 逻辑正确 |
| C2 | 后端 seed 文案 | 代码审查 opening 文案是否与 master-copy 一致："窗边这颗小星星还没有名字\n要不要给它起一个？" | 完全一致 |
| C3 | 后端 seed 按钮 | 代码审查 quick_actions 是否为 "起个名字" / "先看看" | 完全一致 |
| C4 | 后端 seed metadata | 代码审查返回 state="seed", action="name_seed"，不调用 create() | 逻辑正确 |
| C5 | Android seed 视觉点 | 代码审查 `XiaobaohuCompanionStage.kt`：seed 状态窗边小星点，呼吸式 3 秒，暖黄色 | 逻辑正确 |
| C6 | 真机首次打开 | Redmi K60 安装 debug 包，清除数据后首次打开 | 截图：窗边小星点 + 起名种子气泡 |
| C7 | 真机起名流程 | 输入名字后确认小白狐轻回应 | 截图/录屏：起名成功 → 小客人留在窗边 |

### 阶段 D：有小客人 opening 轻召回（代码验证 + 真机）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| D1 | 后端召回逻辑 | 代码审查 `opening_service.py`：有活跃小客人 + 非睡前 + 本会话未召回 → `COMPANION_RECALL` | 逻辑正确 |
| D2 | 后端召回文案 | 代码审查是否与 master-copy 一致："{name}今天在{location}呢\n要不要给它加一个朋友？" | 完全一致 |
| D3 | 后端召回按钮 | 代码审查 quick_actions 是否为 "加一个朋友" / "先聊别的" | 完全一致 |
| D4 | Android recall 视觉点 | 代码审查：recall 状态根据 light_location 在对应位置显示小光点/小光影/小云影 | 逻辑正确 |
| D5 | 真机召回 | 第一天创建小客人后，第二天（或清除 session 后重新）打开 | 截图：recall 对应 light_location 轻视觉点 |

### 阶段 E：睡前不召回（代码验证 + 真机）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| E1 | 后端睡前过滤 | 代码审查 `opening_service.py`：is_bedtime=True 时不返回 COMPANION_RECALL 和 COMPANION_STAR_SEED | 逻辑正确 |
| E2 | 后端睡前测试 | 运行 bedtime 相关测试 | 全部 passed |
| E3 | 真机睡前 opening | 修改设备时间为睡前时段（21:00+），打开 App | 截图：睡前 opening，无小客人召回、无小星星种子 |

### 阶段 F：跳过后本会话不再拉回（代码验证 + 真机）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| F1 | 后端跳过逻辑 | 代码审查 `conversation_service.py`：检测"先聊别的"等信号 → `mark_skipped()` | 逻辑正确 |
| F2 | 后端同会话抑制 | 代码审查 `SessionRecallTracker`：同 session_id 不再召回 | 逻辑正确 |
| F3 | 后端跳过测试 | 运行 skip 相关测试 | 全部 passed |
| F4 | 真机跳过 | 有小客人召回时点击"先聊别的"，继续对话后再次触发 opening | 截图/录屏：点击"先聊别的"后不再拉回 |

### 阶段 G：图片成功后只出现"起个名字"（代码验证 + 真机）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| G1 | 后端图片共创逻辑 | 代码审查 `conversation_service.py`：图片成功后只输出一个"起个名字"按钮 | 逻辑正确 |
| G2 | 后端图片共创测试 | 运行图片共创相关测试 | 全部 passed |
| G3 | 真机拍图成功 | 拍一张非隐私图片上传 | 截图：只出现一个"起个名字"共创入口 |

### 阶段 H：图片失败后不出现共创入口（代码验证 + 真机）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| H1 | 后端图片失败逻辑 | 代码审查：图片失败时不输出共创按钮 | 逻辑正确 |
| H2 | 后端图片失败测试 | 运行图片失败相关测试 | 全部 passed |
| H3 | 真机拍图失败 | 断开后端或模拟网络异常后拍图 | 截图：失败态无共创入口 |

### 阶段 I：Android 小星点 / 小光影渲染（代码审查 + 真机）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| I1 | 视觉点代码审查 | 审查 `XiaobaohuCompanionStage.kt`：Compose Canvas 绘制，尺寸 16-24dp，alpha 0.5-0.8，blur 柔化 | 代码正确 |
| I2 | 视觉状态映射测试 | 运行 `CompanionObjectVisualTest` | 13 个用例全部 passed |
| I3 | 真机视觉点 | Redmi K60 和 Honor Pad 5 分别截图 | 截图：小星点/小光影位置合理，不抢小白狐主视觉 |
| I4 | 暂放状态 | 代码审查：state="paused" 时不显示视觉点 | 逻辑正确 |

### 阶段 J：横屏 / 平板视觉点位置（真机）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| J1 | Honor Pad 5 横屏 | 平板横屏打开，有小客人召回 | 截图：小客人位置合理，不变成聊天控制台 |
| J2 | Honor Pad 5 竖屏 | 平板竖屏打开，有小客人召回 | 截图：小客人位置合理 |
| J3 | Redmi K60 横屏 | 手机横屏打开 | 截图：布局不异常 |

### 阶段 K：家长端"轻共创"区块（代码验证 + 真机）

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| K1 | 后端 companion_summary 逻辑 | 代码审查 `parent_report_service.py`：有轻共创时返回 companion_summary，无时不返回 | 逻辑正确 |
| K2 | 后端 companion_summary 文案 | 代码审查是否只有 3 类确定性表达，与 master-copy 一致 | 完全一致 |
| K3 | 后端 PAUSED 不展示 | 代码审查：PAUSED 状态小客人不触发 companion_signal | 逻辑正确 |
| K4 | 后端禁止表达 | 代码审查 `COMPANION_FORBIDDEN` 列表 | 包含所有 master-copy 禁止表达 |
| K5 | Android 家长端 UI | 代码审查 `ParentReportScreen.kt`：companionSummary 非空时显示"轻共创"区块 | 逻辑正确 |
| K6 | 真机家长端 | 有轻共创后查看家长日报 | 截图：轻共创区块显示，无逐字聊天、无小客人名字/位置 |

### 阶段 L：日志和数据安全

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| L1 | 后端日志扫描 | grep 后端日志输出，检查是否包含儿童原文、图片 base64、音频内容、API key | 0 匹配 |
| L2 | safe_summary 长度 | 代码审查：领域层限制 200 字，DB 字段 500 字 | 逻辑正确 |
| L3 | 不保存原始数据 | 代码审查：companion_object 不保存原始音频、照片、长篇原文 | 逻辑正确 |
| L4 | 禁记内容过滤 | 代码审查：创建时执行隐私、负面事件、学习题目、保密内容过滤 | 逻辑正确 |
| L5 | Android 端无 API key | grep Android 代码检查是否有模型 API key 硬编码 | 0 匹配 |

### 阶段 M：禁止话术扫描

| 序号 | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| M1 | 儿童端禁止话术 | 扫描后端 prompt 模板和 opening/conversation 代码，对照 master-copy 禁止列表 | 0 匹配 |
| M2 | 家长端禁止表达 | 扫描 parent_report 代码，对照 master-copy 家长端禁止列表 | 0 匹配 |
| M3 | 秘密关系话术 | 扫描"悄悄告诉我""只告诉我""我们的小秘密""只有我记得""只有我懂你" | 0 匹配 |
| M4 | 依赖话术 | 扫描"我一直在等你""你不来我会想你""明天一定要来""小棉花会等你""它会难过" | 0 匹配 |
| M5 | 游戏化话术 | 扫描"连续""打卡""任务完成""奖励""领取""升级""徽章" | 0 匹配（排除注释和测试） |

---

## 4. 真机测试设备

| 设备 | 用途 | 优先级 |
|---|---|---|
| Redmi K60 | 主力真机，手机竖屏/横屏 | 必须 |
| Honor Pad 5 | 平板竖屏/横屏 | 必须 |

真机测试前准备：

```text
1. 连接设备，确认 adb devices 可见。
2. 启动后端：bash scripts/start_backend_services.sh --agent main --host 0.0.0.0 --port 8000
3. 构建 APK：bash scripts/build_device_debug_apk.sh --base-url http://192.168.0.118:8000/
4. 安装：bash scripts/install_android_debug.sh
```

---

## 5. 截图 / 录屏提交清单

| 序号 | 内容 | 对应检查项 | 设备 |
|---|---|---|---|
| S1 | 首次打开 seed：窗边小星点 + 起名种子气泡 | C6 | Redmi K60 |
| S2 | 小星星窗边轻视觉点特写 | C6, I3 | Redmi K60 |
| S3 | 有小客人 recall：light_location 对应视觉点 | D5 | Redmi K60 |
| S4 | recall 对应 light_location 轻视觉点特写 | D5, I3 | Redmi K60 |
| S5 | 点击"先聊别的"后不再拉回（录屏） | F4 | Redmi K60 |
| S6 | 拍图成功只显示一个共创入口 | G3 | Redmi K60 |
| S7 | 拍图失败无共创入口 | H3 | Redmi K60 |
| S8 | 睡前 opening | E3 | Redmi K60 |
| S9 | 家长端轻共创区块 | K6 | Redmi K60 |
| S10 | 横屏/平板小客人位置 | J1, J2 | Honor Pad 5 |
| S11 | 平板横屏小客人位置 | J1 | Honor Pad 5 |

截图保存路径：`docs/session_process/handoffs/d5_screenshots/`

---

## 6. 已知问题复核

| 问题 | 来源 | 复核方式 |
|---|---|---|
| `ChatViewModelStreamTest > audioReadyUsesQueueWhenNotMuted` 失败 | D3 已记录，非 D1-D4 引入 | 运行 Android 单测，确认仍为同一失败，无新增失败 |
| 同会话召回抑制使用进程内存 | D1/D2 已知 K05 | 代码确认 `SessionRecallTracker` 为进程内存，记录为 v0.1 可接受 |
| 横屏/平板视觉点位置需真机确认 | D3 已知 | 阶段 J 真机截图确认 |

---

## 7. 执行顺序

```text
第 1 步：阶段 A（后端测试）— 自动化，先跑
第 2 步：阶段 B（Android 测试与构建）— 自动化，可与 A 并行
第 3 步：阶段 C-M（代码审查 + 禁止话术扫描）— 代码审查，不依赖真机
第 4 步：连接真机，启动后端，构建安装 APK
第 5 步：阶段 C6-C7, D5, E3, F4, G3, H3（真机功能验证）— Redmi K60
第 6 步：阶段 I3, J1-J3（视觉点与横屏/平板）— Honor Pad 5
第 7 步：阶段 K6（家长端真机验证）
第 8 步：汇总 QA 结论
```

---

## 8. QA 结论格式

最终输出格式：

```text
D5 QA 结论

后端测试：PASS / FAIL（附失败项）
Android 测试：PASS / FAIL（附失败项）
Android 构建：PASS / FAIL
已知失败复核：确认非 D1-D4 引入 / 新增失败
首次打开 seed：PASS / FAIL
有小客人 recall：PASS / FAIL
睡前不召回：PASS / FAIL
跳过后不再拉回：PASS / FAIL
图片成功只出现"起个名字"：PASS / FAIL
图片失败无共创入口：PASS / FAIL
Android 视觉点渲染：PASS / FAIL
横屏/平板位置：PASS / FAIL
家长端轻共创区块：PASS / FAIL
日志和数据安全：PASS / FAIL
禁止话术扫描：PASS / FAIL

是否可进入连续三天家庭测试：YES / NO / CONDITIONAL
阻塞问题：（如有）
建议修正：（如有）
```

---

## 9. 边界约束

```text
1. 不用 mock 冒充真实路径。
2. 不改产品设计。
3. 不新增文案。
4. 不扩大功能。
5. 不启动家庭测试前必须先给主控 QA 结论。
6. 发现阻塞 bug 时先记录，经主控确认后才修。
```

---

## 10. 需要主控确认的问题

1. **已知 Android 测试失败**：`ChatViewModelStreamTest > audioReadyUsesQueueWhenNotMuted` 在 D3 前已存在。D5 计划将其标记为"已知非引入"，不阻塞发版。主控是否同意？
2. **同会话召回抑制进程内存**：`SessionRecallTracker` 使用进程内存，服务重启后丢失。D1/D2 已标记为 v0.1 可接受（K05）。D5 是否同样接受？
3. **横屏/平板视觉点**：D3 交接提到"横屏/平板的视觉点位置需要真机截图确认，当前使用相对锚点可能需要微调"。如果真机发现位置不理想，D5 是否可以微调视觉点坐标（属于 bug 修复范围），还是必须回到主控确认？
4. **真机设备连接**：当前 `adb devices` 无设备。D5 真机测试需要连接 Redmi K60 和 Honor Pad 5。请确认设备可用后通知 D5 开始真机阶段。
5. **截图保存路径**：计划使用 `docs/session_process/handoffs/d5_screenshots/`，主控是否同意？
