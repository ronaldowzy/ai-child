# Freedom-First Interaction Design v0.1

用途：定义下一阶段交互底座。小白狐默认与孩子自由交流；场景、时间、图片、记忆和家长寄语是上下文或能力，安全、隐私和学习边界是护栏。

---

## 1. 核心原则

```text
默认进入 conversation.open 自由对话。
时间、家长寄语、记忆、最近聊天和设备状态作为上下文注入。
只有明确触发时才进入强约束场景。
```

强约束场景只包括：

```text
1. 高风险安全。
2. 隐私边界。
3. 明确学习 / 作业求助。
4. 明确睡前低刺激收尾。
5. 父母明确设置且不违反儿童安全底线的强规则。
```

以下概念不再作为默认硬入口：

```text
after_school
homework
bedtime
photo
```

它们应被理解为：

```text
上下文
线索
能力
提醒
```

---

## 2. 时间上下文

时间段只影响语气和轻量提醒：

```text
放学后：轻松、低压力，不强迫汇报学校。
作业时间：只有孩子提到学习或作业时才温和衔接。
睡前：短句、低刺激；只有孩子明确说晚安、困了或要睡觉时才进入睡前收尾。
```

验收：

```text
after_school + “我想聊恐龙” -> conversation.open
bedtime + “我想给你看我的积木” -> conversation.open + 低刺激上下文
“晚安” / “我困了” -> daily.bedtime_reflection
“我回来了” -> 轻量问候，不强制菜单式选项
```

---

## 3. 家长寄语

家长寄语是模型理解孩子的背景，不是直接复述给孩子的内容。

Prompt 规则：

```text
1. 不直接说“你爸爸说你……”。
2. 负面标签必须转化为支持性表达。
3. 小名可以自然少量使用。
4. 家长希望应通过低压力方式引导。
5. 安全底线优先于家长寄语。
6. 不能把家长寄语用于套话、监控或诱导孩子透露隐私。
```

---

## 4. 安全边界

自由对话不等于无限制聊天。以下边界保持硬约束：

```text
1. 高风险安全优先。
2. 隐私边界优先。
3. 作业不直接给最终答案。
4. 不鼓励隐瞒父母。
5. 不制造“只有小白狐懂你”的依赖。
6. 不保存原始音频和原始照片。
7. 家长寄语不能覆盖儿童安全底线。
```

---

## 5. 实施阶段

```text
1. 文档和 Prompt 层先完成 freedom-first 设计。
2. ParentPolicy 增加 parent_message_raw。
3. SceneOrchestrator 默认回到 conversation.open。
4. Attachment 从 homework-only 扩展为通用 image sharing。
5. Android 家长设置和 mock 图片入口跟进。
6. 最后做自由对话、安全、隐私和学习边界回归测试。
```

## 6. 第二轮收口规则

已落实的收口规则：

```text
1. 学习意图不再由单独“题”或“不会”触发。
2. “我不会画这个小怪兽”“游戏里有一道谜题”“我想出一个问题考你”保持 conversation.open。
3. “我有一道题不会”“这道题怎么做”“帮我看看作业”“数学题不会”“练习册”等明确学习 / 作业表达才进入 learning.homework_help。
4. 普通图片分享后，后续“聊聊它 / 编个故事 / 问这是什么”会带上 attachment_id 和图片摘要进入对话上下文。
5. 家长寄语优先写入 PostgreSQL parent_policies；本地数据库不可用时 dev 模式回退内存。
6. 家长寄语仍不会出现在儿童端 debug 或 UI 中。
7. child_chat prompt 和 runtime 已接入 age_band thin slice：从父亲沟通偏好里的 `age_band`、`child_age` 或 `age` 派生 age_5_6 / age_7_8 / age_9_10 / unknown，默认 age_7_8，并把 `reply_char_budget` 和 `question_policy` 作为内部提示注入。
8. 开放对话已接入连续追问 thin slice：最近多轮都是小白狐提问、孩子说“换个话题 / 不聊了 / 睡觉了”，或孩子纠正“不是 / 你说错了 / 我还没跑”时，本轮不新增追问钩子，优先尊重边界或修正理解。
9. Task 06 后，家长设置中的年龄、可选年级、称呼偏好、兴趣和近期不想被追问的话题会进入 child_profile / turn guidance；显性作息配置从 v0.1 家庭内测 UI 降级，时间仍只做语气和轻量提醒。
10. 同一普通话题持续多轮且孩子回复变短或变平时，`TurnGuidanceBuilder` 会标记 `topic_shift_recommended` 并提供静态 curated topic seeds；小白狐应给换题机会，不继续深挖旧话题。
11. Task 07 后，topic seeds 升级为 reviewed / age-aware / expiring seed objects，每条包含 `id`、`label`、`age_bands`、`prompt_hint`、`safety_notes`、`expires_at` 和 `source`。Android 只在 Ready/Resting 等空闲状态展示轻量“换个轻松话题”chips，且不抓实时热点、不做任务菜单、不鼓励继续游戏。
12. Task 09 后，普通话题 continuation/shift 以模型 `conversation_control` 语义判断为主，程序规则保留 safety、privacy、bedtime、explicit boundary、fallback 和 metrics；高参与孩子可以继续当前话题，短答/低能量时可自然 soft_shift。
13. Task 09 后，topic choices 由后端基于账号画像、兴趣、topic boundaries、curated seeds 和 `conversation_control` 生成；Android 不再独立硬编码固定话题 chips。
14. 产品术语默认使用“家长”；历史 `Parent*` 代码命名暂保留，UI、QA 和面向家庭的文案避免继续写“家长设置/家长日报”。
```
