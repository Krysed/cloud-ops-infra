output "gke_node_sa_email" {
  description = "GKE node service account email"
  value       = google_service_account.gke_node_sa.email
}

output "app_sa_email" {
  description = "Application service account email (Workload Identity)"
  value       = google_service_account.app_sa.email
}

output "app_sa_id" {
  description = "Application service account resource ID (needed for Workload Identity binding)"
  value       = google_service_account.app_sa.name
}

output "cicd_sa_email" {
  description = "CI/CD service account email (GitHub Actions)"
  value       = google_service_account.cicd_sa.email
}

output "db_password_secret_id" {
  description = "Secret Manager secret ID for database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "app_secret_key_secret_id" {
  description = "Secret Manager secret ID for application secret key"
  value       = google_secret_manager_secret.app_secret_key.secret_id
}
