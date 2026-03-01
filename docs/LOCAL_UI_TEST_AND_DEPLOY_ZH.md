# 我很好（good）本地界面测试与腾讯云部署手册（新手版）

本手册按“**没有 App/云函数经验**”编写，目标是让你按步骤即可跑起来。

---

## 0. 你将得到什么

完成本文后，你可以做到：

1. 在腾讯云部署后端（SCF + COS + TDSQL-C）。
2. 在本地打开老人端界面（uni-app）和家属端界面（微信小程序）。
3. 按测试清单完整验证：登录、绑定、报平安、SOS、失联预警。

---

## 1. 推荐测试路径（先测通，再上生产）

为了降低你第一次上手难度，建议分两阶段：

### 阶段 A：测试模式（推荐先做）

- `debug_mode = true`
- `mock_external_services = true`

效果：

- 不依赖真实短信、真实 COS 上传，也能完整走 UI 流程。
- 登录页会直接显示“测试验证码”。

### 阶段 B：生产模式

- `debug_mode = false`
- `mock_external_services = false`

效果：

- 真实短信下发、真实录音上传 COS、真实通知链路。

---

## 2. 本地环境准备

> 建议：Windows/macOS 直接使用官方 GUI 工具（HBuilderX、微信开发者工具）更稳定。

### 2.1 必装软件

1. **Git**
2. **Python 3.10+**
3. **Node.js 18 LTS**（建议，不要用过新的版本）
4. **Terraform 1.6+**
5. **腾讯云 CLI（tccli）**
6. **HBuilderX**（运行 uni-app）
7. **微信开发者工具**（运行小程序）
8. （可选）MySQL 客户端（`mysql` 命令）

### 2.2 终端自检命令

在终端执行：

```bash
git --version
python3 --version
node --version
terraform version
tccli --version
```

全部有输出即通过。

---

## 3. 腾讯云侧前置准备

### 3.1 开通与确认服务

控制台确认这些服务已开通：

- SCF 云函数
- COS 对象存储
- TDSQL-C（CynosDB）
- API 网关
- SMS（生产模式需要）

### 3.2 创建 API 密钥

路径：`访问管理 CAM -> API 密钥管理`

创建 `SecretId / SecretKey`，后续给 Terraform 与 tccli 使用。

### 3.3 （可选）创建 SCF 执行角色

路径：`CAM -> 角色`

角色需至少具备：

- SCF 执行权限
- COS 读写权限
- 访问数据库所在网络权限（若你有更严格 VPC 策略）

获取 `role arn`，填入 `scf_role_arn`。

> 如果你暂时不配置 role，本项目也支持留空（会尝试使用默认权限模型）。

### 3.4 准备 VPC 与子网（数据库用）

你需要：

- `vpc_id`
- `subnet_id`
- 可用区（例如 `ap-guangzhou-3`）

---

## 4. 拉代码并做基础校验

```bash
git clone <你的仓库地址>
cd good
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

看到 `passed` 即后端核心逻辑正常。

---

## 5. 配置 Terraform 变量并创建云资源

### 5.1 复制变量模板

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

### 5.2 修改 `terraform.tfvars`

最关键字段说明：

- `secret_id` / `secret_key`：你的腾讯云密钥
- `region`：如 `ap-guangzhou`
- `project_name` / `environment`：会影响函数名（如 `good-prod-send_code`）
- `jwt_secret`：务必用高强度随机字符串
- `vpc_id` / `subnet_id` / `cynosdb_zone`：数据库网络信息
- `db_admin_password`：数据库管理员密码
- `db_host` / `db_user` / `db_name`：函数访问数据库配置
- `debug_mode`：是否显示测试验证码
- `mock_external_services`：是否开启外部服务模拟

### 5.3 测试模式推荐值（首次）

```hcl
debug_mode = true
mock_external_services = true
```

### 5.4 执行 Terraform

```bash
terraform init
terraform plan
terraform apply
```

成功后会输出：

- COS bucket 名称
- SCF 命名空间
- 5 个函数名
- CynosDB 集群 ID

---

## 6. 初始化数据库（非常重要）

在可连接数据库的终端执行：

```bash
mysql -h <db_host> -u <db_user> -p < ../db/schema.sql
```

执行后请确认表都创建成功（`users`、`verification_codes`、`bindings`、`heartbeats`、`sos_events` 等）。

---

## 7. 打包并部署 5 个云函数代码

回到仓库根目录执行：

```bash
cd ..
chmod +x deploy.sh
COS_BUCKET=<你的bucket> \
SCF_NAMESPACE=good-prod \
FUNCTION_NAME_PREFIX=good-prod \
TENCENT_REGION=ap-guangzhou \
bash deploy.sh
```

说明：

- `deploy.sh` 会自动打包 5 个函数 zip。
- 如果你传入 `COS_BUCKET`，会上传并更新 SCF 代码。
- 如果 `COS_BUCKET` 为空，只打包不上传（用于本地检查）。

---

## 8. 配置 API 网关（界面联调必须）

本项目前端默认调用 `POST /{function_name}`，所以需要网关路由到 SCF。

### 8.1 在控制台创建 API 服务

路径：`API 网关 -> 服务 -> 新建`

建议：

- 服务名：`good-api`
- 环境：`prod`
- 开启 CORS（允许 `Authorization, Content-Type`）

### 8.2 创建 5 个 API（POST）

为每个函数建一条路径并绑定后端 SCF：

1. `POST /send_code` -> `good-prod-send_code`
2. `POST /verify_login` -> `good-prod-verify_login`
3. `POST /heartbeat` -> `good-prod-heartbeat`
4. `POST /trigger_sos` -> `good-prod-trigger_sos`
5. `POST /check_risk` -> `good-prod-check_risk`

### 8.3 发布服务

在 `prod` 环境点击发布，记下访问域名，例如：

`https://xxxxxx.apigw.tencentcs.com/prod`

---

## 9. 本地运行老人端（uni-app）

你有两种方式：

## 方式 A（推荐新手）：HBuilderX 图形界面

1. 打开 HBuilderX。
2. 选择“打开目录”，选中仓库下的 `frontend/`。
3. 在项目根目录创建 `.env`，内容：

```env
VITE_API_BASE=https://你的网关域名/prod
```

4. 点击运行 -> 运行到浏览器（H5）或运行到手机模拟器。
5. 打开页面后进入登录页测试。

## 方式 B（命令行）

```bash
cd frontend
npm install --legacy-peer-deps
npx uni -p h5
```

> 如果命令行构建失败，优先使用 HBuilderX（兼容性更好）。

---

## 10. 本地运行家属端（微信小程序）

1. 打开微信开发者工具。
2. 导入项目目录：`miniprogram/`。
3. 修改 `miniprogram/config.js`：

```js
API_BASE: "https://你的网关域名/prod"
```

4. 编译运行，默认进入绑定页。

> 当前代码为了便于测试，`openid` 使用本地 mock 值；生产再接入 CloudBase 真实 openid。

---

## 11. 本地界面联调测试清单（按顺序）

## 11.1 场景 1：老人登录

步骤：

1. 老人端输入手机号，点击“获取验证码”。
2. 测试模式下，页面会显示 `测试验证码：xxxxxx`。
3. 输入验证码，点击“进入守护主页”。

期望：

- 成功进入主页。
- 主页显示 6 位绑定码。

## 11.2 场景 2：家属绑定

步骤：

1. 打开家属端绑定页。
2. 输入老人手机号 + 老人页面上的绑定码。
3. 点击“立即绑定”。

期望：

- 提示绑定成功。
- 自动跳转到看板页。

## 11.3 场景 3：一键报平安

步骤：

1. 老人端点击大绿色“我很好”按钮。
2. 家属端点击“刷新状态”。

期望：

- 老人端提示“已报平安”。
- 看板“最近报平安时间”刷新为当前时间。
- 状态正常显示在线/离线变化。

## 11.4 场景 4：SOS 紧急呼救

步骤：

1. 老人端长按绿色按钮 3 秒。
2. 等待 10 秒录音结束并上传。
3. 家属端刷新看板。

期望：

- 老人端提示 “SOS 已发送”。
- 家属端 SOS 历史新增一条记录。
- 生产模式下，COS 应出现新录音对象（`sos/` 前缀）。

## 11.5 场景 5：一键解绑

步骤：

1. 家属端点击“一键解绑”。
2. 确认弹窗。

期望：

- 解绑成功并回到绑定页。

## 11.6 场景 6：失联预警（人工触发）

你可直接调用 `check_risk` 来验证策略：

```bash
tccli scf Invoke \
  --FunctionName good-prod-check_risk \
  --Namespace good-prod \
  --InvocationType Event
```

期望：

- 数据库 `risk_alerts` 会新增预警记录（满足条件时）。
- 生产模式下会发送相应通知（微信/语音）。

---

## 12. 生产切换步骤（从测试模式升级）

1. `infra/terraform.tfvars` 修改：

```hcl
debug_mode = false
mock_external_services = false
```

2. 配置真实短信参数：

- `sms_sdk_app_id`
- `sms_sign_name`
- `sms_template_id`

3. 配置真实告警渠道：

- `wechat_notify_webhook`（或替换成你的 CloudBase 发送逻辑）
- `voice_message_webhook`（或替换为腾讯云语音 API）

4. 重新执行：

```bash
cd infra
terraform apply
cd ..
bash deploy.sh
```

---

## 13. 常见问题排查（新手高频）

### Q1：登录时报“短信发送失败”

原因：短信配置不完整或未开通 SMS。

解决：

1. 先切测试模式：`mock_external_services = true`。
2. 或补齐短信配置并确保签名/模板已审核通过。

### Q2：老人端/家属端请求 401

原因：JWT 缺失或过期。

解决：

1. 重新登录（老人端重新获取验证码登录）。
2. 检查网关是否透传 `Authorization` 头。

### Q3：SOS 失败，提示 COS 上传异常

原因：COS 桶、权限、区域不匹配。

解决：

1. 检查 `COS_BUCKET` 和 `COS_REGION` 环境变量。
2. 检查 SCF 角色是否有 COS 写权限。
3. 测试模式下可先开启 `mock_external_services = true`。

### Q4：家属端看板一直空

原因：未绑定成功或 `elder_id` 不匹配。

解决：

1. 确认绑定成功后再进看板。
2. 查看 `bindings` 表中 `status` 是否为 `active`。

### Q5：命令行构建 uni-app 不稳定

原因：Node/uni-cli 版本兼容差异。

解决：

1. 优先用 HBuilderX 运行与打包。
2. Node 建议固定 18 LTS。

---

## 14. 你下一步最小动作（照着做就行）

如果你只想最快看到页面跑起来：

1. 按第 5 节将 Terraform 配成测试模式。
2. 执行 `terraform apply`。
3. 按第 6 节初始化数据库。
4. 执行第 7 节 `deploy.sh`。
5. 按第 8 节建 API 网关并发布。
6. 用第 9、10 节启动两个前端。
7. 用第 11 节按顺序点一遍完整流程。

做到这 7 步，你就能完整看到“老人端 + 家属端 + 云函数”的闭环。

