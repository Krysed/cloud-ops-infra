variable "namespace" {
  description = "Kubernetes namespace for the monitoring stack"
  type        = string
  default     = "monitoring"
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
}

variable "prometheus_retention_days" {
  description = "Number of days to retain Prometheus data"
  type        = number
  default     = 15
}

variable "loki_retention_days" {
  description = "Number of days to retain Loki log data"
  type        = number
  default     = 30
}

variable "storage_size_grafana" {
  description = "PVC size for Grafana"
  type        = string
  default     = "5Gi"
}

variable "storage_size_prometheus" {
  description = "PVC size for Prometheus"
  type        = string
  default     = "10Gi"
}

variable "storage_size_loki" {
  description = "PVC size for Loki"
  type        = string
  default     = "10Gi"
}

variable "storage_size_tempo" {
  description = "PVC size for Tempo"
  type        = string
  default     = "5Gi"
}

variable "storage_size_mimir" {
  description = "PVC size for Mimir"
  type        = string
  default     = "10Gi"
}
