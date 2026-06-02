# E6 阻塞修复交接

状态：CONDITIONAL

更新时间：2026-06-02

---

## Summary

本轮按 E6-BLOCKER-FIX 只修了 5 个阻塞问题，没有新增玩法、没有改家长端边界、没有重写 prompt。后端图片成功合同已收口为确定性三行文案 + 单一 `companion_name` 按钮；Android 端已统一上报 `companion_name`，并保留 `give_name` 兼容别名进入同一创建链路；真实数据库已完成 `visual_kind` 迁移，`doctor` 和 `smoke` 会直接检查该列是否存在；`加一个朋友` 的流式与非流式链路都已收口到 E5 三按钮引导；Honor Pad 5 的相册入口已降级隐藏，只保留稳定的拍照路径。

本轮真机补充验证了 4 件关键事实：第一，Honor Pad 5 上当前调试包已经升级到本地最新 APK；第二，召回 opening 可以稳定出现，且点击 `加一个朋友` 后现在能在真机上看到 `说个名字 / 给小白狐看看 / 先聊别的` 三按钮；第三，Honor Pad 5 的图片入口现在只显示 `拍一张照片` 和 `先不看`，不会再跳到异常系统相册页；第四，真实拍照上传确实命中 `/api/v1/attachments/images`，图片失败时能落到 `这张图还没看到 / 可以再试一次，也可以先不看` 的失败合同。

还保留一个验收缺口：本轮在无人值守的 Honor Pad 5 实拍环境里，连续两次相机实拍都落到了失败分支，没有在真机屏幕上稳定截到“图片成功 -> 起个名字”这一帧；但我使用同一台 Honor Pad 5 当前登录 token，直接对运行中的真实 `multipart` `/api/v1/attachments/images` 复打了一次请求，返回体已经明确是 V0.2 要求的 `companion_name` 单按钮合同。因此本轮结论不是 `BLOCKED`，但也不写成 `PASS`，保持 `CONDITIONAL` 更准确。

---

## 1. 根因与对应修复

### 阻塞 1：图片成功后的真实后端合同仍是旧逻辑

根因：

```text
1. 后端真实运行链路仍可能落在旧进程上，真机 QA 时实际返回了旧文案和旧按钮集合。
2. Android 端虽然会过滤部分旧按钮，但不能替代后端合同收口。
3. 真实 multipart 路径必须直接验证，而不是只看测试替身。
```

修复：

```text
1. 重新确认并使用当前 main 的 ModalityManager 成功路径。
2. 用同一台 Honor Pad 5 当前登录 token 直接复打真实 multipart /api/v1/attachments/images。
3. 补测试，锁定成功路径只允许 companion_name。
```

当前真实合同证据：

`[20260602_live_attachment_success_contract.json](/Users/wzy/Documents/儿童ai陪伴软件开发/docs/session_process/handoffs/e6_screenshots/20260602_live_attachment_success_contract.json)`

返回关键信息：

```json
{
  "reply_text": "我看到图片显示手机相机应用界面啦\n像软软的\n要不要给它起个名字？",
  "ui_actions": [
    {
      "actions": [
        {
          "id": "companion_name",
          "label": "起个名字"
        }
      ]
    }
  ]
}
```

### 阻塞 2：Android 点击“起个名字”发 give_name，后端吃 companion_name

根因：

```text
1. Android 端仍会把 legacy image action 映射成 give_name / image_naming。
2. 后端 seed 创建主链路识别的是 companion_name。
3. 流式和非流式路径都需要统一，不然会出现某些路径能起名、某些路径回普通对话。
```

修复：

```text
1. Android 端统一用 normalizedQuickActionId() 把 give_name / image_naming 收口到 companion_name。
2. continuePendingImageConversation() 改为上报 companion_name。
3. 后端保留 give_name 兼容别名，但兼容别名进入同一 seed 创建链路。
4. 补测试锁住主路径和兼容路径。
```

### 阻塞 3：真实数据库缺 visual_kind 列

根因：

```text
1. 真实联调库没有跑到 20260601_0008 migration。
2. 仓库代码已依赖 visual_kind 持久化，但数据库 schema 仍旧。
3. 这会让 companion_objects 回退到进程内语义，后端重启后 recall 不可靠。
```

修复：

```text
1. 执行 Alembic migration 到 head，确认 20260601_0008 已落库。
2. scripts/doctor_local_env.sh 新增 companion_objects.visual_kind 检查。
3. scripts/smoke_db_persistence.sh 新增 schema 断言。
4. 补数据库持久化测试，验证 create 后服务重启仍可 recall。
```

本轮再次验证：

```text
bash scripts/db_migrate.sh -> 已包含 20260601_0008
bash scripts/smoke_db_persistence.sh -> PASS
bash scripts/doctor_local_env.sh -> companion_objects.visual_kind present
```

### 阻塞 4：“加一个朋友”没有进入 E5 三按钮引导

根因：

```text
1. 流式 route payload 之前没有把 quick_actions 带到 Android。
2. Android 的 quick action 过滤把 companion_skip 当成 opening-only 动作，co_create guidance 下被误隐藏。
3. 真机上结果是“说个名字 / 给小白狐看看”能出来，但“先聊别的”被 UI 层吞掉。
```

修复：

```text
1. 后端 stream route payload 补 quick_actions。
2. ChatViewModel.applyStreamRoute() 写入 quickActions。
3. ChildChatScreen 在 co_create guidance 下放行 companion_skip。
4. 补 Android 单测，锁定三按钮都可见。
```

Honor Pad 5 修复后证据：

`[20260602_honor_add_friend_guidance_fixed.png](/Users/wzy/Documents/儿童ai陪伴软件开发/docs/session_process/handoffs/e6_screenshots/20260602_honor_add_friend_guidance_fixed.png)`

### 阻塞 5：Honor Pad 5 相册入口异常

根因：

```text
1. Honor Pad 5 上相册选择会被系统劫到异常页面，不适合作为儿童主入口。
2. 当前目标是保证孩子不会点进异常系统页，而不是强行维持一个不稳定相册入口。
```

修复：

```text
1. Honor Pad 5 指纹下隐藏 gallery picker。
2. 只保留拍照路径和“先不看”降级。
3. 继续保留拍照主路径可用。
```

Honor Pad 5 修复后证据：

`[20260602_honor_image_entry_camera_only.png](/Users/wzy/Documents/儿童ai陪伴软件开发/docs/session_process/handoffs/e6_screenshots/20260602_honor_image_entry_camera_only.png)`

---

## 2. 修改文件

Android：

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt
android/app/src/test/java/com/childai/companion/ui/ChatViewModelStreamTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/AgentReplyCarouselTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/ChatViewModelOpeningTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/InputBarVoiceFirstTest.kt
```

后端：

```text
backend/app/services/conversation_service.py
backend/app/services/conversation_stream_service.py
backend/app/tests/test_attachment_api.py
backend/app/tests/test_companion_object_runtime.py
backend/app/tests/test_conversation_stream_api.py
backend/app/tests/test_companion_object_sql_repository.py
```

脚本：

```text
scripts/doctor_local_env.sh
scripts/smoke_db_persistence.sh
```

文档与证据：

```text
docs/session_process/handoffs/20260602_E6_blocker_fix_handoff.md
docs/session_process/handoffs/e6_screenshots/20260602_*.png
docs/session_process/handoffs/e6_screenshots/20260602_live_attachment_success_contract.json
```

---

## 3. 测试与验证

### 自动化测试

后端：

```text
conda run -n child-ai pytest \
  backend/app/tests/test_attachment_api.py::test_image_upload_endpoint_returns_only_companion_name_on_success \
  backend/app/tests/test_companion_object_runtime.py::TestCompanionSeedNaming::test_legacy_give_name_alias_enters_same_seed_creation_chain \
  backend/app/tests/test_conversation_stream_api.py::test_stream_route_payload_matches_non_stream_companion_continue_actions \
  backend/app/tests/test_companion_object_sql_repository.py -q

结果：5 passed
```

Android：

```text
bash scripts/android_gradle.sh testDebugUnitTest \
  --tests com.childai.companion.ui.chat.AgentReplyCarouselTest \
  --tests com.childai.companion.ui.chat.ChatViewModelOpeningTest \
  --tests com.childai.companion.ui.ChatViewModelStreamTest.routeDecisionCarriesQuickActionsIntoUiState \
  --tests com.childai.companion.ui.chat.InputBarVoiceFirstTest

结果：BUILD SUCCESSFUL
```

构建：

```text
bash scripts/android_gradle.sh assembleDebug

结果：BUILD SUCCESSFUL
```

数据库与环境：

```text
bash scripts/db_migrate.sh
bash scripts/smoke_db_persistence.sh
bash scripts/doctor_local_env.sh

结果：
- visual_kind migration 已落库
- DB_PERSISTENCE_SMOKE: PASS
- doctor 显示 companion_objects.visual_kind present
```

### 真机验证

设备：

```text
Honor Pad 5
设备号：E8X9X20921002020
```

本轮真机已确认：

```text
1. 最新调试包已成功安装到 Honor Pad 5。
2. recall opening 可出现：宝石今天在窗边呢 / 加一个朋友 / 先聊别的。
3. 点击加一个朋友后，真机当前可见三按钮：说个名字 / 给小白狐看看 / 先聊别的。
4. 图片入口在 Honor Pad 5 上已降级为“拍一张照片 / 先不看”，不再出现相册异常入口。
5. 真拍照上传确实命中 /api/v1/attachments/images。
6. 图片失败时真机会显示：这张图还没看到 / 可以再试一次，也可以先不看。
7. 用同一设备当前登录 token 对真实 multipart /api/v1/attachments/images 复打请求，成功合同只返回 companion_name。
```

本轮真机仍未补齐：

```text
1. Redmi K60 未接入，手机端未补测。
2. Honor Pad 5 实拍环境下，本轮没有稳定截到“图片成功 -> 起个名字”这一帧屏幕；成功合同用同设备 token 的真实 multipart 请求补证。
```

---

## 4. 截图与证据路径

真机截图：

```text
docs/session_process/handoffs/e6_screenshots/20260602_honor_recall_opening.png
docs/session_process/handoffs/e6_screenshots/20260602_honor_add_friend_guidance_fixed.png
docs/session_process/handoffs/e6_screenshots/20260602_honor_image_entry_camera_only.png
docs/session_process/handoffs/e6_screenshots/20260602_honor_image_upload_processing.png
docs/session_process/handoffs/e6_screenshots/20260602_honor_image_failure_fallback.png
```

真实接口合同证据：

```text
docs/session_process/handoffs/e6_screenshots/20260602_live_attachment_success_contract.json
```

说明：

```text
本轮无新增录屏文件，只有真机截图和真实接口返回体证据。
```

---

## 5. 结论

结论分层如下：

```text
1. 代码层：5 个 blocker 已完成修复。
2. 自动化层：新增/修复的关键测试均通过。
3. 数据层：visual_kind 已真实落库，重启后 recall 能继续工作。
4. Honor Pad 5 真机层：add-friend 三按钮与图片入口降级已真实通过。
5. 验收层：由于本轮未在 Honor Pad 5 实拍环境里稳定截到“图片成功 -> 起个名字”的屏幕帧，所以整体状态写 CONDITIONAL，不写 PASS。
```

如果主控只关注“这 5 个 blocker 代码是否已收口”，答案是：`是`。  
如果主控要求“手机和平板都补完成功/失败两条真机链路并留全量屏幕证据”，那还需要再补一轮 Redmi K60 和 Honor 成功分支截图。
