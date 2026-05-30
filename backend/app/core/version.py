"""
应用版本配置

每次发版时修改此文件中的版本号和更新内容。
Android 客户端启动时会调用 /api/v1/version/check 接口检查是否有新版本。
"""

# 当前最新版本号
APP_LATEST_VERSION = "0.1.0"
APP_LATEST_VERSION_CODE = 1

# 更新提示内容
APP_UPDATE_TITLE = "发现新版本"
APP_UPDATE_CONTENT = "1. 修复了一些问题\n2. 优化了体验"

# 是否强制更新（true 时用户必须更新才能使用）
APP_FORCE_UPDATE = False

# APK 文件名（放在 backend/storage/apk/ 目录下）
APK_FILENAME = "child-ai-companion.apk"
