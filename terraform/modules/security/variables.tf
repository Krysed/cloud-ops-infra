variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_number" {
  description = "GCP Project number (used for Workload Identity)"
  type        = string
}

variable "gke_namespace" {
  description = "Kubernetes namespace where the application runs"
  type        = string
  default     = "dev"
}

variable "gke_sa_name" {
  description = "Service account name for GKE nodes"
  type        = string
  default     = "gke-node-sa"
}

variable "app_sa_name" {
  description = "Service account name for the application (Workload Identity)"
  type        = string
  default     = "app-sa"
}

variable "cicd_sa_name" {
  description = "Service account name for CI/CD (GitHub Actions)"
  type        = string
  default     = "cicd-sa"
}

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "app_secret_key" {
  description = "Application secret key used for session signing"
  type        = string
  sensitive   = true
}

variable "grafana_admin_password" {
  description = "Grafana admin user password"
  type        = string
  sensitive   = true
}
