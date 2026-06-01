# E6 V0.2 真机 QA 计划

## 1. 已阅读文档

```text
README.md
AGENTS.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/session_process/README.md
docs/session_process/SHARED_CONTEXT_V0_1.md
docs/session_process/轻量交接协议_2026_05_30_V0_1.md
docs/给小白狐看看2_0与小屋可见共创增强设计_2026_06_01_V0_1.md
docs/session_process/handoffs/20260601_E1_visual_kind_mapping_handoff.md
docs/session_process/handoffs/20260601_E2_android_visible_object_shadow_handoff.md
docs/session_process/handoffs/20260601_E3_image_detail_cocreation_handoff.md
docs/session_process/handoffs/20260601_E4_landing_feedback_handoff.md
docs/session_process/handoffs/20260601_E5_add_friend_cocreation_handoff.md
```

## 2. 任务范围理解

本轮是 E6 真机验收，不是新功能开发。

目标：

```text
验证 V0.2 是否真的让孩子端感知变强，
尤其是“给小白狐看看 -> 看见一个细节 -> 起名 -> 小物件落到小屋 -> 第二天召回 -> 加一个朋友”的完整链路。
```

本轮默认先做：

```text
1. 真机链路检查。
2. 后端真实返回检查。
3. Android 真机可见性检查。
4. 截图 / 录屏留档。
5. 只在发现明确阻塞 bug 时提出小修项。
```

本轮不先做：

```text
1. 不先改 prompt。
2. 不先改家长端产品边界。
3. 不先改共创玩法。
4. 不先扩展小客人数据模型。
5. 不先改奖励、宠物、列表、收藏等方向。
```

## 3. 会修改的文件

计划阶段只修改：

```text
docs/session_process/handoffs/20260601_E6_v02_true_device_qa_plan.md
```

真机执行阶段预留输出：

```text
docs/session_process/handoffs/20260601_E6_v02_true_device_qa_handoff.md
docs/session_process/handoffs/e6_screenshots/
```

如果出现明确阻塞 bug，等待主控确认后，才进入最小修复。

## 4. 不会修改的文件

计划阶段不修改：

```text
backend/app/prompts/
backend/app/services/parent_report_service.py
backend/app/services/parent_report_language_v4.py
backend/app/services/prompt_manager.py
android/app/src/main/assets/mascot/xiaobaohu/v2/ 现有状态资源
家长端产品文案
儿童端 master-copy 文案
```

在主控确认前，不做任何代码修复。

## 5. 是否涉及文案 / prompt / 家长端表达

```text
不改文案。
不改 prompt。
不改家长端表达。
本轮只验证这些内容是否按既定设计真实生效。
```

## 6. 当前环境与真机准备

当前已确认：

```text
远程 main 已同步，本地分支为最新 main。
doctor_local_env.sh 通过。
后端 main 服务运行中，0.0.0.0:8000，health=ok。
模型 / vision / ASR / TTS 配置均为真实链路可用状态。
Honor Pad 5 当前已通过 USB 连上 adb。
Redmi K60 当前未在 adb 列表中出现。
```

当前 E6 真机前置条件判断：

```text
平板链路可先执行。
手机链路需在 Redmi K60 接入后补测。
```

## 7. 测试数据与账号策略

E6 不能只用已有历史账号做全链路验证。

原因：

```text
已有历史账号可能已经存在 active 小客人，
会直接跳过 seed 首次起名路径，
也可能受 same-session / same-day recall 抑制影响。
```

本轮计划使用三类测试账号或测试状态：

```text
1. 全新孩子账号：
   用于验证首次 opening / 图片成功 / 起名 / 首次落屋。

2. 已有 active 小客人的孩子账号：
   用于验证 reopen recall / 加一个朋友 / 先聊别的。

3. 图片失败测试账号或同一账号的失败分支：
   用于验证失败文案、无起名按钮、无 companion_object 创建。
```

第二天 recall 的验证策略：

```text
优先：使用已有 active 小客人的可召回测试数据。
备选：若同日 recall 被规则抑制，则记录为“规则阻塞当前会话验证”，
并在主控允许下使用测试数据准备方式补足，不在本轮先改产品规则。
```

## 8. 真机验收矩阵

### 8.1 图片成功路径

验证点：

```text
1. 小白狐是否使用确定性模板：
   我看到{细节}啦
   像{温柔想象}
   要不要给它起个名字？
2. 是否只出现一个按钮：起个名字
3. 不出现“上传成功 / 识别成功 / 图片分析结果”
4. 不出现“编个小故事”
```

证据：

```text
真机截图
后端 opening / attachment / conversation 日志摘要
必要时 UI 树或录屏
```

### 8.2 图片失败路径

验证点：

```text
1. 是否显示：
   这张图还没看到
   可以再试一次，也可以先不看
2. 是否没有“起个名字”
3. 是否不创建 companion_object
```

证据：

```text
真机截图
后端 companion_object 状态检查
```

### 8.3 起名成功路径

验证点：

```text
1. 输入“叫小棉花”
2. 是否返回：
   小棉花，软软的名字
   它轻轻落到窗边啦
3. 是否无 quick_actions
4. 是否本轮就显示对应小物件影子
```

### 8.4 Android 小物件影子

验证点：

```text
1. star / cloud / paper_boat / tiny_door / dino_shadow / block_light 是否能区分
2. 是否明显可见
3. 是否不抢小白狐
4. 是否不奖励化、不宠物化
```

方法：

```text
优先用不同 visual_kind 的测试数据或不同图片类型触发。
若同轮难以覆盖 6 种，至少保证每种在真机截图或录屏中留证。
```

### 8.5 recall 路径

验证点：

```text
1. 是否出现：
   小棉花今天在窗边呢
   要不要给它加一个朋友？
2. 是否出现按钮：
   加一个朋友
   先聊别的
3. 是否有对应位置的小物件影子
```

### 8.6 加一个朋友路径

验证点：

```text
1. 点击“加一个朋友”
2. 是否出现：
   那我们给它找一个小伙伴
   你可以说一个名字，也可以给我看看
3. 是否出现按钮：
   说个名字
   给小白狐看看
   先聊别的
```

### 8.7 加朋友说名字路径

验证点：

```text
1. 点击“说个名字”
2. 输入“叫小云朵”
3. 是否返回：
   小云朵，也来小屋里待一会儿啦
4. 是否不创建第二个 active 小客人
5. 是否不出现“新朋友已解锁 / 收集成功 / 任务完成”
```

### 8.8 加朋友图片路径

验证点：

```text
1. 点击“给小白狐看看”
2. Android 是否真的拉起拍图 / 图片入口
3. 图片成功后是否能继续起名
4. 如果按钮只显示但没有拉起相机，标记 BLOCKED
```

若 BLOCKED，计划中的小修项说明应限定为：

```text
只修 Android quick_action 到图片入口的触发映射，
不改文案、不改后端共创规则。
```

### 8.9 跳过路径

验证点：

```text
1. 点击“先聊别的”
2. 是否清除 pending extension
3. 是否本会话不再拉回
4. 不出现亏欠感文案
```

### 8.10 家长端

验证点：

```text
1. 是否仍只显示高层轻共创摘要
2. 不显示小客人名字、朋友名字、位置、跳过、次数、图片细节
```

## 9. 真机执行顺序

建议顺序：

```text
第一阶段：Honor Pad 5
1. 首次图片成功链路
2. 图片失败链路
3. 起名成功后的落屋可见性
4. 小物件影子可见性与区分度
5. recall / 加一个朋友 / 跳过
6. 家长端摘要边界

第二阶段：Redmi K60
1. 复跑图片成功链路
2. 复跑 recall / 加朋友图片入口
3. 补手机尺寸下的小物件可见性
4. 补录屏与截图
```

## 10. 预判阻塞项与小修判定

当前预判的高概率阻塞，不先修，只先验证：

```text
1. Redmi K60 当前未连 adb，手机链路暂时无法执行。
2. recall 存在 same-day / same-session 抑制，可能导致当天无法自然复现。
3. 加朋友图片路径虽然已有设计与代码交接，但真机上可能只显示按钮、不拉起相机。
4. 纯 Canvas 小物件影子在平板和手机上可能仍然辨识度不足。
```

只有满足以下条件，才作为“小修项”提给主控确认：

```text
1. 后端响应正确，但 Android 没有把 quick_action 触发到真实图片入口。
2. 后端 companion_meta 已带 visual_kind，但 Android 真机几乎不可见或类型无法区分。
3. 图片失败仍误创建 companion_object。
4. 起名完成后 quick_actions 未清空。
5. 家长端泄露了名字、位置、图片细节。
```

## 11. 测试策略

自动化与真机分层：

```text
1. 先用当前代码与文档核对既定口径，不重新设计。
2. 真机为主，日志与数据库检查为辅。
3. 每个关键节点至少留一张截图；复杂链路优先录屏。
4. 需要时读取后端日志、数据库 companion_object 记录、Android logcat。
5. 真机结论按 PASS / CONDITIONAL / BLOCKED 标注。
```

计划阶段不新增测试代码。

## 12. 风险点

```text
1. 同日 recall 规则可能让“第二天召回”无法在同一晚完整自然复现。
2. 只有平板在线时，手机专属可见性问题无法当场盖住。
3. 图片失败分支依赖真实 vision 返回低置信度或不可用类型，构造样本要谨慎。
4. 如果当前测试账号带历史状态，容易误判 seed / recall / extension 逻辑。
```

## 13. 发现的文档与代码冲突

当前计划阶段未发现明确冲突。

已知需要真机验证的灰区：

```text
1. E5 交接中提到 extension 图片路径功能正确，但真机尚未验。
2. E2 交接中提到纯 Canvas 形状辨识度需真机验证。
3. E3 / E4 / E5 多处交接仍标注“真机未完成”，E6 正是补这部分。
```

## 14. 需要主控确认的问题

当前无必须先确认才能写计划的产品问题。

执行阶段若出现以下情况，将回报主控：

```text
1. recall 因规则抑制导致当天无法完成 E6 闭环。
2. 加朋友图片入口只显示按钮、无法真实拉起相机。
3. 小物件影子在真机上可见性明显不足，需要 Android 小修。
```
