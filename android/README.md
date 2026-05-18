# Android 壳项目

本目录是儿童 AI 成长智能体的 Android 平板端壳项目。当前阶段对应 S11 / A1，只实现 Kotlin + Jetpack Compose 静态聊天入口。

## 当前范围

- 单一儿童聊天入口。
- 静态小狐狸智能体形象占位。
- 消息列表占位。
- 文本输入框和发送按钮。
- 本地内存 UI 状态。

## 当前不做

- 不接真实后端 API。
- 不接真实相机、语音或 TTS。
- 不做账号系统。
- 不在 Android 端放任何模型 API key。
- 不在客户端实现 AI 决策。

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

## 后续衔接

后续 Android API 接入会话应通过统一 Conversation API 接入后端，客户端只负责展示、输入和轻量状态，不在本地绕过后端安全、意图识别或场景编排。
