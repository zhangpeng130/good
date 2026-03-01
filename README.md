# 我很好（good）- 适老化安全守护系统

一个面向独居老人的“无感守护”样板工程：

- 老人端：`uni-app(Vue3)`，超简登录 + 一键报平安 + 长按 SOS
- 家属端：`微信小程序`，绑定父母 + 守护看板 + 一键解绑
- 后端：`腾讯云 SCF(Python3.9)` + `COS` + `TDSQL-C(MySQL 兼容)`

---

## 1. 项目结构

```text
frontend/         # 老人端 uni-app
miniprogram/      # 家属端微信小程序
cloudfunctions/   # SCF 函数 + 公共模块
infra/            # Terraform (SCF + COS + TDSQL-C)
db/               # 数据库初始化脚本
tests/            # 后端核心单元测试
deploy.sh         # 一键打包/上传/更新函数
```

---

## 2. 已实现能力（核心）

### 老人端

- 手机号验证码登录（支持“语音读验证码”按钮）
- 主界面仅一个超大绿色按钮“我很好”
- 点击按钮：立即报平安并通知家属
- 长按 3 秒：触发 SOS（录音 10 秒 + 上传位置）

### 家属端

- 输入“老人手机号 + 老人提供的绑定码”完成绑定
- 看板显示：在线状态 / 最近报平安时间 / SOS 历史
- 支持一键解绑

### 云函数（5 个）

- `send_code`：发送短信验证码 + 可选 CosyVoice 语音播报
- `verify_login`：老人登录 / 子女绑定
- `trigger_sos`：上传录音到 COS、写 SOS 记录、通知家属
- `heartbeat`：心跳上报 / 报平安 / 看板查询 / 解绑
- `check_risk`：风险巡检（4h低电量失联提醒、12h无操作电话预警）

---

## 3. API 约定（简版）

> 默认走 API 网关，POST `/{function_name}`

### 3.1 `send_code`

请求：

```json
{
  "phone": "13800138000",
  "purpose": "elder_login",
  "read_aloud": true
}
```

### 3.2 `verify_login` - 老人登录

```json
{
  "action": "elder_login",
  "phone": "13800138000",
  "code": "123456"
}
```

### 3.3 `verify_login` - 子女绑定

```json
{
  "action": "child_bind",
  "elder_phone": "13800138000",
  "binding_code": "654321",
  "openid": "wx_openid_xxx",
  "nickname": "女儿"
}
```

### 3.4 `heartbeat`（需 JWT）

- 老人报平安：`{"action":"checkin","battery_level":56}`
- 老人心跳：`{"action":"heartbeat","battery_level":56}`
- 子女看板：`{"action":"get_dashboard","elder_id":1}`
- 子女解绑：`{"action":"unbind","elder_id":1}`

### 3.5 `trigger_sos`（需 JWT）

```json
{
  "audio_base64": "<base64>",
  "audio_format": "wav",
  "location": { "latitude": 23.1, "longitude": 113.3, "address": "广东省广州市..." }
}
```

---

## 4. 安全合规

- 除登录相关接口外均要求 JWT
- 验证码 5 分钟过期，使用后立即失效
- 不涉及通讯录/相册等非必要权限
- SOS 录音按 `sos/` 前缀存储，并配置 7 天生命周期删除

---

## 5. 本地开发

### 5.1 Python 测试

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

### 5.2 数据库初始化

在 TencentDB 执行：

```bash
mysql -h <host> -u <user> -p < db/schema.sql
```

### 5.3 基础设施部署（Terraform）

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

### 5.4 函数打包与更新

```bash
chmod +x deploy.sh
COS_BUCKET=<bucket> SCF_NAMESPACE=good-prod FUNCTION_NAME_PREFIX=good-prod bash deploy.sh
```

若希望一并执行 `terraform apply`：

```bash
RUN_TERRAFORM=1 bash deploy.sh
```

---

## 6. 生产化建议（你可以按需开启）

1. 子女端 `openid` 改为 CloudBase/云函数实时换取（去掉 mock openid）。
2. `VOICE_MESSAGE_WEBHOOK` 替换为腾讯云 VoiceMessage 官方 SDK 网关直连。
3. 为 `check_risk` 增加“重复告警节流 + 升级策略”（如 30 分钟未响应二次外呼）。
4. 给 `trigger_sos` 增加位置信息逆地理编码（腾讯位置服务）以提升电话播报可读性。

