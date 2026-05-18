# Android 平板端

本目录是儿童 AI 成长智能体的 Android 平板端。当前阶段已在 S11 / A1 静态壳基础上接入 S12 / A2 Conversation API。

## 当前范围

- 单一儿童聊天入口。
- 静态小狐狸智能体形象占位。
- 文本输入框和发送按钮。
- 调用后端 `POST /api/v1/conversation/message`。
- 渲染后端返回的 `reply.text`、`ui_actions` 快捷按钮和 `session_state`。
- 使用内存保存当前 `session_id` 和最新 `session_state`。

## 当前不做

- 不接真实相机、语音或 TTS。
- 不做账号系统。
- 不在 Android 端放任何模型 API key。
- 不在客户端实现 AI 决策。
- 不在客户端做安全分类、意图识别或场景路由。

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
3. 页面底部应显示后端返回的 session_state。
4. 断开后端时，页面应显示温和错误，提示请大人检查网络。
```
