output "cicd_sa_email" {
  description = "CI/CD service account email (GitHub Actions)"
  value       = module.security.cicd_sa_email
}

output "wif_provider" {
  description = "Workload Identity Federation provider"
  value       = module.security.wif_provider
}

output "gke_node_sa_email" {
  description = "GKE node service account email"
  value       = module.security.gke_node_sa_email
}

output "app_sa_email" {
  description = "Application service account email"
  value       = module.security.app_sa_email
}
