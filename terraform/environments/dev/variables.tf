variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_number" {
  description = "GCP Project number (find with: gcloud projects describe PROJECT_ID --format='value(projectNumber)')"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (used as suffix in resource names)"
  type        = string
  default     = "dev"
}

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "app_secret_key" {
  description = "Application secret key for session signing (FastAPI/Redis sessions)"
  type        = string
  sensitive   = true
}

variable "grafana_admin_password" {
  description = "Grafana admin user password"
  type        = string
  sensitive   = true
}
