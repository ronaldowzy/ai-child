# CentOS 7 单目录部署说明

目标：服务器上只维护一个大目录，例如：

```text
/opt/ai-child/
```

这个目录里放全部运行所需内容：

```text
/opt/ai-child/backend/                    后端代码
/opt/ai-child/storage/apk/                 APK 下载文件
/opt/ai-child/backend/models/              本地 ASR 模型
/opt/ai-child/start_backend.sh             nohup 启动脚本
/opt/ai-child/stop_backend.sh              停止脚本
/opt/ai-child/status_backend.sh            状态脚本
/opt/ai-child/migrate_db.sh                数据库迁移脚本
/opt/ai-child/child-ai-backend.env         生产环境变量
/opt/ai-child/logs/                        stdout/stderr/start 日志
/opt/ai-child/run/                         pid 文件
```

不使用 systemd，不把服务文件放进系统目录。`start_backend.sh` 使用 `nohup` 后台启动，关闭 SSH/客户端后服务不会跟着退出。

## 1. 解压部署包

把本机生成的部署包上传到服务器，例如：

```text
ai-child-backend-v0.2.1-code3-*.tar.gz
```

首次部署：

```bash
sudo mkdir -p /opt/ai-child
sudo tar -C /opt/ai-child --strip-components=1 -xzf ai-child-backend-v0.2.1-code3-*.tar.gz
sudo chmod +x /opt/ai-child/start_backend.sh /opt/ai-child/stop_backend.sh /opt/ai-child/status_backend.sh /opt/ai-child/migrate_db.sh
```

建议创建运行用户：

```bash
sudo useradd --system --home /opt/ai-child --shell /sbin/nologin ai-child || true
sudo mkdir -p /opt/ai-child/logs /opt/ai-child/run
sudo chown -R ai-child:ai-child /opt/ai-child
```

## 2. Python/conda 环境

如果还没有环境：

```bash
conda create -n child-ai python=3.12 -y
conda activate child-ai
```

安装依赖：

```bash
cd /opt/ai-child
python -m pip install -U pip
conda install -y numpy=1.26.4 greenlet
python -m pip install -e "backend[asr-local]"
```

CentOS 7 自带 GCC 4.8.5 太老，不要让 pip 从源码编译 NumPy 或 greenlet。上面的 `conda install numpy=1.26.4 greenlet` 会安装二进制包，随后 `backend[asr-local]` 只安装剩余依赖。

确认 Python 路径：

```bash
which python
```

把这个路径填到 `/opt/ai-child/child-ai-backend.env` 的 `AI_CHILD_PYTHON_BIN`。

## 3. PostgreSQL 12 初始化

部署包不包含本地数据库文件、dump、SQLite、测试账号、聊天记录、家长日报或缓存数据。首次上线应新建空库，然后只运行 Alembic migration 建表。

创建用户和数据库：

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE child_ai WITH LOGIN PASSWORD '<strong-password>';
CREATE DATABASE child_ai_prod OWNER child_ai;
\q
```

## 4. 生产环境变量

复制模板：

```bash
cd /opt/ai-child
cp child-ai-backend.env.example child-ai-backend.env
chmod 600 child-ai-backend.env
```

编辑：

```bash
vi /opt/ai-child/child-ai-backend.env
```

至少确认：

```text
AI_CHILD_APP_ROOT=
AI_CHILD_PYTHON_BIN=/opt/conda/envs/child-ai/bin/python
AI_CHILD_RUN_DIR=
AI_CHILD_LOG_DIR=
CHILD_AI_BACKEND_HOST=0.0.0.0
CHILD_AI_BACKEND_PORT=22026
CHILD_AI_DATABASE_URL=postgresql+psycopg://child_ai:<strong-password>@127.0.0.1:5432/child_ai_prod
CHILD_AI_MIMO_API_KEY=
CHILD_AI_MIMO_TTS_API_KEY=
CHILD_AI_MIMO_ASR_API_KEY=
```

`AI_CHILD_APP_ROOT`、`AI_CHILD_RUN_DIR`、`AI_CHILD_LOG_DIR` 留空即可，脚本会自动使用当前目录、`run/` 和 `logs/`。

必须保持：

```text
CHILD_AI_ALLOW_MOCK_RUNTIME=false
CHILD_AI_ALLOW_AUTH_MEMORY_FALLBACK=false
CHILD_AI_MODEL_PROVIDER=mimo
CHILD_AI_VISION_PROVIDER=mimo
CHILD_AI_TTS_PROVIDER=mimo
CHILD_AI_ASR_PROVIDER=local_sensevoice
```

## 5. 数据库迁移

```bash
cd /opt/ai-child
sudo -u ai-child bash ./migrate_db.sh
```

迁移只建表，不导入本地数据。

## 6. 启停服务

启动：

```bash
cd /opt/ai-child
sudo -u ai-child bash ./start_backend.sh
```

查看状态：

```bash
sudo -u ai-child bash /opt/ai-child/status_backend.sh
```

停止：

```bash
sudo -u ai-child bash /opt/ai-child/stop_backend.sh
```

日志：

```text
/opt/ai-child/logs/child-ai-backend.log
/opt/ai-child/logs/child-ai-backend.err.log
/opt/ai-child/logs/child-ai-backend.start.log
```

PID：

```text
/opt/ai-child/run/child-ai-backend.pid
```

`start_backend.sh` 使用 `nohup` 后台启动。只要进程没被 `stop_backend.sh`、`kill`、服务器重启或崩溃终止，关闭 SSH/客户端不会停服务。

## 7. 端口和公网验证

开放服务器 TCP `22026`，云安全组也要放行。

本机验证：

```bash
curl -fsS http://127.0.0.1:22026/api/v1/health/detail
curl -fsS http://127.0.0.1:22026/api/v1/version/check
curl -I http://127.0.0.1:22026/api/v1/version/download
curl -I http://127.0.0.1:22026/download
```

公网验证：

```bash
curl -fsS http://ihealth.znitech.com:22026/api/v1/health/detail
curl -fsS http://ihealth.znitech.com:22026/api/v1/version/check
curl -I http://ihealth.znitech.com:22026/api/v1/version/download
curl -I http://ihealth.znitech.com:22026/download
```

APK 下载页：

```text
http://ihealth.znitech.com:22026/download
```

页面会展示 APK 下载按钮和二维码；如果在微信内打开，会提示点右上角用手机自带浏览器打开后再下载。

## 8. 后续更新

本地重新打包：

```bash
bash scripts/bump_app_version.sh --bump patch --content "本次更新内容"
source /Users/wzy/.android/child-ai-release-signing.env
bash scripts/build_release_apk.sh --base-url http://ihealth.znitech.com:22026/ --publish-to-backend-storage
bash scripts/build_backend_deploy_package.sh --include-apk
```

服务器更新：

```bash
cd /opt/ai-child
sudo -u ai-child bash ./stop_backend.sh
sudo tar -C /opt/ai-child --strip-components=1 -xzf /path/to/ai-child-backend-v*.tar.gz
sudo chown -R ai-child:ai-child /opt/ai-child
sudo -u ai-child bash ./migrate_db.sh
sudo -u ai-child bash ./start_backend.sh
sudo -u ai-child bash ./status_backend.sh
```

如果更新前已经有生产 `child-ai-backend.env`，解压前先备份，解压后恢复：

```bash
cp /opt/ai-child/child-ai-backend.env /tmp/child-ai-backend.env.backup
sudo tar -C /opt/ai-child --strip-components=1 -xzf /path/to/ai-child-backend-v*.tar.gz
cp /tmp/child-ai-backend.env.backup /opt/ai-child/child-ai-backend.env
```

每次更新后至少确认：

```text
1. /api/v1/health/detail 返回 ok。
2. /api/v1/version/check 返回新 versionCode。
3. /api/v1/version/download 可下载 APK。
4. /download 页面和二维码可访问。
5. 新 APK 登录、对话、ASR、TTS、图片上传至少做一轮 smoke。
```
