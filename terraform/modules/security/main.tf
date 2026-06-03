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

resource "google_project_iam_member" "gke_node_default_node_sa" {
  project = var.project_id
  role    = "roles/container.defaultNodeServiceAccount"
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

# NOTE: workload_identity_binding is created at the environment level
# (environments/dev/main.tf) because it depends on the GKE cluster existing
# first (the Identity Pool infra-project-ms.svc.id.goog is created by GKE).

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

# Helm upgrades (e.g. kube-prometheus-stack) manage RBAC resources.
# container.developer lacks RBAC permissions, so we add a minimal custom role.
resource "google_project_iam_custom_role" "cicd_k8s_rbac" {
  project     = var.project_id
  role_id     = "cicdK8sRbac"
  title       = "CI/CD Kubernetes RBAC Manager"
  description = "Minimal RBAC permissions for Helm to manage Roles and ClusterRoles during upgrades"
  permissions = [
    "container.roles.create",
    "container.roles.delete",
    "container.roles.get",
    "container.roles.list",
    "container.roles.update",
    "container.clusterRoles.create",
    "container.clusterRoles.delete",
    "container.clusterRoles.get",
    "container.clusterRoles.list",
    "container.clusterRoles.update",
    "container.roleBindings.create",
    "container.roleBindings.delete",
    "container.roleBindings.get",
    "container.roleBindings.list",
    "container.roleBindings.update",
    "container.clusterRoleBindings.create",
    "container.clusterRoleBindings.delete",
    "container.clusterRoleBindings.get",
    "container.clusterRoleBindings.list",
    "container.clusterRoleBindings.update",
  ]
}

resource "google_project_iam_member" "cicd_k8s_rbac" {
  project = var.project_id
  role    = google_project_iam_custom_role.cicd_k8s_rbac.id
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

# ============================================================
# Workload Identity Federation - GitHub Actions (keyless auth)
# ============================================================
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  project                   = var.project_id
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC Provider"
  project                            = var.project_id

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "attribute.repository == \"${var.github_repo}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "cicd_wif_binding" {
  service_account_id = google_service_account.cicd_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}
