locals {
  managed_cos_bucket = var.cos_bucket_name == ""
  namespace_name     = "${var.project_name}-${var.environment}"

  functions = {
    send_code    = { timeout = 10, memory = 256 }
    verify_login = { timeout = 10, memory = 256 }
    trigger_sos  = { timeout = 20, memory = 512 }
    heartbeat    = { timeout = 10, memory = 256 }
    check_risk   = { timeout = 30, memory = 256 }
  }
}

resource "random_id" "bucket_suffix" {
  count       = local.managed_cos_bucket ? 1 : 0
  byte_length = 2
}

resource "tencentcloud_cos_bucket" "good_sos" {
  count       = local.managed_cos_bucket ? 1 : 0
  bucket      = "${var.project_name}-${var.environment}-${random_id.bucket_suffix[0].hex}"
  acl         = "private"
  force_clean = false

  lifecycle_rules {
    id            = "delete-sos-in-7-days"
    filter_prefix = "sos/"
    expiration {
      days = 7
    }
  }
}

locals {
  cos_bucket_name      = local.managed_cos_bucket ? tencentcloud_cos_bucket.good_sos[0].bucket : var.cos_bucket_name
  function_code_bucket = var.function_code_bucket != "" ? var.function_code_bucket : local.cos_bucket_name
  function_code_prefix = trimsuffix(var.function_code_prefix, "/")
  default_function_envs = {
    APP_NAME              = var.project_name
    JWT_SECRET            = "replace-me-in-deploy"
    TENCENT_REGION        = var.region
    COS_REGION            = var.region
    COS_BUCKET            = local.cos_bucket_name
    SMS_SDK_APP_ID        = var.sms_sdk_app_id
    SMS_SIGN_NAME         = var.sms_sign_name
    SMS_TEMPLATE_ID       = var.sms_template_id
    DB_HOST               = var.db_host
    DB_PORT               = tostring(var.db_port)
    DB_USER               = var.db_user
    DB_PASSWORD           = var.db_admin_password
    DB_NAME               = var.db_name
    DASHSCOPE_API_KEY     = var.dashscope_api_key
    WECHAT_NOTIFY_WEBHOOK = var.wechat_notify_webhook
    VOICE_MESSAGE_WEBHOOK = var.voice_message_webhook
  }
}

resource "tencentcloud_scf_namespace" "good" {
  namespace   = local.namespace_name
  description = "good app serverless functions"
}

resource "tencentcloud_scf_function" "good" {
  for_each = local.functions

  namespace         = tencentcloud_scf_namespace.good.namespace
  name              = "${local.namespace_name}-${each.key}"
  description       = "good function ${each.key}"
  handler           = "main.main_handler"
  runtime           = "Python3.9"
  timeout           = each.value.timeout
  mem_size          = each.value.memory
  role              = var.scf_role_arn
  cos_bucket_name   = local.function_code_bucket
  cos_bucket_region = var.region
  cos_object_name   = "${local.function_code_prefix}/${each.key}.zip"
  environment       = merge(local.default_function_envs, { FUNCTION_NAME = each.key })
}

resource "tencentcloud_scf_trigger_config" "check_risk_timer" {
  function_name = tencentcloud_scf_function.good["check_risk"].name
  namespace     = tencentcloud_scf_namespace.good.namespace
  trigger_name  = "every-15-min"
  type          = "timer"
  trigger_desc  = "0 */15 * * * * *"
  qualifier     = "$LATEST"
  enable        = "OPEN"
}

resource "tencentcloud_cynosdb_cluster" "good_mysql" {
  available_zone         = var.cynosdb_zone
  vpc_id                 = var.vpc_id
  subnet_id              = var.subnet_id
  db_type                = "MYSQL"
  db_version             = "5.7"
  db_mode                = "NORMAL"
  cluster_name           = "${local.namespace_name}-db"
  password               = var.db_admin_password
  charge_type            = "POSTPAID_BY_HOUR"
  serverless_status_flag = "resume"
  min_cpu                = 1
  max_cpu                = 4
  auto_pause             = "yes"
  auto_pause_delay       = 1800
  instance_cpu_core      = 2
  instance_memory_size   = 4
  port                   = 3306
  force_delete           = true
}

