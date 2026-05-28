# 普通对话 Prompt Fast Path 窄修开发启动 v0.1

项目：`ai-child`

用途：作为“普通对话 Prompt Fast Path 窄修”的开发启动文档。本文用于指导开发端 A 对普通低风险开放聊天做 prompt 轻量化评估与最小实现，目标是降低无必要 system prompt 负担，不重写小白狐人格，不牺牲安全边界，不影响图片、学习、安全、隐私等复杂场景。

更新时间：2026-05-28

---

## 0. 主控判断

真机测试中发现：

```text
一次真实请求只有 13 字用户输入、26 字回复，但 system prompt 约 7603 字。
```

这不是孩子输入导致的，而是当前每轮普通对话都把完整 prompt 层重新拼入 system message。

当前 `PromptManager.compose(...)` 会固定拼接：

```text
global_system
persona
child_profile
parent_message
parent_policy
time_context
image_context
scene
turn_guidance
memory_context
output_contract
```

普通开放聊天也会带完整开放对话场景规则、轻共创规则、轻记忆规则、图片空上下文说明、完整输出契约等。

这件事需要改，但不能做成“开发端重写一版短提示词”。本轮只做：

```text
普通低风险开放聊天 fast path。
```

---

## 1. 本轮目标

目标：

```text
1. 量化 prompt 各层长度；
2. 只给低风险普通开放聊天启用 fast path；
3. 将普通低风险聊天 system prompt 控制到约 3000-4500 字符以内；
4. opening prompt 保持或优化到约 800-1200 字符以内；
5. 不影响安全、学习、图片、隐私、睡前、轻共创、轻记忆召回等场景；
6. 不重写小白狐人格；
7. 不让开发端自行设计儿童端新文案。
```

本轮成功不是“提示词越短越好”，而是：

```text
普通闲聊不再每轮携带全部重规则；
复杂场景仍然安全可靠；
prompt_total_chars 可观测、可解释、可回归。
```

---

## 2. Fast path 启用条件

只有同时满足以下条件，才能启用 fast path：

```text
1. active_scene == conversation.open；
2. risk_level == none；
3. 无图片附件；
4. 无 homework_context；
5. 无 privacy_sensitive image_context；
6. 当前不是 learning.homework_help；
7. 当前不是 safety.guardian / safety.gentle_checkin；
8. 当前不是 privacy.boundary；
9. 当前不是 bedtime 收尾；
10. memory_context 为空或没有本轮适合召回的内容；
11. turn_guidance 未触发轻共创；
12. child_text 不是明确学习求助、安全、隐私、图片、身体不舒服、家庭冲突等高敏输入。
```

如果任何条件不满足，必须走完整 prompt。

---

## 3. Fast path 应保留的最小规则

普通低风险聊天 fast path 必须保留：

```text
1. 小白狐身份：温和、好奇、低压的儿童陪伴者之一；
2. 不是老师、客服、心理医生、任务系统；
3. 默认 1-3 句，适合朗读；
4. 多数普通聊天可以不提问；
5. 如果提问，最多一个很小的问题；
6. 孩子短答、换题、不想聊时不深挖；
7. 尊重“换个话题 / 不聊了 / 睡觉了 / 一会再聊”；
8. 不制造依赖感或秘密关系；
9. 不使用积分、打卡、奖励、任务、排行榜、宠物饥饿；
10. 不输出 Markdown、列表、标题、代码块；
11. 如果识别到学习、安全、隐私、图片等复杂场景，不能靠 fast path 硬答，应走完整路由/完整 prompt。
```

---

## 4. Fast path 应裁剪或按需加载的内容

普通低风险聊天 fast path 不应每轮携带：

```text
1. 完整图片场景规则；
2. “当前没有图片上下文”这类图片空上下文段；
3. 完整轻共创故事接龙规则；
4. 完整轻记忆召回规则；
5. 完整学习帮助细则；
6. 完整安全场景长规则；
7. 完整图片作品隐私边界长规则；
8. 完整 JSON 输出契约长文本；
9. 家长寄语原文的长段落，除非本轮确实需要；
10. 空 memory_context 的长解释；
11. 空 image_context 的长解释。
```

---

## 5. 输出契约轻量版

普通聊天 fast path 可以使用轻量输出契约。

建议：

```json
{
  "reply": "给孩子看的短回复",
  "conversation_control": {
    "child_engagement": "high|medium|low|unclear",
    "topic_continuity": "continue|soft_shift|stop|unclear"
  }
}
```

要求：

```text
1. reply 是唯一给孩子看的文本；
2. conversation_control 是内部控制信息；
3. 如果模型没有稳定输出 JSON，仍必须能解析或降级拿到 reply；
4. 轻共创、图片、学习、安全、隐私场景不得使用这个轻量契约，应回完整契约。
```

---

## 6. 必须新增的观测

必须记录或返回 debug 指标：

```text
prompt_total_chars
system_prompt_chars
history_chars
user_chars
section_chars_by_layer
fast_path_used
fast_path_reason
fast_path_blocked_reason
prompt_template_mode
```

日志边界：

```text
1. 不记录儿童完整原文到长期日志；
2. 不记录完整 system prompt 到普通日志；
3. 可以记录长度、层名、hash、是否 fast path；
4. 测试环境可输出结构化统计，但不能把 API key、音频、图片、base64 写入日志。
```

---

## 7. 建议实现位置

优先评估：

```text
backend/app/services/prompt_manager.py
backend/app/services/child_agent_runtime.py
backend/app/services/conversation_service.py
backend/app/domain/prompt.py
backend/app/prompts/
backend/app/tests/
```

可选新增：

```text
backend/app/prompts/output_contracts/child_chat_fast_v0_1.txt
backend/app/prompts/scenes/conversation_open_fast_v0_1.txt
```

或通过代码分支组合现有文本，但必须可测试、可观测。

---

## 8. 回归样例

必须至少覆盖：

```text
1. 普通跑步聊天：我一会要去跑步了。
2. 普通运动延续：一块跳绳了，我们跳了很多。
3. 短答：都行吧。
4. 换话题：换个话题。
5. 学习求助：这道题怎么做？
6. 图片分享：带图片上下文。
7. 安全/隐私场景：陌生人让我保密 / 我不想告诉家长。
8. 睡前场景：我要睡觉了 / 晚安。
9. 轻共创触发场景。
10. 有 memory_context 的回访场景。
```

验收要求：

```text
1. 前 4 个低风险普通聊天可以启用 fast path；
2. 后 6 个复杂场景必须阻止 fast path，走完整 prompt；
3. 低风险普通聊天 prompt_total_chars 下降；
4. 输出仍短、低压、不追问、不任务化；
5. 学习、安全、隐私、图片规则没有被削弱。
```

---

## 9. 本轮不得做

```text
1. 不重写小白狐人格；
2. 不全局删除安全规则；
3. 不全局删除学习规则；
4. 不让所有场景共用短 prompt；
5. 不新增儿童端新文案；
6. 不修改家长日报；
7. 不改 Android UI；
8. 不改小白狐素材；
9. 不扩展轻共创；
10. 不新增长期记忆能力。
```

---

## 10. 执行流程要求

请先输出计划，不要直接改代码。

计划必须包含：

```text
1. 当前 prompt 是如何拼接的；
2. 预计哪些层占比最大；
3. fast path 启用条件；
4. 准备新增/修改哪些文件；
5. 明确不会修改哪些文件；
6. 如何保证复杂场景回完整 prompt；
7. 如何记录 prompt 分层长度；
8. 回归测试策略；
9. 是否需要主控确认。
```

完成后输出交接摘要，必须包含：

```text
Summary:
- 做了什么。

Files changed:
- 修改了哪些文件。

Prompt weight:
- fast_path_used 条件。
- 修改前后 prompt_total_chars 对比。
- section_chars_by_layer 示例。

Behavior:
- 普通聊天是否仍短、低压、不追问。
- 学习/安全/图片/隐私是否仍走完整 prompt。

Tests:
- 运行了哪些测试，结果如何。

Safety:
- 是否没有削弱儿童安全、隐私、学习不过度代答。

Known issues:
- 未完成事项或风险。

Commit:
- 远程主分支提交编号。
```
