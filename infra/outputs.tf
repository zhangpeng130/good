output "cos_bucket_name" {
  value       = local.cos_bucket_name
  description = "COS bucket for SOS audio"
}

output "scf_namespace" {
  value       = tencentcloud_scf_namespace.good.namespace
  description = "SCF namespace name"
}

output "scf_function_names" {
  value = {
    for name, fn in tencentcloud_scf_function.good :
    name => fn.name
  }
}

output "cynosdb_cluster_id" {
  value       = tencentcloud_cynosdb_cluster.good_mysql.id
  description = "CynosDB cluster id"
}

