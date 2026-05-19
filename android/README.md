# Android 平板端

本目录是儿童 AI 成长智能体的 Android 平板端。当前阶段已在 S11 / A1 静态壳和 S12 / A2 Conversation API 基础上接入 S13 / A3-A4 演示闭环。

## 当前范围

- 单一儿童聊天入口。
- 静态小狐狸智能体形象占位。
- 文本输入框和发送按钮。
- 调用后端 `POST /api/v1/conversation/message`。
- 渲染后端返回的 `reply.text`、`ui_actions` 快捷按钮和 `session_state`。
- 点击“拍题目”走 mock attachment 流程，不接真实 CameraX，不保存真实图片。
- 父亲设置页可读取和保存目标、沟通偏好、放学后/作业/睡前时间段。
- 父亲日报页读取后端 `GET /api/v1/parent/reports/{child_id}` 只读摘要。
- 使用内存保存当前 `session_id` 和最新 `session_state`。

## 当前不做

- 不接真实相机、语音或 TTS。
- 不长期保存真实图片；拍题流程只发送 mock OCR 文本和 mock metadata。
- 不做账号系统。
- 不在 Android 端放任何模型 API key。
- 不在客户端实现 AI 决策。
- 不在客户端做安全分类、意图识别或场景路由。
- 不展示孩子完整逐字聊天记录。

## 后端配置

默认开发 base URL 是 Android Emulator 访问宿主机的地址：

```text
http://10.0.2.2:8000/
```

如需改成真机或其他地址，可以在 Gradle 命令中传入：

```bash
cd android
./gradlew assembleDebug -PconversationApiBaseUrl=http://192.168.1.10:8000/
```

本地开发使用 HTTP 明文访问后端；不要在 Android 端写入任何模型 API key 或真实 secret。

## 本地运行

需要本机安装 JDK 17 和 Android SDK，并设置 Android SDK 路径，例如：

```bash
export ANDROID_HOME="$HOME/Library/Android/sdk"
```

构建：

```bash
cd android
./gradlew assembleDebug
```

单元测试：

```bash
cd android
./gradlew test
```

## 手动联调

先从仓库根目录启动后端：

```bash
bash scripts/dev_backend.sh
```

再安装运行 Android debug 包。验证路径：

```text
1. 输入“我回来了”，页面应追加孩子消息和后端回复。
2. 输入“我有一道题不会”，页面应显示“拍题目”“读题目”等快捷按钮。
3. 点击“拍题目”，保留默认 mock 题目或编辑题目文字，然后点击“发送题目”。
4. 页面应通过 /conversation/attachment 创建 attachment，再通过 /conversation/message 携带 attachment_id。
5. 页面应显示后端返回的题意引导，例如先问“这道题是在问什么”，不显示最终答案。
6. 点击“父亲设置”，读取当前 policy，修改目标、沟通偏好或时间段，保存后应显示成功提示。
7. 回到聊天页再发送消息，后端应使用更新后的 parent policy。
8. 点击“父亲日报”，读取当天 summary；如果当天没有结构化记忆，后端会返回“暂无可汇总的结构化会话素材”类摘要。
9. 页面底部应显示后端返回的 session_state。
10. 断开后端时，页面应显示温和错误，提示请大人检查网络。
```

## 父亲日报说明

后端当前已提供父亲日报 API：

```text
GET /api/v1/parent/reports/{child_id}?date=YYYY-MM-DD
```

Android 端按只读页展示后端 summary、学习观察、表达观察、情绪/社交观察、建议父亲动作和需要关注事项。该页不展示 evidence、quote_summary 或孩子完整逐字聊天记录。当前后端日报素材来自内存态结构化 memory；如果重启后端或当天没有 memory，日报会显示空摘要，这不是 Android stub。
