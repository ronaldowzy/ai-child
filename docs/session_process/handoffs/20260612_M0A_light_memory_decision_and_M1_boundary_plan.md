# M0-A：小白狐轻记忆产品决策落档与 M1 边界计划

日期：2026-06-12

执行角色：产品决策落档与边界计划会话

状态：DOC PASS / 待主控审核

---

## 1. 本轮目标

本轮完成两件事：

```text
1. 将“小白狐轻记忆”写入 docs/PRODUCT_DECISIONS_V0_1.md。
2. 明确 M1 最小实现边界。
```

本轮不编码，不新增儿童端最终文案，不修改奇怪小门、小展台、语言游戏、后端或家长端代码。

---

## 2. 已阅读依据

```text
docs/小白狐轻记忆产品方向设计_2026_06_12_V0_1.md
docs/session_process/handoffs/20260612_M0_light_memory_product_direction_plan.md
docs/PRODUCT_DECISIONS_V0_1.md
docs/session_process/handoffs/20260609_LG_review_language_game_suite_handoff.md
docs/session_process/handoffs/20260609_LG1_brain_teaser_handoff.md
docs/session_process/handoffs/20260609_LG2_word_chain_handoff.md
docs/session_process/handoffs/20260609_LG3_riddle_handoff.md
docs/session_process/handoffs/20260608_S5_showcase_item_back_to_door_handoff.md
```

同步状态：

```text
git fetch origin main 已完成。
main 与 origin/main 差异为 0 / 0。
```

注意：

```text
当前工作区存在本轮之前遗留的 Android / release / 本地材料改动。
本轮未修改、未暂存、未提交这些改动。
```

---

## 3. PRODUCT_DECISIONS 新增 PD 编号

新增：

```text
PD-061
```

状态：

```text
confirmed
```

主题：

```text
小白狐轻记忆确认为新的产品方向。
```

---

## 4. PRODUCT_DECISIONS 表述

已在 `docs/PRODUCT_DECISIONS_V0_1.md` 增加表格行和结构化决策记录。

核心表述：

```text
小白狐轻记忆确认为下一阶段产品方向：
先做轻量、低敏、可放下的连续陪伴，
不做学习画像、隐私档案、成绩记录或复杂成长档案。

MVP 采用两阶段：
第一阶段只做 Android 本地轻状态 + 既有小展台数据；
第二阶段再评估后端白名单轻摘要。
```

M1 明确禁止：

```text
1. 不新增后端跨天轻摘要。
2. 不新增 memory endpoint。
3. 不新增数据表。
4. 不新增 image_purpose。
5. 不保存原始语音。
6. 不保存原始照片。
7. 不保存原始聊天全文。
8. 不保存孩子原始回答。
9. 不保存错误答案、分数、等级、排名。
10. 不做学习画像。
11. 不做家长报告项。
12. 不做积分、奖励、打卡、排行榜。
```

---

## 5. M1 是否只做本地轻状态 + 既有小展台数据

是。

M1 只允许使用：

```text
1. Android 本地生命周期内轻状态。
2. 奇怪小门已有本地状态。
3. 既有小展台数据读取能力。
4. 既有小展台 item 的安全可见字段。
```

M1 不做跨天后端轻摘要，不扩展记忆服务。

---

## 6. M1 是否禁止新增后端

是。

M1 禁止：

```text
1. 新增后端 endpoint。
2. 新增后端 service。
3. 新增 repository。
4. 新增数据表或 migration。
5. 新增 GrowthEvent。
6. 新增 image_purpose。
7. 改动 attachment 链路。
8. 改动 conversation / opening 后端接口。
```

如 M1 发现 Android 本地无法满足最小体验，需要先回主控确认，不得自行扩到后端。

---

## 7. M1 是否禁止新增儿童端最终文案

是。

M1 可以规划状态和数据合同，但不能自行新增儿童端最终文案。

允许做：

```text
1. 标注需要主控提供 opening 轻记忆 master-copy。
2. 在测试中使用非儿童端内部标识。
3. 复用已经存在的按钮或页面文本。
```

禁止做：

```text
1. 自行写 opening 记忆话术。
2. 自行写普通聊天记忆话术。
3. 自行写奇怪小门记忆提示语。
4. 自行新增“我记得你”类儿童端文案。
```

---

## 8. M1 是否需要先做数据合同

需要。

M1 应先做轻记忆数据合同，再实现 UI 或状态流转。

数据合同需要回答：

```text
1. 本地轻记忆 snapshot 放在哪里。
2. 如何从奇怪小门生成完成摘要。
3. 如何从小展台读取最近小发现名称。
4. 如何标记小展台小发现是否回来帮过门。
5. 如何记录本生命周期是否已经轻召回。
6. 如何记录本生命周期的跳过 / 暂放。
7. 如何确保 blocked / privacy / homework 不进入轻状态。
```

---

## 9. 轻记忆数据结构建议

建议新增 Android 本地轻量结构，名称由 M1 实现计划再确认，例如：

```text
LightMemorySnapshot
LightMemorySource
LightMemoryCandidate
LightMemoryStatus
```

建议字段：

```text
sourceType：
  StrangeDoorCompleted
  StrangeDoorTool
  ShowcaseItem
  ShowcaseAssist

safeLabel：
  低敏摘要标签，例如 round / soft / shiny / showcase_item。

displayName：
  小展台小发现名称或安全道具名。

mechanismType：
  Round / Soft / Shiny，可为空。

toolName：
  最近安全奇怪道具名，可为空。

showcaseItemId：
  既有小展台 item id，可为空。

showcaseItemName：
  既有小展台 item name，可为空。

lastTouchedAt：
  本地时间戳。

recalledInCurrentLifecycle：
  当前 ChatViewModel 生命周期是否已提过。

skipCountInCurrentLifecycle：
  当前生命周期跳过次数。

status：
  Active / MutedForLifecycle。
```

M1 不建议字段：

```text
1. rawTranscript。
2. rawPhotoBytes。
3. recognizedText。
4. childAnswer。
5. score。
6. rank。
7. school / address / phone / realName。
8. promptTrace。
```

---

## 10. 轻记忆来源白名单

M1 白名单仅限：

```text
1. 奇怪小门完成摘要。
2. 最近安全机关类型。
3. 最近安全道具名。
4. 小展台小发现名称。
5. 小展台小发现是否回来帮过门。
```

来源要求：

```text
1. 必须来自已经通过安全边界的本地状态或既有小展台 item。
2. 必须避开 blocked / privacy / homework。
3. 必须只保存摘要，不保存原始材料。
4. 必须只在当前 Android 生命周期内自动召回。
```

---

## 11. 轻记忆禁止来源

M1 禁止来源：

```text
1. 语言游戏偏好。
2. 普通聊天自由抽取。
3. 后端长期记忆摘要。
4. 家长端逐条管理数据。
5. 孩子端显式“忘掉这个”入口。
6. 原始语音。
7. 原始照片。
8. 原始聊天全文。
9. 孩子原始回答。
10. 错误答案、分数、等级、排名。
11. 作业 / 学习内容。
12. 隐私、学校、住址、电话、真实姓名、证件、人脸、医疗信息。
```

---

## 12. opening 召回是否只做低频

是。

M1 opening 召回原则：

```text
1. 每个 ChatViewModel 生命周期最多一次。
2. 不是每次打开都必须出现。
3. 奇怪小门进行中不触发普通 opening 轻记忆。
4. 高风险、安全、隐私、学习、睡前场景不触发。
5. 孩子选择先聊别的、换题、短答或跳过后，本生命周期不再提。
```

M1 不写最终 opening 文案，只预留状态和决策点。

---

## 13. 普通聊天是否只在孩子主动相关时接住

是。

普通聊天中只允许在孩子主动提到以下内容时接住：

```text
1. 小门。
2. 小展台。
3. 某个小发现。
4. 刚才帮小白狐的东西。
```

不允许：

```text
1. 孩子说新话题时强拉回旧小发现。
2. 孩子短答后继续追问。
3. 孩子负面情绪中召回娱乐记忆。
4. 睡前召回兴奋玩法。
```

---

## 14. 奇怪小门是否可读取最近小展台小发现

可以。

M1 可规划：

```text
1. 奇怪小门 PhotoPrompt 继续复用 S5 “用小展台里的”路径。
2. 可读取最近一个安全小展台 item 名称作为本地轻状态候选。
3. 可记录某个小展台 item 本生命周期内回来帮过门。
```

M1 不做：

```text
1. 不改 S5 选择页行为。
2. 不改小展台 item 数据模型。
3. 不新增小展台副本。
4. 不写入历史。
5. 不做图鉴、背包、等级、稀有度。
```

---

## 15. 小展台是否不新增复杂记忆 UI

是。

M1 小展台只允许作为既有数据来源。

禁止：

```text
1. 新增记忆列表。
2. 新增分类。
3. 新增图鉴。
4. 新增回忆墙。
5. 新增成就。
6. 新增删除 / 收起 UI。
7. 新增复杂家长管理入口。
```

---

## 16. 语言游戏偏好是否暂缓实现

是。

M1 暂缓：

```text
1. 最近常玩哪个语言游戏。
2. 语言游戏偏好排序。
3. “上次那个游戏”的自动路由。
4. 语言游戏轻记忆写入。
```

保留原因：

```text
语言游戏偏好容易滑向成绩化或练习感。
M1 先只接奇怪小门和小展台这两个更低风险来源。
```

---

## 17. 家长端是否暂缓实现

是。

M1 不实现：

```text
1. 家长端轻记忆开关。
2. 家长端清除全部。
3. 家长端逐条列表。
4. 家长日报轻记忆项。
5. 家长端语言游戏偏好展示。
```

可以规划但不实现：

```text
1. 后续家长端轻记忆开关。
2. 后续家长端清除全部。
3. 后续后端白名单轻摘要。
```

---

## 18. public repo 数据扫描规则如何补

M1 计划应补一组文档和检查项，不要求本轮实现脚本。

建议扫描目标：

```text
1. `.env`
2. API key / token / production credential
3. 原始儿童音频
4. 原始儿童照片
5. 私有截图
6. 原始聊天转录
7. prompt trace
8. 本地数据库
9. 模型权重
10. TTS cache
11. 真实学校、住址、电话、证件、人脸
12. 家庭测试材料
```

建议落点：

```text
1. M1 交接文档列出 public repo 数据扫描清单。
2. 后续单独任务可评估是否新增脚本。
3. 真机截图 / 录屏如需入库，必须使用测试账号、测试素材、无真实儿童隐私内容。
```

---

## 19. 真机验收清单如何补

M1 真机验收建议新增：

```text
1. 奇怪小门完成后，本地轻状态可记录完成摘要。
2. 拍照 blocked / privacy / homework 不进入轻状态。
3. 小展台保存成功后，本地轻状态可读取小发现名称。
4. 用小展台小发现帮门后，本地轻状态可记录“回来帮过门”。
5. opening 轻记忆每生命周期最多出现一次。
6. 孩子选择先聊别的后，本生命周期不再提轻记忆。
7. 普通聊天只有孩子主动提小门 / 小展台 / 小发现时才接住。
8. 语言游戏过程不写入轻记忆。
9. 家长端没有新增轻记忆入口或报告项。
10. 日志和仓库不包含真实儿童照片、音频、聊天转录或家庭测试材料。
```

验收重点：

```text
孩子是否觉得小白狐轻轻记得一点点；
而不是被系统追踪、复盘或催促继续。
```

---

## 20. 会修改哪些文件

本轮修改：

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/session_process/handoffs/20260612_M0A_light_memory_decision_and_M1_boundary_plan.md
```

---

## 21. 不会修改哪些文件

本轮不修改：

```text
android/
backend/
release/
docs/session_process/handoffs/20260609_LG1_brain_teaser_handoff.md
docs/session_process/handoffs/20260609_LG2_word_chain_handoff.md
docs/session_process/handoffs/20260609_LG3_riddle_handoff.md
docs/session_process/handoffs/20260609_LG_review_language_game_suite_handoff.md
docs/session_process/handoffs/20260608_S5_showcase_item_back_to_door_handoff.md
题库
词库
素材
家长端代码
```

---

## 22. 需要主控确认的问题

```text
1. M1 是否按本文边界启动“本地轻状态与数据合同计划”。
2. M1 是否完全不触碰后端，即使 opening 低频召回暂时只能在本生命周期内验证。
3. M1 是否允许读取既有小展台 item 的 id、name、createdAt、foxQuote，还是只允许读取 name。
4. M1 是否需要同时更新 CODEX_PROGRESS_BOARD，标记当前阶段进入轻记忆 M1。
5. public repo 数据扫描是否需要在 M1 作为脚本实现，还是先作为清单进入交接。
6. opening 轻记忆最终儿童端文案由哪个 master-copy 文档承接。
7. 如果 M1 需要任何儿童端可见文本，是否由主控先提供精确文案。
```

---

## 23. 本轮测试与校验

本轮只改文档，计划运行：

```bash
git diff --check -- docs/PRODUCT_DECISIONS_V0_1.md docs/session_process/handoffs/20260612_M0A_light_memory_decision_and_M1_boundary_plan.md
```

不运行 Android / 后端测试，因为本轮不改代码。
