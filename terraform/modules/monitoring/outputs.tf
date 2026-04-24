output "namespace" {
  description = "Kubernetes namespace for the monitoring stack"
  value       = kubernetes_namespace.monitoring.metadata[0].name
}

output "grafana_service_name" {
  description = "Grafana service name (within the monitoring namespace)"
  value       = "kube-prometheus-stack-grafana"
}

output "prometheus_service_name" {
  description = "Prometheus service name (within the monitoring namespace)"
  value       = "kube-prometheus-stack-prometheus"
}

output "loki_service_name" {
  description = "Loki service name"
  value       = helm_release.loki.name
}

output "tempo_service_name" {
  description = "Tempo service name"
  value       = helm_release.tempo.name
}

output "mimir_service_name" {
  description = "Mimir service name"
  value       = kubernetes_service.mimir.metadata[0].name
}
