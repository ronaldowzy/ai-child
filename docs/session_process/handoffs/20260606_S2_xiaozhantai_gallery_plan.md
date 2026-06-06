# S2：我的小展台列表与详情计划

日期：2026-06-06

执行角色：开发执行会话

任务状态：PLAN ONLY，不编码。

当前主控状态：

```text
1. Q2 奇怪小门 R1 真机视觉验收延期，后续与下一轮功能一起做合并真机测试。
2. R1-C：CODE PASS / 待真机视觉验收。
3. 暂停继续修改奇怪小门视觉，不继续调整门、小白狐位置、光效、按钮层级。
4. 本轮启动 S2：我的小展台列表与详情。
```

---

## 1. 本轮目标

让孩子点开首页已有“小展台”入口后，可以看到以前放进去的所有东西，并查看单个展品详情。

S2 只做小展台的只读列表与详情：

```text
1. 首页保留小展台入口。
2. 小展台页面展示所有已保存展品。
3. 每个展品显示图片缩略图、名字、保存时间。
4. 点开展品进入详情。
5. 详情显示大图、名字、小白狐当时的话。
6. 没有展品时显示空状态。
7. 复用现有小展台数据能力。
```

---

## 2. 当前代码现状

现有 Android 本地小展台能力已经可以支撑 S2：

```text
1. AppNavHost 已有 XiaozhantaiList 和 XiaozhantaiDetail 两个目的地。
2. ChildChatScreen 已有 onOpenXiaozhantai 入口，首页入口文案当前为“小展台”。
3. LocalXiaozhantaiRepository 已将展品元数据保存到 app 私有目录 items.json，并将照片保存到 app 私有 photos 目录。
4. XiaozhantaiRepository 已提供 observeItems(childId) 和 itemById(childId, itemId)。
5. XiaozhantaiItem 已包含 photoUri、name、foxQuote、createdAt，可支撑缩略图、名字、保存时间和详情展示。
6. XiaozhantaiScreens 已有列表和详情雏形，图片读取也已支持本地文件路径。
```

当前主要差距：

```text
1. 列表标题当前不是主控文本“我的小展台”。
2. 空状态当前不是主控提供的两行文本。
3. 详情小标题当前不是主控文本“小白狐那时说”。
4. 顶栏关闭按钮当前不是主控文本“关上”。
5. 列表卡当前缺少保存时间展示。
6. 详情页当前暴露了“再聊聊它”和删除 / 收起相关入口，超出 S2 范围。
7. 部分兜底、预览或按钮文案不是本轮主控文本，实施前需要收敛或确认。
```

---

## 3. 数据方案

S2 首版使用 Android 本地状态与现有本地仓库：

```text
数据来源：LocalXiaozhantaiRepository
列表读取：observeItems(childId)
详情读取：itemById(childId, itemId)，并兼容 uiState.items 中已加载 item
排序规则：沿用 visibleXiaozhantaiItems 的 createdAt 倒序
图片引用：沿用 XiaozhantaiItem.photoUri
展品名字：沿用 XiaozhantaiItem.name，并继续使用现有展示名裁剪工具
小白狐当时的话：沿用 XiaozhantaiItem.foxQuote
保存时间：沿用 XiaozhantaiItem.createdAt
```

不新增后端接口，不新增后端数据表，不新增 GrowthEvent 类型，不新增成长系统。

---

## 4. 页面形态

建议首版继续使用现有全屏页面导航，而不是新建弹窗：

```text
1. 首页点“小展台”进入 XiaozhantaiList。
2. 点击列表卡片进入 XiaozhantaiDetail。
3. 列表页和详情页均通过“关上”返回上一层。
4. 从列表页“关上”回到儿童首页。
5. 从详情页“关上”回到列表页。
```

理由：

```text
1. AppNavHost 已经具备列表 / 详情目的地。
2. 全屏页面更适合展示图片列表和详情大图。
3. 可以避免在奇怪小门首屏上叠加复杂弹层，减少对主玩法的干扰。
```

如果主控要求必须是弹窗或底部面板，S2 实施前再调整。

---

## 5. 儿童端文案使用计划

只使用本轮主控提供文本：

```text
入口：小展台
标题：我的小展台
空状态第一行：这里还空空的
空状态第二行：等你和小白狐放进一个小发现
详情小标题：小白狐那时说
关闭：关上
```

实施阶段需要移除或隐藏以下超出 S2 文案入口：

```text
1. “和小白狐再聊聊它”
2. 删除 / 收起相关按钮和确认弹窗
3. 未经主控确认的详情页额外标题
4. 未经主控确认的新增儿童端兜底提示
```

保存时间属于数据格式展示，计划优先沿用当前 `M月d日` / `刚刚` 格式；如主控认为这也属于儿童端文案，需要补充确认文本后再实现。

---

## 6. 列表页计划

列表页只承接已保存展品，不做分类、搜索或复杂展台系统。

计划展示：

```text
1. 顶部标题：我的小展台。
2. 关闭按钮：关上。
3. 有展品时：两列或自适应网格展示展品卡。
4. 每个展品卡显示：
   - 图片缩略图；
   - 名字；
   - 保存时间。
5. 无展品时显示：
   这里还空空的
   等你和小白狐放进一个小发现
```

布局约束：

```text
1. 手机上保持图片缩略图、名字、时间不互相挤压。
2. 平板上可增加网格宽度，但不把入口做成复杂作品库。
3. 小展台入口仍是弱入口，不抢奇怪小门主玩法。
```

---

## 7. 详情页计划

详情页只展示单个展品，不做编辑、删除、搜索、分类或再创作。

计划展示：

```text
1. 大图。
2. 名字。
3. 详情小标题：小白狐那时说。
4. 小白狐当时的话：XiaozhantaiItem.foxQuote。
5. 关闭按钮：关上。
```

不展示：

```text
1. 删除 / 收起入口。
2. “再聊聊它”入口。
3. 分类、标签、图鉴、背包、奖励、积分、等级。
4. 新增未确认儿童端文案。
```

如果详情数据缺失，优先返回列表页或展示主控已确认的空状态；不新增“加载失败”等儿童端文案，除非主控确认。

---

## 8. 与奇怪小门的边界

S2 不改奇怪小门链路：

```text
1. 不改 StrangeDoorDemoState。
2. 不改 StrangeDoorState。
3. 不改 door reducer。
4. 不改 StrangeDoorPhotoTransformMapper。
5. 不改 StrangeDoorRiddleEvaluator。
6. 不改拍照上传、recognizedContent、image_purpose=share。
7. 不改 R1-A 门状态推进节奏。
8. 不改 R1-B 拍照结果视觉。
9. 不改 R1-C 首屏视觉层级。
```

S2 只消费 D5 已保存到小展台的数据。

---

## 9. 会修改的文件

计划中的后续实现预计修改：

```text
android/app/src/main/java/com/childai/companion/ui/showcase/XiaozhantaiScreens.kt
android/app/src/main/java/com/childai/companion/ui/AppNavHost.kt
android/app/src/main/java/com/childai/companion/ui/showcase/XiaozhantaiViewModel.kt
```

说明：

```text
1. XiaozhantaiScreens.kt：收敛列表 / 详情 UI、替换主控文案、增加保存时间展示、隐藏删除和再聊入口。
2. AppNavHost.kt：如需要，调整详情页回调参数，避免继续暴露 recall 行为。
3. XiaozhantaiViewModel.kt：如需要，保留底层 softDelete 能力但 S2 UI 不调用；若要移除 UI 侧依赖，需要做最小签名调整。
```

预计新增或更新测试：

```text
android/app/src/test/java/com/childai/companion/ui/showcase/XiaozhantaiScreensTest.kt
android/app/src/test/java/com/childai/companion/data/showcase/XiaozhantaiModelsTest.kt
```

本计划文档：

```text
docs/session_process/handoffs/20260606_S2_xiaozhantai_gallery_plan.md
```

---

## 10. 不会修改的文件和范围

S2 不修改：

```text
backend/
android/app/src/main/java/com/childai/companion/ui/parent/
android/app/src/main/java/com/childai/companion/data/growth/
android/app/src/main/java/com/childai/companion/data/attachment/
android/app/src/main/java/com/childai/companion/ui/chat/strangedoor/
android/app/src/main/res/drawable-nodpi/
docs/奇怪小门Demo吸引力增强设计_2026_06_05_V0_1.md
docs/奇怪小门Demo实施总计划_2026_06_04_V0_1.md
```

S2 不做：

```text
1. 删除。
2. 分类。
3. 搜索。
4. 百宝箱复杂系统。
5. 收藏图鉴。
6. 奖励、积分、等级。
7. 任务、打卡。
8. 家长端新功能。
9. 后端改造。
10. 奇怪小门视觉继续微调。
11. 真实儿童照片、截图、音频、转录或隐私材料入库。
```

---

## 11. 测试策略

S2 实施阶段建议验证：

```bash
bash scripts/doctor_local_env.sh
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.data.showcase.*' --tests 'com.childai.companion.ui.showcase.*'
bash scripts/android_gradle.sh :app:testDebugUnitTest --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorShowcaseTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorPhotoTransformTest' --tests 'com.childai.companion.ui.chat.ChatViewModelStrangeDoorRiddlePathTest' --tests 'com.childai.companion.ui.chat.strangedoor.*'
bash scripts/android_gradle.sh assembleDebug
git diff --check
```

新增或更新测试覆盖：

```text
1. 列表标题为“我的小展台”。
2. 空状态显示两行主控文本。
3. 列表 item 显示图片缩略图、名字和保存时间。
4. 点击 item 进入详情。
5. 详情显示大图、名字、“小白狐那时说”和 foxQuote。
6. 关闭按钮使用“关上”。
7. S2 UI 不显示删除、分类、搜索、奖励、积分、等级、任务、打卡相关入口。
8. D3 / D4 / D5 / R1-A / R1-B 回归不破。
```

测试数据要求：

```text
1. 只使用合成测试数据或临时测试图片。
2. 不提交真实儿童照片、私有截图、原始音频、原始转录或本地数据库。
3. 不把 app 私有目录中的真实 items.json 或 photos 文件提交入库。
```

---

## 12. 风险点

```text
1. 当前小展台详情已有“再聊聊它”能力，S2 范围不包含该行为；隐藏后可能让既有 recall 入口不可见，需要主控确认。
2. 当前详情已有删除 / 收起入口；S2 禁止删除，计划隐藏 UI，但底层 softDelete 是否保留需要主控确认。
3. 当前 UI 存在未列入 S2 词池的兜底和预览文本；实施时需要逐项收敛，不能由开发方新增替代文案。
4. 保存时间格式当前是 `M月d日` / `刚刚`，如果主控认为日期格式也需严格词池，需要补充文本。
5. 当前小展台本地仓库使用 app 私有路径 photoUri；功能上可用，但公开仓库提交时必须避免带入真实本地数据。
6. 计划使用现有页面导航；如果主控要求弹窗形态，实施范围会增加。
```

---

## 13. 需要主控确认的问题

```text
1. S2 是否确认使用现有全屏页面导航，而不是弹窗或底部面板？
2. 详情页顶栏是否允许继续使用“我的小展台”，不新增单独详情标题？
3. 现有“和小白狐再聊聊它”入口是否本轮隐藏，不纳入 S2？
4. 现有删除 / 收起能力是否仅隐藏 UI，底层 softDelete 暂时保留？
5. 列表保存时间是否可以沿用当前 `M月d日` / `刚刚` 格式？
6. 图片加载失败时是否允许直接使用空状态回退，还是需要主控补充专门兜底文本？
```

---

## 14. 计划结论

```text
S2 可以在不改后端、不改奇怪小门链路、不新增复杂小展台系统的前提下实现。
首版建议基于现有 Android 本地小展台仓库和现有 AppNavHost 页面导航。
实施重点是收敛 UI 文案和入口范围，补齐列表保存时间与详情只读展示。
本轮不进入编码，等待主控审核计划后再启动实现。
```
