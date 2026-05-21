# Universal Image Sharing Design v0.1

用途：把“拍题目”升级为“拍给小白狐看”的通用图片分享能力。作业题仍然支持，但只是图片能力的一个分支。

---

## 1. 产品原则

孩子可以拍任何东西给小白狐：

```text
玩具
画
书
昆虫
植物
作业
手工
生活中看到的东西
```

系统先判断孩子意图：

```text
1. 这是想分享吗？
2. 这是想问“这是什么”吗？
3. 这是想让小白狐讲故事吗？
4. 这是学习 / 作业题吗？
5. 是否含隐私或安全风险？
```

---

## 2. Image Intent

第一版后端可先 mock，不接真实视觉模型。

```text
share
ask_what_is_this
tell_story
learning_homework
reading_text
art_feedback
privacy_sensitive
unsafe_unknown
```

---

## 3. API 兼容策略

保留旧 `homework_photo` 语义，但新增通用字段：

```json
{
  "attachment_type": "image",
  "image_purpose": "share",
  "mock_vision_text": "孩子说这是他搭的积木城堡",
  "child_caption": "你看我搭的这个"
}
```

作业题可以使用：

```json
{
  "attachment_type": "image",
  "image_purpose": "learning_homework",
  "mock_ocr_text": "题目文字",
  "mock_vision_text": "题目文字"
}
```

---

## 4. Android v1

```text
1. 入口文案从“拍题目”升级为“拍给小白狐看”。
2. mock dialog 支持“分享给小白狐”和“这是作业题”两个分支。
3. 普通分享走 conversation.open。
4. 作业题走 learning.homework_help。
5. 隐私敏感图片描述走 privacy.boundary。
6. 普通分享成功后暂存 pendingImageContext，后续快捷动作带上 attachment_id 和图片摘要。
```

---

## 5. 安全和数据

```text
1. v1 不接真实 CameraX，不保存真实照片。
2. 不把原始照片写入长期记忆。
3. 图片描述含地址、电话、学校名等隐私时，先进入 privacy.boundary。
4. 作业题仍遵守“不直接给最终答案”。
5. 后续真实视觉模型必须走模型外发和图片数据策略闸门。
```

---

## 6. 验收

```text
孩子拍玩具 -> 自然观察和聊天，不进入 homework_help。
孩子拍画 -> 先鼓励观察，不评分、不批评。
孩子拍题目 -> 进入 learning.homework_help。
孩子拍含地址/电话/学校名的图片描述 -> privacy.boundary。
普通图片后续点击“聊聊它 / 编个故事 / 问这是什么” -> conversation.open 且围绕刚才图片继续。
拍照失败或后端失败 -> network_error，不崩溃。
```

---

## 7. 第二轮收口：图片上下文连续性

已落实规则：

```text
1. Android 暂存普通图片 pendingImageContext，包括 attachment_id、图片摘要、image_purpose 和 recognized_type。
2. 后续“聊聊它 / 编个故事 / 问这是什么”会把图片摘要写入本轮文本，并携带 attachments=[attachment_id]。
3. 后端 AttachmentService 提供 get_image_context，ConversationService 会把 image_context 传入 ChildAgentRuntime 和 PromptManager。
4. Prompt 中会说明孩子刚刚分享了一张图片、图片描述和孩子说明；如果不是作业题，不把它当成作业。
5. 隐私图片的后续追问仍进入 privacy.boundary。
6. 不保存原始照片；只使用 mock 识别摘要和孩子说明。
```
