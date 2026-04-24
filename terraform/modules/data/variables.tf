variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "network_id" {
  description = "VPC network ID (self_link) for private service access"
  type        = string
}

# Cloud SQL
variable "db_instance_name" {
  description = "Cloud SQL instance name"
  type        = string
  default     = "infra-postgres"
}

variable "db_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "POSTGRES_17"
}

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "app_db"
}

variable "db_user" {
  description = "Database user"
  type        = string
  default     = "app_user"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "backup_enabled" {
  description = "Enable automated backups for Cloud SQL"
  type        = bool
  default     = true
}

variable "backup_start_time" {
  description = "Backup window start time (HH:MM)"
  type        = string
  default     = "03:00"
}

# Memorystore Redis
variable "redis_instance_name" {
  description = "Memorystore Redis instance name"
  type        = string
  default     = "infra-redis"
}

variable "redis_tier" {
  description = "Redis service tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "BASIC"

  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "redis_tier must be BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

variable "redis_version" {
  description = "Redis version"
  type        = string
  default     = "REDIS_7_0"
}
