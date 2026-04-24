output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster API endpoint (sensitive)"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "Base64-encoded cluster CA certificate (sensitive)"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cluster_id" {
  description = "GKE cluster full resource ID"
  value       = google_container_cluster.primary.id
}

output "cluster_location" {
  description = "GKE cluster region/location"
  value       = google_container_cluster.primary.location
}

output "get_credentials_command" {
  description = "gcloud command to configure kubectl for this cluster"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}"
}
