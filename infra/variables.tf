variable "secret_id" {
  description = "TencentCloud SecretId"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "TencentCloud SecretKey"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "TencentCloud region"
  type        = string
  default     = "ap-guangzhou"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project short name"
  type        = string
  default     = "good"
}

variable "vpc_id" {
  description = "VPC ID for CynosDB"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for CynosDB"
  type        = string
}

variable "cynosdb_zone" {
  description = "Availability zone for CynosDB"
  type        = string
  default     = "ap-guangzhou-3"
}

variable "db_admin_password" {
  description = "Admin password for CynosDB"
  type        = string
  sensitive   = true
}

variable "db_host" {
  description = "Database host for SCF env, optional when managed outside Terraform"
  type        = string
  default     = ""
}

variable "db_port" {
  description = "Database port"
  type        = number
  default     = 3306
}

variable "db_user" {
  description = "Database username for SCF"
  type        = string
  default     = "root"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "good"
}

variable "scf_role_arn" {
  description = "SCF execution role ARN"
  type        = string
}

variable "sms_sdk_app_id" {
  description = "Tencent SMS sdk app id"
  type        = string
}

variable "sms_sign_name" {
  description = "Tencent SMS sign name"
  type        = string
  default     = "我很好"
}

variable "sms_template_id" {
  description = "Tencent SMS template id"
  type        = string
}

variable "cos_bucket_name" {
  description = "Existing COS bucket name. Empty means create one."
  type        = string
  default     = ""
}

variable "function_code_bucket" {
  description = "Bucket used to store function zip package."
  type        = string
  default     = ""
}

variable "function_code_prefix" {
  description = "Prefix path for SCF function code package in COS."
  type        = string
  default     = "functions/"
}

variable "dashscope_api_key" {
  description = "DashScope API key for CosyVoice"
  type        = string
  sensitive   = true
  default     = ""
}

variable "wechat_notify_webhook" {
  description = "Webhook endpoint for mini-program subscription notification"
  type        = string
  default     = ""
}

variable "voice_message_webhook" {
  description = "Webhook endpoint to bridge Tencent VoiceMessage send API"
  type        = string
  default     = ""
}

