# S2：我的小展台列表与详情交接

日期：2026-06-06

执行角色：开发执行会话

任务范围：让孩子点开“小展台”后，可以看到以前放进去的所有东西，并查看单个展品详情；只做只读列表与详情，不改奇怪小门拍照、怪问题、门状态节奏，不改后端。

---

## 1. 本轮结论

S2 已完成代码侧实现。

已按主控确认后的边界落地：

```text
1. 使用现有 AppNavHost 全屏页面导航，不做弹窗或底部面板。
2. 列表页和详情页顶栏均使用“我的小展台”。
3. 详情页不新增单独详情标题，页面主体显示展品名字。
4. “和小白狐再聊聊它”入口已从 S2 UI 隐藏。
5. 删除 / 收起入口已从 S2 UI 隐藏，底层 softDelete 能力暂时保留。
6. 列表保存时间沿用 `M月d日` / `刚刚` 格式。
7. 图片加载失败不显示新增兜底文案；图片区域只保留无文字的轻量视觉占位。
```

---

## 2. 修改文件

修改：

```text
android/app/src/main/java/com/childai/companion/ui/AppNavHost.kt
android/app/src/main/java/com/childai/companion/ui/showcase/XiaozhantaiScreens.kt
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

新增：

```text
android/app/src/test/java/com/childai/companion/ui/showcase/XiaozhantaiGalleryContractTest.kt
docs/session_process/handoffs/20260606_S2_xiaozhantai_gallery_handoff.md
```

未修改：

```text
backend/
android/app/src/main/java/com/childai/companion/data/showcase/
android/app/src/main/java/com/childai/companion/data/growth/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/
android/app/src/main/java/com/childai/companion/ui/parent/
android/app/src/main/res/drawable-nodpi/
```

---

## 3. 行为变化

儿童端可见变化：

```text
1. 首页“小展台”入口继续保留。
2. 点开后进入“我的小展台”列表页。
3. 有展品时，每个展品显示图片缩略图、名字和保存时间。
4. 没有展品时显示：
   这里还空空的
   等你和小白狐放进一个小发现
5. 点开展品进入详情页。
6. 详情页显示大图、名字、“小白狐那时说”和保存时的 foxQuote。
7. 详情页关闭返回列表页，列表页关闭返回儿童首页。
```

已隐藏：

```text
1. “和小白狐再聊聊它”入口。
2. 删除 / 收起入口。
3. 删除确认弹窗。
4. 图片加载失败专门兜底文案。
```

---

## 4. 安全和边界

已保持：

```text
1. 不新增删除。
2. 不新增分类。
3. 不新增搜索。
4. 不新增百宝箱复杂系统。
5. 不新增收藏图鉴。
6. 不新增奖励、积分、等级。
7. 不新增任务、打卡。
8. 不新增家长端功能。
9. 不提交真实儿童照片、截图、音频、转录或隐私材料。
10. 不因为 public repo 包装改儿童端产品方向。
```

奇怪小门边界：

```text
1. 不改 D3 拍照路径。
2. 不改 D4 怪问题路径。
3. 不改 D5 小展台保存流程。
4. 不改 R1-A 门状态节奏。
5. 不改 R1-B 拍照结果视觉。
6. 不继续修改 R1-C 首屏视觉。
```

---

## 5. 测试结果

已通过：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.showcase.XiaozhantaiGalleryContractTest' --tests 'com.childai.companion.data.showcase.*' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh assembleDebug
```

覆盖：

```text
1. S2 儿童端文本使用主控确认文本。
2. 列表卡模型包含图片引用、名字和保存时间。
3. 详情模型包含大图引用、名字和小白狐当时的话。
4. S2 文案不包含删除、搜索、分类、百宝箱、图鉴、背包、奖励、积分、等级、任务、打卡等表达。
5. data.showcase 现有测试继续通过。
6. D3 / D4 / D5 / strangedoor 相关回归继续通过。
7. Android assembleDebug 通过。
```

---

## 6. 截图 / 录屏

本轮未产出截图或录屏。

原因：

```text
当前没有真机测试条件；doctor_local_env 显示 adb devices WARN：没有连接真机。
```

---

## 7. 风险点

```text
1. 本轮未做真机视觉验收，列表与详情在 Redmi K60 / Honor Pad 5 上仍需合并真机测试确认。
2. 单个图片加载失败当前为无文字视觉占位，不新增儿童端兜底文案；如果主控希望完全隐藏该展品，后续需要补充实现规则。
3. 底层 softDelete 和 recall 能力仍保留，只是 S2 UI 不暴露；后续如果要彻底下线，需要单独任务确认。
4. 详情页不显示保存时间，符合本轮范围；如果后续需要展示，需要主控补充确认。
```

---

## 8. 是否可进入下一步

结论：

```text
可以进入后续合并真机测试或下一个已确认功能任务。
```

合并真机测试建议关注：

```text
1. 小展台入口是否仍是弱入口，不抢奇怪小门主玩法。
2. 列表中缩略图、名字、时间是否清楚且不拥挤。
3. 详情大图和“小白狐那时说”是否足够清楚。
4. 图片缺失或加载失败时是否不会出现未经确认的儿童端文案。
5. 是否没有删除、分类、搜索、奖励、积分、任务、打卡等表达。
```
