# Terraform 基础设施

本目录用于部署 **腾讯云** 资源：

- SCF 函数命名空间与 5 个函数
- COS 桶 + `sos/` 前缀 7 天生命周期删除
- TDSQL-C（CynosDB MySQL）集群

## 快速开始

1. 复制变量文件：

   `cp terraform.tfvars.example terraform.tfvars`

2. 修改 `terraform.tfvars`。

3. 执行：

   `terraform init && terraform plan && terraform apply`

## 注意事项

- SCF 代码包由 `deploy.sh` 生成并上传到 COS 后，再由 Terraform 引用。
- `check_risk` 通过定时触发器每 15 分钟巡检一次。
- 微信订阅消息与语音外呼在样例中通过 webhook 适配，生产可直接替换成腾讯云官方 API 网关/SDK 实现。

