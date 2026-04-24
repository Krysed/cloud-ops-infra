# ============================================================
# GKE Node Service Account
# ============================================================
resource "google_service_account" "gke_node_sa" {
  account_id   = var.gke_sa_name
  display_name = "GKE Node Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "gke_node_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_node_sa.email}"
}

resource "google_project_iam_member" "gke_node_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_node_sa.email}"
}

resource "google_project_iam_member" "gke_node_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.gke_node_sa.email}"
}

resource "google_project_iam_member" "gke_node_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_node_sa.email}"
}

# ============================================================
# Application Service Account (Workload Identity)
# Allows pods in GKE to authenticate as this GCP SA
# ============================================================
resource "google_service_account" "app_sa" {
  account_id   = var.app_sa_name
  display_name = "Application Service Account (Workload Identity)"
  project      = var.project_id
}

resource "google_project_iam_member" "app_sa_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}

resource "google_project_iam_member" "app_sa_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}

# Workload Identity binding: K8s ServiceAccount → GCP ServiceAccount
# The K8s SA must be named "app-sa" in the gke_namespace
resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.gke_namespace}/app-sa]"
}

# ============================================================
# CI/CD Service Account (used by GitHub Actions)
# ============================================================
resource "google_service_account" "cicd_sa" {
  account_id   = var.cicd_sa_name
  display_name = "CI/CD Service Account (GitHub Actions)"
  project      = var.project_id
}

resource "google_project_iam_member" "cicd_container_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

resource "google_project_iam_member" "cicd_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

# NOTE: roles/editor is broad - scope down before production
resource "google_project_iam_member" "cicd_terraform_runner" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

# ============================================================
# Secret Manager
# ============================================================
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "app_secret_key" {
  secret_id = "app-secret-key"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "app_secret_key" {
  secret      = google_secret_manager_secret.app_secret_key.id
  secret_data = var.app_secret_key
}

resource "google_secret_manager_secret" "grafana_admin_password" {
  secret_id = "grafana-admin-password"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "grafana_admin_password" {
  secret      = google_secret_manager_secret.grafana_admin_password.id
  secret_data = var.grafana_admin_password
}
