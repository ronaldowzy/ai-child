# QA Result Template v0.1

用途：记录 Redmi K60 / Honor Pad 5 家庭内测结果。不要上传真实儿童音频、真实儿童图片或真实家庭照片。

## 1. Test Session

```text
测试设备：
Android 版本：
设备内存 / 备注：
APK path：
APK sha256：
后端 base URL：
后端启动命令：
测试时间：
测试人：
```

## 2. Environment

```text
Mac LAN IP：
设备和 Mac 是否同一网络：
后端 health URL：
health 检查结果：
PostgreSQL setup：PASS / FAIL / BLOCKED
DB smoke：PASS / FAIL / BLOCKED
real MiMo ASR smoke：PASS / FAIL / BLOCKED
real MiMo vision smoke：PASS / FAIL / BLOCKED
```

## 3. Summary

```text
通过项：
- 

失败项：
- 

未测项：
- 
```

## 4. Issues

### Issue 1

```text
严重级别：Blocker / P1 / P2
功能区域：
是否稳定复现：
复现步骤：
1.
2.
3.

期望行为：

实际行为：

截图 / 录屏路径：
日志路径：
是否涉及真实儿童音频/图片：默认否；如是，不上传，先本地保留并征得父亲确认。
备注：
```

### Issue 2

```text
严重级别：Blocker / P1 / P2
功能区域：
是否稳定复现：
复现步骤：
1.
2.
3.

期望行为：

实际行为：

截图 / 录屏路径：
日志路径：
是否涉及真实儿童音频/图片：默认否；如是，不上传，先本地保留并征得父亲确认。
备注：
```

## 5. Evidence Boundary

```text
1. 不上传真实儿童语音。
2. 不上传真实儿童照片或家庭照片。
3. 不在 QA 文档里写 MiMo key、Bearer token、API key 或完整 provider raw response。
4. 日志如含孩子逐字 transcript，先本地保留，不提交 git。
5. 可以记录 APK sha256、base URL、错误码、HTTP status、request_id 和非敏感截图路径。
```
